# Trufo — Claude Code Guide

## What is Trufo?

Trufo is a **serverless secret-sharing PWA** built on AWS. Owners create time-limited secrets (strings, booleans, toggles) and share access links. Viewers open the link to retrieve the content — no account needed on the viewer side.

**Live URL:** `https://trufo.maimons.dev`  
**PWA path:** `/app/`  
**Stack name:** `trufo-api` (us-east-1)

---

## Repository Layout

```
trufo/
├── src/                         # Lambda source (Python 3.9)
│   ├── lambda_function.py       # Main handler — all routes + auth + storage
│   ├── reports.py               # DailyReportFunction handler
│   ├── templates.py             # Legacy SSR HTML pages (kept for /create, /access, /manage)
│   ├── requirements.txt         # boto3 only (pre-installed in Lambda runtime)
│   └── pwa_static/              # Compiled PWA bundle — built by CI, NOT committed
├── pwa/                         # React 18 + TypeScript + Vite PWA
│   ├── src/
│   │   ├── App.tsx              # Router + MagicLinkHandler
│   │   ├── main.tsx             # React root + service worker registration
│   │   ├── index.css            # All styles (mobile-first, CSS vars, no UI lib)
│   │   ├── types/index.ts       # Shared TS types (Secret, CreateResult, AccessResult)
│   │   ├── context/AuthContext.tsx  # Global auth state (email + secret)
│   │   ├── lib/api.ts           # Typed fetch wrappers for every API endpoint
│   │   ├── lib/auth.ts          # localStorage get/set/clear for auth
│   │   ├── pages/
│   │   │   ├── SignIn.tsx       # Email → OTP or magic-link auth
│   │   │   ├── Home.tsx         # Authenticated secrets list + manage actions
│   │   │   ├── Create.tsx       # Create new secret form
│   │   │   └── Access.tsx       # Public secret viewer (no auth required)
│   │   └── components/
│   │       ├── Layout.tsx       # App shell (header, scrollable body, bottom nav)
│   │       └── BottomNav.tsx    # 2-tab nav: Secrets | Create
│   ├── public/                  # manifest.json, icons, sw.js (service worker)
│   ├── vite.config.ts           # base: '/app/', output: dist/
│   └── package.json             # React 18, React Router v6, Vite, TypeScript
├── sam/
│   └── template.yaml            # SAM/CloudFormation — full infrastructure definition
├── .github/workflows/
│   └── deploy.yml               # CI/CD: build PWA → SAM build → SAM deploy
└── CLAUDE.md                    # This file
```

---

## AWS Architecture

```
                    ┌─────────────────────────┐
  Browser / PWA ──► │  API Gateway (REST)       │
                    │  ANY / + /{proxy+}        │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  TrufoLambdaFunction     │  Python 3.9 · 512 MB · 30s
                    │  lambda_function.py      │
                    └──┬────────┬────────┬───┘
                       │        │        │
              ┌────────▼──┐  ┌──▼───┐  ┌▼──────────┐
              │ S3 Bucket  │  │ SES  │  │ CloudWatch │
              │ (objects)  │  │(email│  │ (metrics)  │
              └────────────┘  └──────┘  └────────────┘

  EventBridge ──► TrufoLambdaFunction  (hourly cleanup: /api/cleanup)
  EventBridge ──► DailyReportFunction  (8 AM UTC: reports.py)
              └► SNS → AdminEmail      (CloudWatch alarms)
```

**Key resources:**
| Resource | Details |
|---|---|
| S3 bucket | `trufo-storage-bucket` · AES-256 · versioned · private |
| API Gateway | REST (v1) · REGIONAL · CORS `*` · binary media types `*/*` |
| Lambda (main) | `trufo-api-TrufoLambdaFunction-…` · 512 MB · 30 s |
| Lambda (report) | `trufo-api-daily-report` · 256 MB · 60 s |
| SES | Domain identity `maimons.dev` · DKIM + SPF + DMARC |
| SNS | Admin alert topic → `ADMIN_EMAIL` |
| Usage plan | Rate 5000 rps, burst 10 000, quota 1M/day (kill switch sets to 0) |
| CloudWatch alarms | HighDailyUsage (1000 creates), HighMonthlyUsage (10k), HighErrorRate (10 errors/5 min) |

---

## S3 Data Layout

```
users/{md5(email)}/{type}/{name}.json   ← object payload (auth-gated write, token-gated read)
tokens/{token}.json                     ← { "s3_key": "users/…" }  (fast token lookup)
```

