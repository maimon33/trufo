import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import type { Secret } from '../types'

function formatExpiry(ttlMs: number): { label: string; cls: string } {
  const diff = ttlMs - Date.now()
  if (diff <= 0) return { label: 'Expired', cls: 'expiry expired' }
  const h = Math.floor(diff / 3_600_000)
  const d = Math.floor(h / 24)
  if (d > 1) return { label: `${d}d left`, cls: 'expiry' }
  if (h > 2) return { label: `${h}h left`, cls: 'expiry soon' }
  return { label: `${h}h left`, cls: 'expiry soon' }
}

function TypeBadge({ type }: { type: string }) {
  return <span className={`badge badge-${type}`}>{type}</span>
}

function SecretCard({
  secret,
  onShare,
  onDelete,
  onSaveEdit,
  onRegenerateCodes,
}: {
  secret: Secret
  onShare: (s: Secret) => void
  onDelete: (s: Secret) => void
  onSaveEdit: (s: Secret, content: string | boolean) => Promise<void>
  onRegenerateCodes: (s: Secret) => Promise<string[]>
}) {
  const { auth } = useAuth()
  const expiry = formatExpiry(secret.ttl)

  const [editing, setEditing] = useState(false)
  const [editContent, setEditContent] = useState<string | boolean>('')
  const [loadingEdit, setLoadingEdit] = useState(false)
  const [editSaving, setEditSaving] = useState(false)

  const [showTotp, setShowTotp] = useState(false)
  const [totpCopied, setTotpCopied] = useState(false)
  const [recoveryCodes, setRecoveryCodes] = useState<string[] | null>(null)
  const [regeneratingCodes, setRegeneratingCodes] = useState(false)

  const handleEditClick = async () => {
    if (editing) { setEditing(false); return }
    if (!auth) return
    setLoadingEdit(true)
    try {
      const res = await api.getObjectContent(auth.email, auth.session, secret.s3_key)
      setEditContent(res.content)
      setEditing(true)
    } catch {
      alert('Failed to load content for editing')
    } finally {
      setLoadingEdit(false)
    }
  }

  const handleSave = async () => {
    setEditSaving(true)
    try {
      await onSaveEdit(secret, editContent)
      setEditing(false)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Save failed')
    } finally {
      setEditSaving(false)
    }
  }

  const handleCopyTotp = async () => {
    if (!secret.totp_secret) return
    await navigator.clipboard.writeText(secret.totp_secret)
    setTotpCopied(true)
    setTimeout(() => setTotpCopied(false), 2000)
  }

  const handleRegenerateCodes = async () => {
    if (!confirm('Regenerate backup codes? Your existing codes will stop working immediately.')) return
    setRegeneratingCodes(true)
    try {
      setRecoveryCodes(await onRegenerateCodes(secret))
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Could not regenerate backup codes')
    } finally {
      setRegeneratingCodes(false)
    }
  }

  return (
    <div className="card">
      <div className="secret-item">
        <div className="secret-meta">
          <div className="secret-name">{secret.name || secret.token.slice(0, 8) + '…'}</div>
          <div className="secret-preview">{secret.preview || '—'}</div>
          <div className="secret-footer">
            <TypeBadge type={secret.type} />
            {secret.one_time && <span className="badge badge-1time">1×</span>}
            {secret.security === 'totp' && (
              <button
                className="badge badge-totp"
                style={{ border: 'none', cursor: 'pointer' }}
                onClick={() => setShowTotp(v => !v)}
                title="Show TOTP secret"
              >
                🔑 TOTP
              </button>
            )}
            <span className={expiry.cls}>{expiry.label}</span>
            {secret.access_count > 0 && (
              <span className="expiry">{secret.access_count}×</span>
            )}
          </div>
        </div>
        <div className="secret-actions">
          <button className="btn btn-secondary btn-sm" onClick={() => onShare(secret)}>
            Share
          </button>
          <button className="btn btn-secondary btn-sm" onClick={handleEditClick} disabled={loadingEdit}>
            {loadingEdit ? '…' : 'Edit'}
          </button>
          <button className="btn btn-danger btn-sm" onClick={() => onDelete(secret)}>
            Del
          </button>
        </div>
      </div>

      {editing && (
        <button className="btn btn-secondary btn-sm" style={{ marginTop: '0.6rem', width: '100%' }} onClick={() => setEditing(false)}>
          ✕ Cancel edit
        </button>
      )}

      {/* TOTP secret reveal */}
      {showTotp && secret.totp_secret && (
        <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border)' }}>
          <div className="form-label" style={{ color: '#ea580c', marginBottom: '0.35rem' }}>TOTP Seed — add to authenticator</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span className="mono" style={{ flex: 1, fontSize: '0.8rem', wordBreak: 'break-all', color: 'var(--text)' }}>
              {secret.totp_secret}
            </span>
            <button className="btn btn-secondary btn-sm" onClick={handleCopyTotp}>
              {totpCopied ? '✓' : 'Copy'}
            </button>
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
            Scan or paste into Google Authenticator, Authy, etc.
          </div>
          <button className="btn btn-secondary btn-sm" style={{ marginTop: '0.65rem' }} onClick={handleRegenerateCodes} disabled={regeneratingCodes}>
            {regeneratingCodes ? 'Regenerating…' : 'Regenerate backup codes'}
          </button>
          {recoveryCodes && (
            <div className="alert alert-info" style={{ marginTop: '0.65rem', marginBottom: 0 }}>
              <strong>Save these new codes now.</strong><br />{recoveryCodes.join('\n')}
            </div>
          )}
        </div>
      )}

      {/* Inline edit form */}
      {editing && (
        <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border)' }}>
          <div className="form-label" style={{ marginBottom: '0.5rem' }}>Edit content</div>
          {secret.type === 'string' ? (
            <textarea
              className="input"
              rows={4}
              value={editContent as string}
              onChange={e => setEditContent(e.target.value)}
              autoFocus
            />
          ) : (
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <button
                type="button"
                className={`ttl-btn${editContent === true ? ' selected' : ''}`}
                style={{ flex: 1 }}
                onClick={() => setEditContent(true)}
              >
                True
              </button>
              <button
                type="button"
                className={`ttl-btn${editContent === false ? ' selected' : ''}`}
                style={{ flex: 1 }}
                onClick={() => setEditContent(false)}
              >
                False
              </button>
            </div>
          )}
          <button
            className="btn btn-primary btn-sm"
            style={{ marginTop: '0.5rem', width: '100%' }}
            onClick={handleSave}
            disabled={editSaving || (secret.type === 'string' && !(editContent as string).trim())}
          >
            {editSaving ? 'Saving…' : 'Save changes'}
          </button>
        </div>
      )}
    </div>
  )
}