**Object payload schema:**
```json
{
  "id":           "obj_1712345678_a1b2c3d4",
  "token":        "abc123def456…",        // 32-char hex, random
  "name":         "api-key-staging",
  "type":         "string | boolean | toggle",
  "securityType": "none | basic | totp",
  "content":      "<base64(json.dumps(value))>",
  "ttl":          1712345678000,           // ms epoch, expiry
  "ownerEmail":   "user@example.com",
  "hitCount":     5,
  "createdAt":    1712345670000,
  "lastHit":      1712345680000,
  "oneTimeAccess": false,
  "totpSecret":   "JBSWY3DPEHPK3PXP",    // only for securityType=totp
  "recoveryCodes": ["XXXX-XXXX", …]       // 8 codes, consumed on use
}
```

**Content encryption:** `base64(json.dumps(value))` — obfuscated, not cryptographically encrypted. The per-object HMAC secret (`generate_object_secret`) protects access.

---

## Authentication Model

### Owner authentication (two-factor stateless)
1. **Email verification** — client sends email → server generates 6-digit OTP (in-memory `email_codes` dict, 5 min TTL) → SES delivery
2. **Magic link** — server generates URL-safe token (in-memory `magic_links`, 10 min TTL) → email contains `{returnUrl}?auth={token}`
3. **User secret** — on verification, server returns `SHA256(normalized_email)`. This is the user's durable credential stored in `localStorage`.

**Protected endpoints** accept `{ email, secret }` and do constant-time HMAC comparison.

### Object access secret (per-object HMAC)
`HMAC-SHA256(ENCRYPTION_KEY, "{token}:{email}:{createdAt}")` — embedded in the share link. Cannot be forged without the server key.

### TOTP 2FA (optional per object)
- Generated on creation: 20-byte base32 secret + 8 recovery codes
- Verified on access: 30-second windows ±1
- Recovery codes are one-time-use (consumed from the stored array)

### Email normalization
All emails are lowercased, Gmail dots removed, `+` aliases rejected, disposable domains blocked.

---

## API Endpoints

All routes handled by `lambda_function.lambda_handler`. API Gateway catches all via `/{proxy+}`.

### Auth
| Method | Path | Handler | Notes |
|---|---|---|---|
| POST | `/api/validate-email` | `send_email_validation` | Send OTP; bot detection on first-time users |
| POST | `/api/verify-code` | `verify_email_code` | Verify OTP → return `userSecret` |
| POST | `/api/send-magic-link` | `send_magic_link` | Email magic link |
| POST | `/api/verify-magic-link` | `verify_magic_link` | Verify token → return `email + userSecret` |
| GET  | `/api/check-auth` | `check_user_auth` | Cookie-based auth check |

### Objects (owner, requires `email + secret`)
| Method | Path | Handler | Notes |
|---|---|---|---|
| POST | `/api/objects` | `create_object` | Create; max 30/user, max 1 MB |
| POST | `/api/list-objects` | `list_user_objects` | List non-expired objects with `accessSecret` |
| POST | `/api/list-secrets` | `list_user_secrets` | Alternate list endpoint used by PWA |
| POST | `/api/delete-object` | `delete_user_object` | Delete by s3Key + ownership check |
| POST | `/api/update-object` | `update_object` | Update content by s3Key + ownership check |
| POST | `/api/get-object-content` | `get_object_content` | Fetch full decrypted content for editing |

### Objects (viewer, public — requires token + accessSecret)
| Method | Path | Handler | Notes |
|---|---|---|---|
| GET | `/api/objects` | `get_object` | Retrieve + increment hitCount; handles TOTP |
| GET | `/api/info/{token}` | `get_object_info` | Metadata only, no secret consumed |
| POST | `/api/toggle` | `toggle_object` | Flip boolean object |
| DELETE | `/api/objects` | `delete_object` | Legacy delete by id |

### System
| Method | Path | Handler | Notes |
|---|---|---|---|
| POST | `/api/cleanup` | `cleanup_expired_objects` | Requires `cleanup_key`; triggered hourly by EventBridge |

### Static / Web
| Path | Behavior |
|---|---|
| `/app` `/app/` | Serve `pwa_static/index.html` |
| `/app/{path}` | Serve from `pwa_static/`; SPA fallback to `index.html` |
| `/` `/create` | SSR create page (templates.py) |
| `/access/{token}` | SSR access page |
| `/manage` | SSR manage page |