export default function Home() {
  const { auth, signOut } = useAuth()
  const navigate = useNavigate()
  const [secrets, setSecrets] = useState<Secret[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deleting, setDeleting] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!auth) return
    setLoading(true)
    setError('')
    try {
      const res = await api.listSecrets(auth.email, auth.session)
      setSecrets(res.secrets)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load secrets')
    } finally {
      setLoading(false)
    }
  }, [auth])

  useEffect(() => { load() }, [load])

  const handleShare = async (secret: Secret) => {
    const url = secret.access_url
    if (navigator.share) {
      try {
        await navigator.share({ title: 'Trufo secret', url })
      } catch {
        // dismissed
      }
    } else {
      await navigator.clipboard.writeText(url)
      alert('Link copied to clipboard')
    }
  }

  const handleDelete = async (secret: Secret) => {
    if (!auth) return
    if (!confirm('Delete this secret?')) return
    setDeleting(secret.token)
    try {
      await api.deleteObject(auth.email, auth.session, secret.token, secret.s3_key)
      setSecrets(prev => prev.filter(s => s.token !== secret.token))
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Delete failed')
    } finally {
      setDeleting(null)
    }
  }

  const handleSaveEdit = async (secret: Secret, content: string | boolean) => {
    if (!auth) throw new Error('Not authenticated')
    await api.updateObject(auth.email, auth.session, secret.s3_key, content)
    setSecrets(prev => prev.map(s =>
      s.token === secret.token
        ? { ...s, preview: String(content).slice(0, 100) }
        : s
    ))
  }

  const handleRegenerateCodes = async (secret: Secret) => {
    if (!auth) throw new Error('Not authenticated')
    return (await api.regenerateRecoveryCodes(auth.email, auth.session, secret.s3_key)).recoveryCodes
  }

  const headerAction = (
    <button
      className="btn btn-ghost btn-sm"
      onClick={() => { signOut(); navigate('/signin', { replace: true }) }}
    >
      Sign out
    </button>
  )

  return (
    <Layout title="My Secrets" action={headerAction}>
      {loading && (
        <div className="loading">
          <div className="spinner" />
          Loading…
        </div>
      )}

      {error && (
        <div className="alert alert-error">
          {error}
          <button
            style={{ marginLeft: '0.5rem', textDecoration: 'underline', background: 'none', border: 'none', cursor: 'pointer', color: 'inherit' }}
            onClick={load}
          >
            Retry
          </button>
        </div>
      )}

      {!loading && !error && secrets.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">🔐</div>
          <p>No secrets yet</p>
          <button className="btn btn-primary" style={{ maxWidth: 200, margin: '0 auto' }} onClick={() => navigate('/create')}>
            Create your first
          </button>
        </div>
      )}

      {secrets.map(secret => (
        <SecretCard
          key={secret.token}
          secret={secret}
          onShare={handleShare}
          onDelete={deleting === secret.token ? () => {} : handleDelete}
          onSaveEdit={handleSaveEdit}
          onRegenerateCodes={handleRegenerateCodes}
        />
      ))}

      {secrets.length > 0 && (
        <p style={{ textAlign: 'center', fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
          {secrets.length} secret{secrets.length !== 1 ? 's' : ''} · {auth?.email}
        </p>
      )}
    </Layout>
  )
}