---

## PWA Pages & Flows

### SignIn (`/signin`)
Modes: **OTP** (default on desktop) or **Magic Link** (default on mobile).
Steps: email input → sent → code entry (OTP mode only).
On success: `signIn({ email, secret })` → navigate to `/`.

### Home (`/`) — My Secrets
- Calls `POST /api/list-secrets` on mount
- Shows `SecretCard` per secret: name, preview, type badge, security badge, expiry, hit count
- Actions per card: **Share** (native share or clipboard copy), **Edit** (inline edit form), **Del** (confirm + delete)
- TOTP secrets show a **🔑** button to reveal the stored TOTP seed (for re-adding to authenticator)

### Create (`/create`)
Two views:
1. **Form** — name, type, content, TTL, security, one-time toggle
2. **Result** — share URL, TOTP secret + recovery codes (if applicable), Share/Copy, Create Another, ← My Secrets

### Access (`/access/:token?secret=…`)
Public page (no auth). Handles TOTP gate (prompts for code if required). Increments hit counter on each view. Deletes on one-time access. Link at bottom to "Open Trufo App".

### Magic Link Handler (App.tsx)
Reads `?auth=` param → verifies with `/api/verify-magic-link` → if PWA (standalone mode): navigate in-place; if browser tab: show "Open Trufo App" screen. Cleans up URL param immediately.

---

## CI/CD Pipeline

**Trigger:** push to `main` touching `src/**`, `sam/**`, or `pwa/**`. Also `workflow_dispatch`.

**Steps:**
1. `npm --prefix pwa ci && npm --prefix pwa run build` → output to `pwa/dist/`
2. `cp -r pwa/dist/* src/pwa_static/` — bundle embedded inside Lambda package
3. `sam build` (cached by hash of `src/` + `template.yaml`)
4. `sam deploy --stack-name trufo-api --resolve-s3 --no-confirm-changeset`
   - Parameters via **GitHub Secrets** (never `vars`): `AWS_ROLE_ARN`, `FROM_EMAIL`, `ADMIN_EMAIL`, `DOMAIN_NAME`
5. Deployment summary extracted from CloudFormation outputs → GitHub Actions job summary

**OIDC auth:** `secrets.AWS_ROLE_ARN` assumed via `aws-actions/configure-aws-credentials`.

---

## Development Notes

### Adding a new API endpoint
1. Add route in `lambda_function.py` → `lambda_handler` (in the `try` block, before the `else: 404`)
2. Add handler function in `lambda_function.py`
3. Add typed method to `pwa/src/lib/api.ts`
4. No SAM template changes needed — `/{proxy+}` catches everything

### Adding a new PWA page
1. Create `pwa/src/pages/MyPage.tsx`
2. Add `<Route path="/mypath" element={<MyPage />} />` in `App.tsx`
3. Wrap with `<Layout>` for the standard shell; or render standalone for public pages

### Key conventions
- All Lambda responses go through `cors_response(status, data, content_type)`
- User ownership is verified by checking S3 key starts with `users/{md5(normalized_email)}/`
- Ownership double-checked: `obj_data['ownerEmail'] == normalized_email`
- Content stored as `base64(json.dumps(value))` via `encrypt_content` / `decrypt_content`
- Metrics tracked via `track_metrics(event_type, **kwargs)` → CloudWatch namespace `Trufo`
- Email codes and magic link tokens live in **in-memory dicts** (lost on Lambda cold start — acceptable given short TTLs)

### Security rules
- Never store plain-text content — always `encrypt_content()`
- Always use `hmac.compare_digest` for secret comparisons (timing attack prevention)
- Always normalize email with `normalize_email()` before any comparison or storage
- Admin endpoint (`/api/cleanup`) gated by `cleanup_key = ENCRYPTION_KEY + "cleanup"`

### Cost profile (us-east-1, light usage)
Lambda + API Gateway + S3 + SES easily stays inside free tier at low scale. Daily report emails estimated costs. Kill switch (API Gateway throttle → 0) available as emergency lockdown.

---

## GitHub Secrets Required

| Secret | Purpose |
|---|---|
| `AWS_ROLE_ARN` | OIDC role for SAM deploy |
| `FROM_EMAIL` | SES verified sender |
| `ADMIN_EMAIL` | Daily reports + CloudWatch alarm emails |
| `DOMAIN_NAME` | Custom domain (optional) |
