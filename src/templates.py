"""
HTML templates for Trufo web interface
"""

def serve_create_page() -> str:
    """Return HTML for object creation page"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trufo - Create Secret Object</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            margin: 0;
            padding: 10px;
        }
        .container {
            background: white;
            border-radius: 8px;
            padding: 1rem;
            max-width: 600px;
            width: 100%;
            margin: 0.5rem auto;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }
        .header-section {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
        }
        .header-btn {
            background: #667eea;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 0.5rem 1rem;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.3s ease;
            width: auto;
        }
        .header-btn:hover {
            background: #5a6fd8;
            transform: translateY(-1px);
        }
        .header-section h1 {
            margin: 0;
            flex: 1;
            text-align: center;
            color: #333;
            font-size: 1.5rem;
        }
        h1 { color: #333; margin-bottom: 0.75rem; text-align: center; font-size: 1.5rem; }
        .form-group { margin-bottom: 0.75rem; }
        label { display: block; margin-bottom: 0.3rem; color: #555; font-weight: 500; font-size: 0.9rem; }
        input, textarea, select {
            width: 100%;
            padding: 0.5rem;
            border: 1px solid #e1e5e9;
            border-radius: 4px;
            font-size: 0.9rem;
            transition: border-color 0.2s;
        }
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        textarea { min-height: 60px; resize: vertical; }
        .checkbox-group {
            display: flex;
            align-items: center;
            margin-top: 0.5rem;
        }
        .checkbox-group input[type="checkbox"] {
            width: auto;
            margin-right: 0.5rem;
        }
        button {
            width: 100%;
            padding: 0.75rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, opacity 0.2s;
        }
        button:hover { transform: translateY(-2px); }
        button:disabled { opacity: 0.7; cursor: not-allowed; transform: none; }
        .result {
            margin-top: 1.5rem;
            padding: 1rem;
            border-radius: 6px;
            display: none;
        }
        .result.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .result.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .intro-section {
            background: #f8f9fa;
            border-radius: 4px;
            padding: 0.75rem;
            margin-bottom: 1rem;
            border-left: 3px solid #667eea;
        }
        .intro-section ul {
            margin: 1rem 0;
            padding-left: 1.5rem;
        }
        .intro-section li {
            margin-bottom: 0.5rem;
        }
        .auth-section {
            border: 2px dashed #e1e5e9;
            border-radius: 6px;
            padding: 1rem;
            text-align: center;
            margin-bottom: 1rem;
        }
        .auth-methods {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin: 1rem 0;
        }
        .auth-button {
            background: #4285f4;
            margin-bottom: 0.5rem;
            padding: 1.2rem 1rem;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 600;
            transition: all 0.3s ease;
            border: 2px solid transparent;
            text-align: center;
            line-height: 1.4;
        }
        .auth-button small {
            display: block;
            font-size: 0.75rem;
            opacity: 0.8;
            font-weight: 400;
            margin-top: 0.25rem;
        }
        .auth-button.primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .auth-button.primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        .auth-button.secondary {
            background: #f8f9fa;
            color: #495057;
            border: 2px solid #e9ecef;
        }
        .auth-button.secondary:hover {
            background: #e9ecef;
            border-color: #667eea;
            transform: translateY(-1px);
        }
        .email-form { display: none; }
        .access-info {
            background: #f8f9fa;
            border-radius: 6px;
            padding: 1rem;
            margin-top: 1rem;
            font-family: monospace;
            font-size: 0.9rem;
            word-break: break-all;
            white-space: normal;
        }
        .ttl-horizontal {
            display: flex;
            gap: 1rem;
            align-items: flex-start;
            flex-wrap: wrap;
        }
        .ttl-presets {
            display: flex;
            gap: 0.25rem;
            flex-wrap: wrap;
            flex: 1;
        }
        .ttl-custom {
            flex: 0 0 auto;
            min-width: 120px;
        }
        .preset-btn {
            background: #f8f9fa;
            border: 1px solid #e1e5e9;
            border-radius: 3px;
            padding: 0.25rem 0.5rem;
            cursor: pointer;
            font-size: 0.8rem;
            font-weight: 500;
            transition: all 0.2s;
            color: #555;
            min-width: 40px;
        }
        .preset-btn:hover {
            background: #e9ecef;
            border-color: #667eea;
        }
        .preset-btn.active {
            background: #667eea;
            border-color: #667eea;
            color: white;
        }
        .ttl-custom input {
            margin-bottom: 0.25rem;
        }
        .ttl-custom small {
            color: #666;
            font-size: 0.8rem;
        }
        .ttl-preview {
            background: #d4edda;
            color: #155724;
            padding: 0.5rem;
            border-radius: 4px;
            font-size: 0.9rem;
            margin-top: 0.5rem;
            display: none;
        }
        .ttl-preview.error {
            background: #f8d7da;
            color: #721c24;
        }
        .security-info {
            background: #f8f9fa;
            border-radius: 6px;
            padding: 1rem;
            margin-bottom: 1rem;
            border-left: 4px solid #adb5bd;
        }
        .security-info.notice {
            border-left-color: #17a2b8;
        }
        .security-info.basic {
            border-left-color: #fd7e14;
        }
        .security-info.totp {
            border-left-color: #dc3545;
        }
        .security-info h4 {
            margin-bottom: 0.5rem;
            color: #333;
        }
        .security-info #securityDetails {
            font-size: 0.9rem;
            color: #666;
            line-height: 1.4;
        }
        .sec-level {
            display: flex;
            gap: 3px;
            margin-top: 6px;
        }
        .sec-level .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #dee2e6;
            border: 1px solid #ced4da;
        }
        .sec-level .dot.l1 { background: #17a2b8; border-color: #138496; }
        .sec-level .dot.l2 { background: #fd7e14; border-color: #e8680b; }
        .sec-level .dot.l3 { background: #dc3545; border-color: #c82333; }
        .security-options {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin-top: 0.5rem;
        }
        .security-option {
            flex: 1;
            min-width: 120px;
            border: 1px solid #e1e5e9;
            border-radius: 4px;
            padding: 0.5rem;
            cursor: pointer;
            transition: all 0.2s;
            position: relative;
        }
        .security-option:hover {
            border-color: #667eea;
            background: #f8f9fa;
        }
        .security-option input[type="radio"] {
            position: absolute;
            opacity: 0;
            width: 0;
            height: 0;
        }
        .security-option input[type="radio"]:checked + label {
            color: #667eea;
        }
        .security-option input[type="radio"]:checked ~ .security-option,
        .security-option:has(input[type="radio"]:checked) {
            border-color: #667eea;
            background: #f0f4ff;
        }
        .security-option label {
            cursor: pointer;
            display: block;
            margin: 0;
        }
        .security-option strong {
            display: block;
            margin-bottom: 0.2rem;
            font-size: 0.9rem;
        }
        .security-option small {
            color: #666;
            font-size: 0.75rem;
        }
        .content-tabs {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 0.75rem;
        }
        .content-tab {
            background: #f8f9fa;
            border: 1px solid #e1e5e9;
            border-radius: 4px;
            padding: 0.4rem 0.8rem;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.2s;
            color: #666;
            width: auto;
        }
        .content-tab:hover {
            background: #e9ecef;
            border-color: #667eea;
        }
        .content-tab.active {
            background: #667eea;
            border-color: #667eea;
            color: white;
        }

        .copy-box {
            background: #f8f9fa;
            border: 1px solid #e1e5e9;
            border-radius: 4px;
            padding: 0.75rem;
            margin: 0.5rem 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .copy-box code {
            flex: 1;
            background: none;
            border: none;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.85rem;
            color: #333;
            overflow-x: auto;
            white-space: nowrap;
        }
        .copy-btn {
            background: #667eea;
            color: white;
            border: none;
            border-radius: 3px;
            padding: 0.4rem 0.8rem;
            font-size: 0.8rem;
            cursor: pointer;
            white-space: nowrap;
        }
        .copy-btn:hover {
            background: #5a6fd8;
        }
        .copy-btn:active {
            background: #4f63d2;
        }

        /* Modal styles */
        .modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        .modal-content {
            background: white;
            border-radius: 8px;
            max-width: 90%;
            max-height: 90%;
            overflow: auto;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }
        .modal-header {
            padding: 1rem 1.5rem;
            border-bottom: 1px solid #e1e5e9;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .modal-header h3 {
            margin: 0;
            color: #333;
        }
        .close-btn {
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: #666;
            padding: 0;
            width: 30px;
            height: 30px;
        }
        .close-btn:hover {
            color: #000;
        }
        .modal-body {
            padding: 1.5rem;
            min-width: 600px;
        }
        .secrets-grid {
            display: grid;
            gap: 1rem;
            grid-template-columns: 1fr;
        }
        .secret-card {
            border: 1px solid #e1e5e9;
            border-radius: 8px;
            padding: 1.5rem;
            background: #f8f9fa;
            margin-bottom: 1rem;
        }
        .secret-card.expired {
            opacity: 0.7;
            border-color: #dc3545;
            background: #f8d7da;
        }
        .secret-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        .secret-type {
            font-weight: bold;
            color: #667eea;
            font-size: 1rem;
        }
        .secret-status {
            font-weight: 600;
            font-size: 0.85rem;
        }
        .secret-credentials {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 1rem;
            margin: 1rem 0;
        }
        .credential-row {
            margin-bottom: 0.75rem;
        }
        .credential-row:last-child {
            margin-bottom: 0;
        }
        .credential-row strong {
            display: block;
            margin-bottom: 0.25rem;
        }
        .credential-box {
            position: relative;
        }
        .credential-value {
            display: block;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.85rem;
            background: #f8f9fa;
            padding: 1.8rem 0.5rem 0.5rem 0.5rem;
            border-radius: 3px;
            border: 1px solid #e9ecef;
            word-break: break-all;
        }
        .copy-btn-small {
            position: absolute;
            top: 0.25rem;
            right: 0.25rem;
            background: transparent;
            color: #666;
            border: none;
            border-radius: 3px;
            padding: 0.25rem;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.2s;
            opacity: 0.5;
        }
        .copy-btn-small:hover {
            opacity: 1;
            background: rgba(0,0,0,0.05);
        }
        .access-options {
            margin-top: 1rem;
        }
        .access-option {
            margin-bottom: 1rem;
        }
        .access-option:last-child {
            margin-bottom: 0;
        }
        .access-link {
            position: relative;
            margin-top: 0.5rem;
        }
        .access-link code {
            display: block;
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            padding: 2rem 0.5rem 0.5rem 0.5rem;
            border-radius: 4px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.8rem;
            word-break: break-word;
            line-height: 1.3;
            position: relative;
            min-height: 1.3em;
        }
        .copy-icon {
            position: absolute;
            top: 0.5rem;
            right: 0.5rem;
            background: transparent;
            border: none;
            cursor: pointer;
            padding: 0.25rem;
            border-radius: 3px;
            opacity: 0.5;
            transition: all 0.2s;
            font-size: 0.9rem;
            color: #666;
        }
        .copy-icon:hover {
            opacity: 1;
            background: rgba(0,0,0,0.05);
        }
        .secret-preview {
            font-family: monospace;
            background: white;
            padding: 0.5rem;
            border-radius: 3px;
            margin-bottom: 0.5rem;
            word-break: break-all;
            max-height: 60px;
            overflow: hidden;
        }
        .secret-meta {
            font-size: 0.85rem;
            color: #666;
            margin-bottom: 0.5rem;
        }
        .access-url {
            margin-top: 0.5rem;
            padding-top: 0.5rem;
            border-top: 1px solid #e1e5e9;
        }
        .access-url code {
            font-size: 0.8rem;
            background: #f8f9fa;
            padding: 2px 4px;
            border-radius: 3px;
            word-break: break-all;
        }
        .secret-actions {
            text-align: right;
        }
        .no-secrets, .error {
            text-align: center;
            padding: 2rem;
            color: #666;
        }
        .error {
            color: #dc3545;
        }

        /* Mobile responsiveness */
        @media (max-width: 768px) {
            body { padding: 10px; }
            .container {
                padding: 1rem;
                margin: 1rem auto;
                max-width: none;
            }
            .security-options {
                flex-direction: column;
                gap: 0.75rem;
            }
            .security-option {
                min-width: auto;
                text-align: center;
            }
            .ttl-horizontal {
                flex-direction: column;
                gap: 0.5rem;
                align-items: stretch;
            }
            .ttl-custom {
                min-width: auto;
            }
            .ttl-presets {
                justify-content: center;
            }
            .preset-btn {
                flex: 1;
                min-width: 50px;
            }
            .content-tabs {
                justify-content: center;
            }
            .intro-section {
                padding: 1rem;
            }
            h1 { font-size: 1.5rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-section" id="headerSection">
            <button type="button" class="header-btn" id="returnBtn" onclick="showCreateView()" style="display: none;">← Return</button>
            <h1>🔒 Trufo - Create Secret</h1>
            <button type="button" class="header-btn" id="listSecretsBtn" onclick="showListSecrets()" style="display: none;">📋 My Secrets</button>
        </div>

        <div class="intro-section" id="welcomeMessage">
            <p><strong>Welcome to Trufo!</strong> Share secrets securely with automatic expiration and flexible security options.</p>
            <p style="font-size: 0.8rem; color: #666; margin-top: 0.5rem;">
                📊 <em>Anonymous usage statistics are collected (no content or emails stored)</em>
            </p>
        </div>

        <div class="auth-section" id="authSection">
            <p>🔐 <strong>Choose Authentication Method:</strong></p>
            <div class="auth-methods">
                <button type="button" class="auth-button primary" onclick="showMagicLinkAuth()">
                    ✨ Magic Link<br>
                    <small>One-click email login</small>
                </button>
                <button type="button" class="auth-button secondary" onclick="showMFAAuth()">
                    🔐 MFA Code<br>
                    <small>6-digit verification</small>
                </button>
            </div>
            <div class="email-form" id="emailForm">
                <div class="form-group">
                    <label for="email">Email Address</label>
                    <input type="email" id="email" placeholder="your@email.com" required>
                </div>

                <div style="background: #e3f2fd; border: 1px solid #2196f3; border-radius: 6px; padding: 0.75rem; margin: 1rem 0; font-size: 0.85rem; color: #1565c0;">
                    <strong>🔒 MFA & Cookie Notice:</strong> When using TOTP 2FA, this site uses secure cookies to remember your authentication for several days. Stay on the same browser/device to avoid re-authentication. Clear cookies to force re-login.
                </div>

                <button type="button" onclick="sendVerificationCode()">Send Verification Code</button>

                <div class="form-group" id="codeGroup" style="display: none; margin-top: 1rem;">
                    <label for="verificationCode">Verification Code</label>
                    <input type="text" id="verificationCode" placeholder="123456" maxlength="6">
                    <button type="button" onclick="verifyCode()">Verify Code</button>
                </div>
            </div>
        </div>

        <form id="createForm" style="display: none;">
            <div class="form-group">
                <label for="name">Object Name</label>
                <input type="text" id="name" placeholder="my-secret" required>
            </div>

            <div class="form-group">
                <label for="content">Content</label>
                <div class="content-options">
                    <div class="content-tabs">
                        <button type="button" class="content-tab active" onclick="showTextContent()">Text</button>
                        <button type="button" class="content-tab" onclick="showFileContent()">File</button>
                    </div>
                    <div id="textContent" class="content-input">
                        <div class="form-group" style="margin-bottom: 0.75rem;">
                            <label for="type">Text Type</label>
                            <select id="type" required>
                                <option value="string">Text/String</option>
                                <option value="boolean">True/False</option>
                                <option value="toggle">Auto-Toggle</option>
                            </select>
                        </div>
                        <textarea id="content" placeholder="Your secret content here..." required></textarea>
                        <small id="contentSizeHint">Max: 1MB</small>
                        <div id="booleanSwitch" style="display:none; margin-top: 0.75rem;">
                            <label style="display: flex; align-items: center; gap: 0.75rem; cursor: pointer; font-size: 1rem;">
                                <span id="boolSwitchLabel" style="min-width: 40px; color: #555;">true</span>
                                <div class="toggle-switch" onclick="toggleBoolSwitch()" id="boolToggleTrack" style="position:relative;width:52px;height:28px;background:#667eea;border-radius:14px;transition:background 0.2s;cursor:pointer;flex-shrink:0;">
                                    <div id="boolToggleThumb" style="position:absolute;top:3px;left:3px;width:22px;height:22px;background:white;border-radius:50%;transition:transform 0.2s;"></div>
                                </div>
                            </label>
                            <small style="color:#666; margin-top:0.4rem; display:block;">Click to toggle the initial value</small>
                        </div>
                    </div>
                    <div id="fileContent" class="content-input" style="display: none;">
                        <input type="file" id="fileInput" accept="*/*">
                        <small>Max: 1MB - File will be base64 encoded</small>
                        <div id="filePreview" style="margin-top: 0.5rem; font-size: 0.8rem; color: #666;"></div>
                    </div>
                </div>
            </div>

            <div class="form-group">
                <div class="checkbox-group">
                    <input type="checkbox" id="oneTimeAccess">
                    <label for="oneTimeAccess">🔥 One-time access (delete immediately after reading)</label>
                </div>
                <small style="color: #666; margin-top: 0.5rem; display: block;">
                    💡 <strong>Note:</strong> If enabled, the secret will be deleted immediately after the first access, regardless of the TTL setting below.
                    However, if the TTL expires before anyone accesses it, the secret will still be automatically deleted.
                </small>
            </div>

            <div class="form-group">
                <label for="ttl">Expires After</label>
                <div class="ttl-horizontal">
                    <div class="ttl-presets">
                        <button type="button" class="preset-btn" data-value="1h">1h</button>
                        <button type="button" class="preset-btn" data-value="6h">6h</button>
                        <button type="button" class="preset-btn" data-value="24h">24h</button>
                        <button type="button" class="preset-btn" data-value="7d">7d</button>
                        <button type="button" class="preset-btn" data-value="30d">30d</button>
                    </div>
                    <div class="ttl-custom">
                        <input type="text" id="ttl" placeholder="24h" value="24h" pattern="^\\d+[hHdDwWmMyY]$" required>
                        <small>1h, 7d, 30d, 1y (max: 365d)</small>
                    </div>
                </div>
                <div id="ttlPreview" class="ttl-preview"></div>
            </div>

            <div class="form-group">
                <label>🔒 Security Level</label>
                <div class="security-options">
                    <div class="security-option">
                        <input type="radio" id="securityNone" name="security" value="none" checked>
                        <label for="securityNone">
                            <strong>None</strong><br>
                            <small>Token access only, no verification</small>
                            <div class="sec-level"><span class="dot"></span><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>
                        </label>
                    </div>
                    <div class="security-option">
                        <input type="radio" id="securityNotice" name="security" value="notice">
                        <label for="securityNotice">
                            <strong>Notification</strong><br>
                            <small>Creator is alerted on every access</small>
                            <div class="sec-level"><span class="dot l1"></span><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>
                        </label>
                    </div>
                    <div class="security-option">
                        <input type="radio" id="securityBasic" name="security" value="basic">
                        <label for="securityBasic">
                            <strong>Basic</strong><br>
                            <small>Viewer must verify email to access</small>
                            <div class="sec-level"><span class="dot l2"></span><span class="dot l2"></span><span class="dot"></span><span class="dot"></span></div>
                        </label>
                    </div>
                    <div class="security-option">
                        <input type="radio" id="securityTotp" name="security" value="totp">
                        <label for="securityTotp">
                            <strong>Maximum (TOTP)</strong><br>
                            <small>Authenticator app + backup codes</small>
                            <div class="sec-level"><span class="dot l3"></span><span class="dot l3"></span><span class="dot l3"></span><span class="dot l3"></span></div>
                        </label>
                    </div>
                </div>
            </div>

            <button type="submit">Create Secret Object</button>
        </form>

        <div id="result" class="result"></div>
    </div>

    <script>
        let userEmail = '';
        let userSecret = '';

        // Behavioral analysis data
        let behavioralData = {
            mouse_moves: [],
            keystrokes: [],
            click_events: [],
            focus_events: [],
            page_load_time: Date.now(),
            form_fill_start: null
        };

        // Behavioral tracking setup
        document.addEventListener('DOMContentLoaded', function() {
            // Check for magic link authentication
            checkMagicLinkAuth();
            // Mouse movement tracking
            let mouseTrackingActive = false;
            document.addEventListener('mousemove', function(e) {
                if (mouseTrackingActive && behavioralData.mouse_moves.length < 50) {
                    behavioralData.mouse_moves.push({
                        x: e.clientX,
                        y: e.clientY,
                        timestamp: Date.now()
                    });
                }
            });

            // Click tracking
            document.addEventListener('click', function(e) {
                const rect = e.target.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                const clickX = e.clientX;
                const clickY = e.clientY;

                // Check if click was exactly on center (suspicious)
                const isPerfectCenter = Math.abs(clickX - centerX) < 2 && Math.abs(clickY - centerY) < 2;

                behavioralData.click_events.push({
                    x: clickX,
                    y: clickY,
                    target: {
                        tag: e.target.tagName,
                        id: e.target.id,
                        className: e.target.className,
                        perfect_center: isPerfectCenter
                    },
                    timestamp: Date.now()
                });
            });

            // Focus tracking
            document.addEventListener('focusin', function(e) {
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                    behavioralData.focus_events.push({
                        field: e.target.id || e.target.name,
                        timestamp: Date.now()
                    });
                }
            });

            // Keystroke tracking
            document.addEventListener('keydown', function(e) {
                if (e.target.tagName === 'INPUT' && e.target.type === 'email') {
                    behavioralData.keystrokes.push({
                        key: e.key.length === 1 ? 'char' : e.key,
                        timestamp: Date.now()
                    });
                }
            });

            // Start mouse tracking when user first interacts
            document.addEventListener('mousedown', function() {
                mouseTrackingActive = true;
            }, { once: true });

            // TTL preset buttons and parsing
            setupTTLHandlers();

            // Setup form handlers
            setupFormHandlers();

            // Initial auth section update
            updateAuthSection();

            // Add email input listener for auto-auth check
            const emailInput = document.getElementById('email');
            if (emailInput) {
                emailInput.addEventListener('blur', async function() {
                    const securityValue = document.querySelector('input[name="security"]:checked').value;
                    if (securityValue !== 'none') {
                        await checkExistingAuth();
                    }
                });
            }
        });

        function setupTTLHandlers() {
            const ttlInput = document.getElementById('ttl');
            const previewDiv = document.getElementById('ttlPreview');
            const presetBtns = document.querySelectorAll('.preset-btn');

            // Preset button handlers
            presetBtns.forEach(btn => {
                btn.addEventListener('click', function() {
                    presetBtns.forEach(b => b.classList.remove('active'));
                    this.classList.add('active');
                    ttlInput.value = this.dataset.value;
                    updateTTLPreview();
                });
            });

            // Input change handler
            ttlInput.addEventListener('input', function() {
                presetBtns.forEach(b => b.classList.remove('active'));
                updateTTLPreview();
            });

            // Initial preview
            updateTTLPreview();
        }

        function parseTTLToHours(ttlString) {
            const match = ttlString.toLowerCase().match(/^(\\d+(?:\\.\\d+)?)([hdwmy])$/);
            if (!match) return null;

            const [, value, unit] = match;
            const num = parseFloat(value);

            switch (unit) {
                case 'h': return num;
                case 'd': return num * 24;
                case 'w': return num * 24 * 7;
                case 'm': return num * 24 * 30; // Approximate month
                case 'y': return num * 24 * 365; // Year
                default: return null;
            }
        }

        function updateTTLPreview() {
            const ttlInput = document.getElementById('ttl');
            const previewDiv = document.getElementById('ttlPreview');
            const ttlString = ttlInput.value.trim();

            if (!ttlString) {
                previewDiv.style.display = 'none';
                return;
            }

            const hours = parseTTLToHours(ttlString);

            if (hours === null || hours <= 0) {
                previewDiv.innerHTML = 'Invalid format. Use: 1h, 24h, 7d, 30d, 1y';
                previewDiv.className = 'ttl-preview error';
                previewDiv.style.display = 'block';
                return;
            }

            if (hours > 24 * 365) { // 365 days max
                previewDiv.innerHTML = 'Maximum TTL is 365 days (8760 hours)';
                previewDiv.className = 'ttl-preview error';
                previewDiv.style.display = 'block';
                return;
            }

            // Calculate expiry date
            const now = new Date();
            const expiry = new Date(now.getTime() + (hours * 60 * 60 * 1000));
            const options = {
                year: 'numeric', month: 'short', day: 'numeric',
                hour: 'numeric', minute: '2-digit', hour12: true
            };

            previewDiv.innerHTML = `Expires: ${expiry.toLocaleDateString('en-US', options)}`;
            previewDiv.className = 'ttl-preview';
            previewDiv.style.display = 'block';
        }

        let authMode = 'mfa'; // 'mfa' or 'magic'

        function showMagicLinkAuth() {
            authMode = 'magic';
            document.getElementById('emailForm').style.display = 'block';
            behavioralData.form_fill_start = Date.now();

            // Update UI for magic link
            const button = document.querySelector('#emailForm button');
            button.textContent = '✨ Send Magic Link';
            button.onclick = sendMagicLink;

            // Update instructions
            const label = document.querySelector('#emailForm label');
            label.textContent = 'Email Address (for magic link)';
        }

        function showMFAAuth() {
            authMode = 'mfa';
            document.getElementById('emailForm').style.display = 'block';
            behavioralData.form_fill_start = Date.now();

            // Update UI for MFA
            const button = document.querySelector('#emailForm button');
            button.textContent = 'Send Verification Code';
            button.onclick = sendVerificationCode;

            // Update instructions
            const label = document.querySelector('#emailForm label');
            label.textContent = 'Email Address';
        }

        // Keep old function for compatibility
        function showEmailAuth() {
            showMFAAuth();
        }

        async function sendMagicLink() {
            const email = document.getElementById('email').value;
            if (!email) {
                showResult('Please enter email address', 'error');
                return;
            }

            userEmail = email;

            try {
                const response = await fetch('/api/send-magic-link', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        email: email,
                        returnUrl: window.location.origin
                    })
                });

                const data = await response.json();
                if (response.ok) {
                    showResult('✨ Magic link sent! Check your email and click the link to login instantly.', 'success');

                    // Hide the form
                    document.getElementById('emailForm').style.display = 'none';

                    // Show waiting message
                    document.querySelector('.auth-section p').innerHTML = '📧 <strong>Magic link sent!</strong> Check your email and click the link to authenticate.';
                } else {
                    showResult(data.error, 'error');
                }
            } catch (error) {
                showResult('Error sending magic link', 'error');
            }
        }

        // Handle magic link authentication when page loads with token
        async function checkMagicLinkAuth() {
            const urlParams = new URLSearchParams(window.location.search);
            const token = urlParams.get('auth');

            if (token) {
                try {
                    const response = await fetch('/api/verify-magic-link', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ token: token })
                    });

                    const data = await response.json();
                    if (response.ok) {
                        userEmail = data.email;
                        userSecret = data.userSecret;

                        showResult('✨ Successfully authenticated via magic link!', 'success');
                        document.getElementById('authSection').style.display = 'none';
                        document.getElementById('createForm').style.display = 'block';
                        document.getElementById('listSecretsBtn').style.display = 'block';

                        // Clean URL
                        window.history.replaceState({}, document.title, window.location.pathname);
                    } else {
                        showResult('Invalid or expired magic link', 'error');
                    }
                } catch (error) {
                    showResult('Error verifying magic link', 'error');
                }
            }
        }

        function showCreateView() {
            // Hide any modals
            const modals = document.querySelectorAll('.modal');
            modals.forEach(modal => modal.remove());

            // Hide return button, show list secrets button
            document.getElementById('returnBtn').style.display = 'none';
            document.getElementById('listSecretsBtn').style.display = 'block';

            // Update header title
            document.querySelector('.header-section h1').textContent = '🔒 Trufo - Create Secret';

            // Show create form and intro, hide result
            document.getElementById('welcomeMessage').style.display = 'block';
            document.getElementById('authSection').style.display = userEmail && userSecret ? 'none' : 'block';
            document.getElementById('createForm').style.display = userEmail && userSecret ? 'block' : 'none';
            document.getElementById('result').style.display = 'none';
        }

        function showListSecrets() {
            // Check if user has authentication data (use global variables, not sessionStorage)
            if (!userEmail || !userSecret) {
                alert('Please authenticate first using Email Validation to list your secrets.');
                showEmailAuth();
                return;
            }

            // Hide create form and intro, show return button
            document.getElementById('welcomeMessage').style.display = 'none';
            document.getElementById('authSection').style.display = 'none';
            document.getElementById('createForm').style.display = 'none';
            document.getElementById('result').style.display = 'none';

            // Show return button, hide list secrets button
            document.getElementById('returnBtn').style.display = 'block';
            document.getElementById('listSecretsBtn').style.display = 'none';

            // Update header title
            document.querySelector('.header-section h1').textContent = '📋 My Secrets';

            // Create and show inline secrets list
            showInlineSecretsList(userEmail, userSecret);
        }

        async function showInlineSecretsList(email, secret) {
            try {
                const resultDiv = document.getElementById('result');
                resultDiv.style.display = 'block';
                resultDiv.className = 'result';
                resultDiv.innerHTML = '<div id="secretsList">Loading your secrets...</div>';

                // Fetch user's secrets
                const response = await fetch('/api/list-secrets', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, secret })
                });

                const data = await response.json();
                const secretsList = document.getElementById('secretsList');

                if (data.success && data.secrets && data.secrets.length > 0) {
                    let html = '<div class="secrets-grid">';
                    data.secrets.forEach(secret => {
                        const expires = new Date(secret.ttl).toLocaleDateString('en-US', {
                            year: 'numeric', month: 'short', day: 'numeric',
                            hour: 'numeric', minute: '2-digit', hour12: true
                        });
                        const isExpired = secret.ttl < Date.now();

                        const secretId = secret.token;
                        const guiUrl = `${window.location.origin}/access/${secret.token}?secret=${userSecret}`;
                        const curlCommand = `curl "${window.location.origin}/api/access/${secret.token}?secret=${userSecret}&raw=true"`;

                        window._copyRegistry = window._copyRegistry || {};
                        const rId = `s_${secret.token}`;
                        window._copyRegistry[`${rId}_id`] = secretId;
                        window._copyRegistry[`${rId}_secret`] = userSecret;
                        window._copyRegistry[`${rId}_gui`] = guiUrl;
                        window._copyRegistry[`${rId}_curl`] = curlCommand;

                        html += `
                            <div class="secret-card ${isExpired ? 'expired' : ''}">
                                <div class="secret-header">
                                    <div class="secret-type">${secret.type === 'string' ? '📄 Text' : '📁 File'}</div>
                                    <div class="secret-status">${isExpired ? '🔴 Expired' : '🟢 Active'}</div>
                                </div>
                                <div class="secret-preview">${secret.preview}</div>

                                <div class="secret-credentials">
                                    <div class="credential-row">
                                        <strong>Secret ID:</strong>
                                        <div class="credential-box">
                                            <code class="credential-value">${secretId}</code>
                                            <button onclick="copyFromRegistry('${rId}_id', this)" class="copy-btn-small">📋</button>
                                        </div>
                                    </div>
                                    <div class="credential-row">
                                        <strong>Your Token:</strong>
                                        <div class="credential-box">
                                            <code class="credential-value">${userSecret}</code>
                                            <button onclick="copyFromRegistry('${rId}_secret', this)" class="copy-btn-small">📋</button>
                                        </div>
                                    </div>
                                </div>

                                <div class="secret-meta">
                                    <div>Expires: ${expires}</div>
                                    <div>Security: ${secret.security}</div>
                                    <div>Access Count: ${secret.access_count}</div>
                                </div>

                                <div class="access-options">
                                    <div class="access-option">
                                        <strong>🌐 GUI Access:</strong>
                                        <div class="access-link">
                                            <code>${guiUrl}</code>
                                            <button onclick="copyFromRegistry('${rId}_gui', this)" class="copy-icon">📋</button>
                                        </div>
                                    </div>
                                    <div class="access-option">
                                        <strong>⚡ API Access (raw content):</strong>
                                        <div class="access-link">
                                            <code>${curlCommand}</code>
                                            <button onclick="copyFromRegistry('${rId}_curl', this)" class="copy-icon">📋</button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                    html += '</div>';
                    secretsList.innerHTML = html;
                } else {
                    secretsList.innerHTML = '<div class="no-secrets">📭 No secrets found for this email address.</div>';
                }

            } catch (error) {
                console.error('Error fetching secrets:', error);
                document.getElementById('secretsList').innerHTML = '<div class="error">❌ Error loading secrets. Please try again.</div>';
            }
        }

        async function showListSecretsModal(email, secret) {
            try {
                // Create modal
                const modal = document.createElement('div');
                modal.className = 'modal';
                modal.innerHTML = `
                    <div class="modal-content">
                        <div class="modal-header">
                            <h3>📋 My Secrets</h3>
                            <button type="button" class="close-btn" onclick="closeModal(this)">&times;</button>
                        </div>
                        <div class="modal-body">
                            <div id="secretsList">Loading your secrets...</div>
                        </div>
                    </div>
                `;
                document.body.appendChild(modal);

                // Fetch user's secrets
                const response = await fetch('/api/list-secrets', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, secret })
                });

                const data = await response.json();
                const secretsList = document.getElementById('secretsList');

                if (data.success && data.secrets && data.secrets.length > 0) {
                    let html = '<div class="secrets-grid">';
                    data.secrets.forEach(secret => {
                        const expires = new Date(secret.ttl).toLocaleDateString('en-US', {
                            year: 'numeric', month: 'short', day: 'numeric',
                            hour: 'numeric', minute: '2-digit', hour12: true
                        });
                        const isExpired = secret.ttl < Date.now();

                        const secretId = secret.token;
                        const guiUrl = `${window.location.origin}/access/${secret.token}?secret=${userSecret}`;
                        const curlCommand = `curl "${window.location.origin}/api/access/${secret.token}?secret=${userSecret}&raw=true"`;

                        window._copyRegistry = window._copyRegistry || {};
                        const rId = `s_${secret.token}`;
                        window._copyRegistry[`${rId}_id`] = secretId;
                        window._copyRegistry[`${rId}_secret`] = userSecret;
                        window._copyRegistry[`${rId}_gui`] = guiUrl;
                        window._copyRegistry[`${rId}_curl`] = curlCommand;

                        html += `
                            <div class="secret-card ${isExpired ? 'expired' : ''}">
                                <div class="secret-header">
                                    <div class="secret-type">${secret.type === 'string' ? '📄 Text' : '📁 File'}</div>
                                    <div class="secret-status">${isExpired ? '🔴 Expired' : '🟢 Active'}</div>
                                </div>
                                <div class="secret-preview">${secret.preview}</div>

                                <div class="secret-credentials">
                                    <div class="credential-row">
                                        <strong>Secret ID:</strong>
                                        <div class="credential-box">
                                            <code class="credential-value">${secretId}</code>
                                            <button onclick="copyFromRegistry('${rId}_id', this)" class="copy-btn-small">📋</button>
                                        </div>
                                    </div>
                                    <div class="credential-row">
                                        <strong>Your Token:</strong>
                                        <div class="credential-box">
                                            <code class="credential-value">${userSecret}</code>
                                            <button onclick="copyFromRegistry('${rId}_secret', this)" class="copy-btn-small">📋</button>
                                        </div>
                                    </div>
                                </div>

                                <div class="secret-meta">
                                    <div>Expires: ${expires}</div>
                                    <div>Security: ${secret.security}</div>
                                    <div>Access Count: ${secret.access_count}</div>
                                </div>

                                <div class="access-options">
                                    <div class="access-option">
                                        <strong>🌐 GUI Access:</strong>
                                        <div class="access-link">
                                            <code>${guiUrl}</code>
                                            <button onclick="copyFromRegistry('${rId}_gui', this)" class="copy-icon">📋</button>
                                        </div>
                                    </div>
                                    <div class="access-option">
                                        <strong>⚡ API Access (raw content):</strong>
                                        <div class="access-link">
                                            <code>${curlCommand}</code>
                                            <button onclick="copyFromRegistry('${rId}_curl', this)" class="copy-icon">📋</button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                    html += '</div>';
                    secretsList.innerHTML = html;
                } else {
                    secretsList.innerHTML = '<div class="no-secrets">📭 No secrets found for this email address.</div>';
                }

            } catch (error) {
                console.error('Error fetching secrets:', error);
                document.getElementById('secretsList').innerHTML = '<div class="error">❌ Error loading secrets. Please try again.</div>';
            }
        }

        function closeModal(btn) {
            const modal = btn.closest('.modal');
            if (modal) {
                modal.remove();
            }
        }

        async function checkExistingAuth() {
            const emailInput = document.getElementById('email');
            const email = emailInput.value;

            if (email && email.includes('@')) {
                try {
                    const response = await fetch(`/api/check-auth?email=${encodeURIComponent(email)}`);
                    const data = await response.json();

                    if (data.authenticated) {
                        userEmail = email;
                        userSecret = data.userSecret;
                        showResult('Already authenticated! You can create objects.', 'success');
                        document.getElementById('authSection').style.display = 'none';
                        document.getElementById('createForm').style.display = 'block';

                        // Update welcome message for returning users
                        document.getElementById('welcomeMessage').innerHTML = '<p><strong>Welcome back!</strong> Create text secrets, upload files, or share data with flexible security options.</p>';
                        return true;
                    }
                } catch (error) {
                    console.log('Auth check failed:', error);
                }
            }
            return false;
        }

        async function sendVerificationCode() {
            const email = document.getElementById('email').value;
            if (!email) {
                showResult('Please enter an email address', 'error');
                return;
            }

            // First check if user is already authenticated
            const alreadyAuth = await checkExistingAuth();
            if (alreadyAuth) {
                return; // Skip sending code if already authenticated
            }

            // Calculate timing data
            const now = Date.now();
            behavioralData.form_fill_time = behavioralData.form_fill_start ? now - behavioralData.form_fill_start : 0;
            behavioralData.page_load_time = now - behavioralData.page_load_time;

            const requestData = {
                email,
                behavioral_data: behavioralData
            };

            try {
                const response = await fetch('/api/validate-email', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestData)
                });

                const data = await response.json();
                if (response.ok) {
                    showResult('Verification code sent to your email', 'success');
                    document.getElementById('codeGroup').style.display = 'block';
                    userEmail = email;
                } else {
                    showResult(data.error, 'error');
                }
            } catch (error) {
                showResult('Network error', 'error');
            }
        }

        async function verifyCode() {
            const code = document.getElementById('verificationCode').value;
            if (!code) {
                showResult('Please enter verification code', 'error');
                return;
            }

            try {
                const response = await fetch('/api/verify-code', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: userEmail, code })
                });

                const data = await response.json();
                if (response.ok) {
                    userSecret = data.userSecret;
                    showResult('Email verified! You can now create objects.', 'success');
                    document.getElementById('authSection').style.display = 'none';
                    document.getElementById('createForm').style.display = 'block';
                    // Show the list secrets button after successful authentication
                    document.getElementById('listSecretsBtn').style.display = 'block';

                    // Update welcome message after login
                    document.getElementById('welcomeMessage').innerHTML = '<p><strong>Create Your Secret:</strong> Choose content type, security level, and expiration time.</p>';
                } else {
                    showResult(data.error, 'error');
                }
            } catch (error) {
                showResult('Network error', 'error');
            }
        }

        document.getElementById('createForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const ttlHours = parseTTLToHours(document.getElementById('ttl').value);
            if (!ttlHours || ttlHours <= 0 || ttlHours > 24 * 365) {
                showResult('Please enter a valid TTL (1h to 365d)', 'error');
                return;
            }

            const objectType = document.getElementById('type').value;
            const securityType = document.querySelector('input[name="security"]:checked').value;

            // Generate path from both selections
            const pathType = securityType === 'basic' ? objectType : `${objectType}-${securityType}`;

            const formData = {
                name: document.getElementById('name').value,
                type: objectType,
                securityType: securityType,
                pathType: pathType, // This will be used for S3 path
                content: document.getElementById('content').value,
                ttlHours: ttlHours,
                ownerEmail: userEmail,
                ownerName: userEmail.split('@')[0],
                oneTimeAccess: document.getElementById('oneTimeAccess').checked
            };

            try {
                const response = await fetch('/api/objects', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });

                const data = await response.json();
                if (response.ok) {
                    const accessUrl = `${window.location.origin}/access/${data.object.token}?secret=${userSecret}`;
                    const curlCommand = `curl "${window.location.origin}/api/access/${data.object.token}?secret=${userSecret}&raw=true"`;

                    // Store copy values in a registry to avoid quote escaping issues in inline handlers
                    window._copyRegistry = window._copyRegistry || {};
                    const regId = Date.now();
                    window._copyRegistry[`${regId}_token`] = data.object.token;
                    window._copyRegistry[`${regId}_secret`] = userSecret;
                    window._copyRegistry[`${regId}_gui`] = accessUrl;
                    window._copyRegistry[`${regId}_curl`] = curlCommand;

                    let resultHtml = `<strong>✅ Object created successfully!</strong><br>
                        <div class="secret-credentials" style="margin-top: 1rem;">
                            <div class="credential-row">
                                <strong>Secret ID:</strong>
                                <div class="credential-box">
                                    <code class="credential-value">${data.object.token}</code>
                                    <button onclick="copyFromRegistry('${regId}_token', this)" class="copy-btn-small">📋</button>
                                </div>
                            </div>
                            <div class="credential-row">
                                <strong>Your Token:</strong>
                                <div class="credential-box">
                                    <code class="credential-value">${userSecret}</code>
                                    <button onclick="copyFromRegistry('${regId}_secret', this)" class="copy-btn-small">📋</button>
                                </div>
                            </div>
                        </div>

                        <div class="access-options" style="margin-top: 1rem;">
                            <div class="access-option">
                                <strong>🌐 GUI Access:</strong>
                                <div class="access-link">
                                    <code>${accessUrl}</code>
                                    <button onclick="copyFromRegistry('${regId}_gui', this)" class="copy-icon">📋</button>
                                </div>
                            </div>
                            <div class="access-option">
                                <strong>⚡ API Access (raw content):</strong>
                                <div class="access-link">
                                    <code>${curlCommand}</code>
                                    <button onclick="copyFromRegistry('${regId}_curl', this)" class="copy-icon">📋</button>
                                </div>
                            </div>
                        </div>`;

                    // Show TOTP and recovery codes if applicable (ONLY SHOWN ONCE!)
                    if (data.security && data.security.totpSecret) {
                        resultHtml += `<br><br>
                            <div style="border: 2px solid #dc3545; padding: 1rem; margin-top: 1rem; border-radius: 6px; background: #fff5f5;">
                                <h4 style="color: #dc3545; margin-bottom: 1rem;">⚠️ SAVE THIS INFORMATION NOW - IT WON'T BE SHOWN AGAIN!</h4>

                                <strong>📱 TOTP Secret (for authenticator app):</strong><br>
                                <code style="background: #f8f9fa; padding: 0.25rem;">${data.security.totpSecret}</code><br><br>

                                <strong>📲 QR Code URL (scan with authenticator app):</strong><br>
                                <small style="word-break: break-all; font-family: monospace;">${data.security.totpQR}</small><br><br>

                                <strong>🔑 Emergency Backup Codes (use if you lose your phone):</strong><br>
                                <div style="background: #f8f9fa; padding: 0.5rem; border-radius: 4px; font-family: monospace;">`;

                        data.security.recoveryCodes.forEach((code, index) => {
                            resultHtml += `${code}${index % 2 === 1 ? '<br>' : '&nbsp;&nbsp;&nbsp;'}`;
                        });

                        resultHtml += `</div>
                                <small style="color: #666;">Each backup code can only be used once. Store them securely!</small>
                            </div>`;
                    }

                    resultHtml += '</div>';
                    showResult(resultHtml, 'success');

                    // Hide create form and intro after successful creation
                    document.getElementById('createForm').style.display = 'none';
                    document.getElementById('welcomeMessage').style.display = 'none';

                    // Show return button, hide list secrets button
                    document.getElementById('returnBtn').style.display = 'block';
                    document.getElementById('listSecretsBtn').style.display = 'none';

                    // Update header title
                    document.querySelector('.header-section h1').textContent = '✅ Secret Created';

                    document.getElementById('createForm').reset();
                } else {
                    showResult(data.error, 'error');
                }
            } catch (error) {
                showResult('Network error', 'error');
            }
        });

        function showResult(message, type) {
            const result = document.getElementById('result');
            result.innerHTML = message;
            result.className = `result ${type}`;
            result.style.display = 'block';
        }

        let _boolValue = true;

        function toggleBoolSwitch() {
            _boolValue = !_boolValue;
            const label = document.getElementById('boolSwitchLabel');
            const track = document.getElementById('boolToggleTrack');
            const thumb = document.getElementById('boolToggleThumb');
            label.textContent = _boolValue ? 'true' : 'false';
            track.style.background = _boolValue ? '#667eea' : '#ccc';
            thumb.style.transform = _boolValue ? 'translateX(24px)' : 'translateX(0)';
            document.getElementById('content').value = String(_boolValue);
        }

        function setupFormHandlers() {
            // Handle object type changes for content placeholder
            document.getElementById('type').addEventListener('change', function(e) {
                const contentField = document.getElementById('content');
                const boolSwitch = document.getElementById('booleanSwitch');
                const type = e.target.value;

                if (type === 'boolean' || type === 'toggle') {
                    _boolValue = true;
                    contentField.value = 'true';
                    contentField.style.display = 'none';
                    document.getElementById('contentSizeHint').style.display = 'none';
                    boolSwitch.style.display = 'block';
                    // Reset switch to true
                    document.getElementById('boolSwitchLabel').textContent = 'true';
                    document.getElementById('boolToggleTrack').style.background = '#667eea';
                    document.getElementById('boolToggleThumb').style.transform = 'translateX(24px)';
                } else {
                    contentField.style.display = '';
                    document.getElementById('contentSizeHint').style.display = '';
                    boolSwitch.style.display = 'none';
                    contentField.placeholder = 'Your secret content here...';
                    contentField.value = '';
                }
            });

            // Handle security option clicks
            document.querySelectorAll('.security-option').forEach(option => {
                option.addEventListener('click', function() {
                    const radio = this.querySelector('input[type="radio"]');
                    radio.checked = true;

                    // Update visual selection
                    document.querySelectorAll('.security-option').forEach(opt => {
                        opt.style.borderColor = '#e1e5e9';
                        opt.style.background = 'white';
                    });
                    this.style.borderColor = '#667eea';
                    this.style.background = '#f0f4ff';

                    // Show/hide auth section based on security level
                    updateAuthSection();
                });
            });
        }

        function updateAuthSection() {
            const securityValue = document.querySelector('input[name="security"]:checked').value;
            const authSection = document.getElementById('authSection');
            const createForm = document.getElementById('createForm');

            // All security types require email authentication to CREATE
            // "None" just means no verification needed to VIEW later
            if (userEmail && userSecret) {
                // Already authenticated
                authSection.style.display = 'none';
                createForm.style.display = 'block';
            } else {
                // Need authentication for all security types
                authSection.style.display = 'block';
                createForm.style.display = 'none';
            }
        }

        function showTextContent() {
            document.getElementById('textContent').style.display = 'block';
            document.getElementById('fileContent').style.display = 'none';
            document.querySelectorAll('.content-tab').forEach(tab => tab.classList.remove('active'));
            document.querySelector('.content-tab:first-child').classList.add('active');
            document.getElementById('content').required = true;
            document.getElementById('fileInput').required = false;
        }

        function showFileContent() {
            document.getElementById('textContent').style.display = 'none';
            document.getElementById('fileContent').style.display = 'block';
            document.querySelectorAll('.content-tab').forEach(tab => tab.classList.remove('active'));
            document.querySelector('.content-tab:last-child').classList.add('active');
            document.getElementById('content').required = false;
            document.getElementById('fileInput').required = true;

            // Set default type for files (files are always "string" type in backend)
            document.getElementById('type').value = 'string';

            // Setup file input handler
            const fileInput = document.getElementById('fileInput');
            if (!fileInput.hasAttribute('data-setup')) {
                fileInput.addEventListener('change', handleFileSelect);
                fileInput.setAttribute('data-setup', 'true');
            }
        }

        function handleFileSelect(event) {
            const file = event.target.files[0];
            if (!file) return;

            const preview = document.getElementById('filePreview');

            // Check file size (1MB = 1024*1024 bytes)
            if (file.size > 1024 * 1024) {
                preview.innerHTML = '<span style="color: #721c24;">⚠️ File too large. Maximum size is 1MB.</span>';
                event.target.value = '';
                return;
            }

            preview.innerHTML = `📁 ${file.name} (${(file.size/1024).toFixed(1)}KB)`;

            // Read file as base64
            const reader = new FileReader();
            reader.onload = function(e) {
                // Store base64 data in hidden content field
                document.getElementById('content').value = JSON.stringify({
                    type: 'file',
                    filename: file.name,
                    mimetype: file.type,
                    size: file.size,
                    data: e.target.result
                });
            };
            reader.readAsDataURL(file);
        }

        function copyFromRegistry(key, buttonElement) {{
            const text = (window._copyRegistry || {})[key];
            if (text) copyTextToClipboard(text, buttonElement);
        }}

        function copyTextToClipboard(text, buttonElement) {{
            navigator.clipboard.writeText(text).then(() => {{
                const originalText = buttonElement.textContent;
                const originalBg = buttonElement.style.background;
                buttonElement.textContent = '✓';
                buttonElement.style.background = '#28a745';
                buttonElement.style.color = 'white';
                setTimeout(() => {{
                    buttonElement.textContent = originalText;
                    buttonElement.style.background = originalBg;
                    buttonElement.style.color = '';
                }}, 2000);
            }}).catch(() => {{
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                const originalText = buttonElement.textContent;
                buttonElement.textContent = '✓';
                setTimeout(() => {{ buttonElement.textContent = originalText; }}, 2000);
            }});
        }}
    </script>
    <div style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e1e5e9; text-align: center; font-size: 0.8rem; color: #999;">
        <a href="https://github.com/maimon33/trufo" target="_blank" rel="noopener noreferrer" style="color: #999; text-decoration: none; margin: 0 0.75rem;">Source</a>
        <a href="https://github.com/maimon33/chrome-extensions" target="_blank" rel="noopener noreferrer" style="color: #999; text-decoration: none; margin: 0 0.75rem;">Chrome Extension</a>
        <a href="https://www.maimons.dev" target="_blank" rel="noopener noreferrer" style="color: #999; text-decoration: none; margin: 0 0.75rem;">maimons.dev</a>
    </div>
</body>
</html>
    """

def serve_access_page(token: str, query_params: dict) -> str:
    """Return HTML for object access page"""
    secret = query_params.get('secret', '')

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trufo - Access Secret</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            background: white;
            border-radius: 12px;
            padding: 2rem;
            max-width: 600px;
            width: 100%;
            margin: 2rem auto;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #333; margin-bottom: 1.5rem; text-align: center; }}
        .form-group {{ margin-bottom: 1rem; }}
        label {{ display: block; margin-bottom: 0.5rem; color: #555; font-weight: 500; }}
        input {{
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #e1e5e9;
            border-radius: 6px;
            font-size: 1rem;
        }}
        button {{
            width: 100%;
            padding: 1rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            margin-top: 1rem;
        }}
        .content {{
            background: #f8f9fa;
            border-radius: 6px;
            padding: 1.5rem;
            margin-top: 1.5rem;
            font-family: monospace;
            word-break: break-all;
        }}
        .result {{
            margin-top: 1.5rem;
            padding: 1rem;
            border-radius: 6px;
            display: none;
        }}
        .result.success {{ background: #d4edda; color: #155724; }}
        .result.error {{ background: #f8d7da; color: #721c24; }}
        .totp-section {{ display: none; }}
        .qr-code {{ text-align: center; margin: 1rem 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔓 Access Secret Object</h1>

        <p style="font-size: 0.8rem; color: #666; text-align: center; margin-bottom: 1rem;">
            📊 <em>Anonymous usage statistics are collected (no content or emails stored)</em>
        </p>

        <div class="form-group">
            <label for="secret">Your Secret Key</label>
            <input type="text" id="secret" value="{secret}" placeholder="Enter your secret key" required>
        </div>

        <div class="totp-section" id="totpSection">
            <div class="form-group">
                <label for="totpCode">TOTP Code</label>
                <input type="text" id="totpCode" placeholder="123456" maxlength="6">
                <div class="qr-code" id="qrCode"></div>
            </div>
        </div>

        <button onclick="accessObject()" id="accessBtn">Access Object</button>

        <div id="onetimeWarning" style="display:none; margin-top:1.5rem; padding:1.25rem; background:#fff3cd; border:2px solid #ffc107; border-radius:8px; text-align:center;">
            <p style="font-size:1.1rem; font-weight:700; color:#856404; margin-bottom:0.5rem;">⚠️ One-Time Secret</p>
            <p style="color:#856404; margin-bottom:1.25rem;">This secret will be <strong>permanently deleted</strong> once viewed. You cannot un-see it or view it again.</p>
            <div style="display:flex; gap:0.75rem; justify-content:center; flex-wrap:wrap;">
                <button onclick="confirmView()" style="width:auto; padding:0.75rem 1.5rem; background:#dc3545; margin-top:0;">View Secret (will be deleted)</button>
                <button onclick="cancelView()" style="width:auto; padding:0.75rem 1.5rem; background:#6c757d; margin-top:0;">Leave Without Viewing</button>
            </div>
        </div>

        <div id="result" class="result"></div>
        <div id="content" class="content" style="display: none;"></div>
    </div>

    <script>
        const token = '{token}';
        let requiresTOTP = false;
        let pendingSecret = null;
        let pendingTotpCode = null;

        async function accessObject() {{
            const secret = document.getElementById('secret').value;
            const totpCode = document.getElementById('totpCode').value;

            if (!secret) {{
                showResult('Please enter your secret key', 'error');
                return;
            }}

            try {{
                // Check metadata first to see if this is a one-time secret
                const infoResponse = await fetch(`/api/info/${{token}}`);
                if (infoResponse.ok) {{
                    const info = await infoResponse.json();
                    if (info.oneTimeAccess) {{
                        // Show warning UI, defer actual access
                        pendingSecret = secret;
                        pendingTotpCode = totpCode;
                        document.getElementById('accessBtn').style.display = 'none';
                        document.getElementById('onetimeWarning').style.display = 'block';
                        return;
                    }}
                }}
            }} catch (e) {{
                // If info check fails, proceed normally
            }}

            await doAccess(secret, totpCode);
        }}

        async function confirmView() {{
            document.getElementById('onetimeWarning').style.display = 'none';
            document.getElementById('accessBtn').style.display = 'block';
            await doAccess(pendingSecret, pendingTotpCode);
        }}

        function cancelView() {{
            document.getElementById('onetimeWarning').style.display = 'none';
            document.getElementById('accessBtn').style.display = 'block';
            showResult('Access cancelled. The secret was not viewed.', 'error');
        }}

        async function doAccess(secret, totpCode) {{
            try {{
                let url = `/api/objects?token=${{token}}&secret=${{secret}}`;
                if (totpCode) {{
                    url += `&totpCode=${{totpCode}}`;
                }}

                const response = await fetch(url);
                const data = await response.json();

                if (response.ok) {{
                    document.getElementById('content').innerHTML = `
                        <strong>Content:</strong><br>
                        ${{JSON.stringify(data.content, null, 2)}}
                        ${{data.oneTimeAccess ? '<div style="margin-top:1rem; padding:0.75rem; background:#f8d7da; border-radius:6px; color:#721c24; font-weight:700; font-family:sans-serif;">🔥 This secret has been permanently deleted and will never be shown again.</div>' : ''}}
                    `;
                    document.getElementById('content').style.display = 'block';
                    showResult('Object accessed successfully!', 'success');
                }} else if (data.requiresTOTP) {{
                    requiresTOTP = true;
                    document.getElementById('totpSection').style.display = 'block';
                    if (data.totpQR) {{
                        document.getElementById('qrCode').innerHTML = `
                            <p>Scan this with your authenticator app:</p>
                            <div style="margin: 1rem 0; padding: 1rem; background: white; font-size: 0.8rem; word-break: break-all;">
                                ${{data.totpQR}}
                            </div>
                        `;
                    }}
                    showResult('TOTP verification required', 'error');
                }} else {{
                    showResult(data.error, 'error');
                }}
            }} catch (error) {{
                showResult('Network error', 'error');
            }}
        }}

        function showResult(message, type) {{
            const result = document.getElementById('result');
            result.innerHTML = message;
            result.className = `result ${{type}}`;
            result.style.display = 'block';
        }}

        // Auto-access if secret is provided
        if ('{secret}') {{
            accessObject();
        }}
    </script>
</body>
</html>
    """

def serve_manage_page() -> str:
    """Return HTML for object management page"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trufo - Manage Objects</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 12px;
            padding: 2rem;
            max-width: 1000px;
            width: 100%;
            margin: 2rem auto;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        h1 { color: #333; margin-bottom: 1.5rem; text-align: center; }
        .auth-form { margin-bottom: 2rem; }
        .form-group { margin-bottom: 1rem; }
        label { display: block; margin-bottom: 0.5rem; color: #555; font-weight: 500; }
        input {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #e1e5e9;
            border-radius: 6px;
            font-size: 1rem;
            max-width: 300px;
        }
        button {
            padding: 0.75rem 1.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            margin-left: 1rem;
        }
        .objects-grid { display: grid; gap: 1rem; margin-top: 2rem; }
        .object-card {
            border: 1px solid #e1e5e9;
            border-radius: 6px;
            padding: 1rem;
            background: #f8f9fa;
        }
        .object-header { display: flex; justify-content: between; align-items: center; margin-bottom: 0.5rem; }
        .object-name { font-weight: 600; color: #333; }
        .object-type { color: #666; font-size: 0.9rem; }
        .object-meta { font-size: 0.9rem; color: #666; margin: 0.5rem 0; }
        .object-actions { margin-top: 1rem; }
        .btn-small {
            padding: 0.5rem 1rem;
            font-size: 0.9rem;
            margin-right: 0.5rem;
        }
        .btn-danger { background: #dc3545; }
        .expired { opacity: 0.6; }
        .result {
            margin-top: 1rem;
            padding: 1rem;
            border-radius: 6px;
            display: none;
        }
        .result.success { background: #d4edda; color: #155724; }
        .result.error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Manage Your Objects</h1>

        <p style="font-size: 0.8rem; color: #666; text-align: center; margin-bottom: 1.5rem;">
            📊 <em>Anonymous usage statistics are collected (no content or emails stored)</em>
        </p>

        <div class="auth-form">
            <div class="form-group">
                <label for="email">Email Address</label>
                <input type="email" id="email" placeholder="your@email.com">
                <label for="secret">User Secret</label>
                <input type="password" id="secret" placeholder="Your user secret">
                <button onclick="authenticateAndLoad()">Authenticate & Load Objects</button>
            </div>
        </div>

        <div id="result" class="result"></div>
        <div id="objectsContainer" class="objects-grid"></div>
    </div>

    <script>
        async function authenticateAndLoad() {
            const email = document.getElementById('email').value;
            const secret = document.getElementById('secret').value;

            if (!email || !secret) {
                showResult('Please enter both email and secret', 'error');
                return;
            }

            try {
                const response = await fetch('/api/list-objects', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ email, secret })
                });
                const data = await response.json();

                if (response.ok) {
                    displayObjects(data.objects);
                    showResult(`Found ${data.objects.length} objects`, 'success');
                    // Store credentials for delete operations
                    window.userCredentials = { email, secret };
                } else {
                    showResult(data.error || 'Authentication failed', 'error');
                }
            } catch (error) {
                showResult('Network error', 'error');
            }
        }

        function displayObjects(objects) {
            const container = document.getElementById('objectsContainer');
            const now = Date.now();

            if (objects.length === 0) {
                container.innerHTML = '<p style="text-align: center; color: #666;">No objects found</p>';
                return;
            }

            container.innerHTML = objects.map(obj => {
                const expired = obj.ttl <= now;
                const expiresAt = new Date(obj.ttl).toLocaleString();
                const createdAt = new Date(obj.createdAt).toLocaleString();

                return `
                    <div class="object-card ${expired ? 'expired' : ''}">
                        <div class="object-header">
                            <div>
                                <div class="object-name">${obj.name}</div>
                                <div class="object-type">${obj.type.toUpperCase()}</div>
                            </div>
                            <div style="text-align: right;">
                                ${expired ? '<span style="color: red;">EXPIRED</span>' : '<span style="color: green;">ACTIVE</span>'}
                            </div>
                        </div>
                        <div class="object-meta">
                            Created: ${createdAt}<br>
                            Expires: ${expiresAt}<br>
                            Hits: ${obj.hitCount}<br>
                            ${obj.oneTimeAccess ? 'One-time access • ' : ''}
                            ${obj.totpSecret ? 'MFA enabled' : 'No MFA'}
                        </div>
                        <div class="object-actions">
                            <button class="btn-small" onclick="copyAccessLink('${obj.token}')">Copy Access Link</button>
                            <button class="btn-small btn-danger" onclick="deleteObject('${obj.id}', '${obj.s3Key}', '${obj.name}')">Delete</button>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function copyAccessLink(token) {
            const email = document.getElementById('email').value;
            // Generate user secret (same logic as backend)
            const userSecret = CryptoJS.SHA256(email.toLowerCase()).toString();
            const link = `${window.location.origin}/access/${token}?secret=${userSecret}`;

            navigator.clipboard.writeText(link).then(() => {
                showResult('Access link copied to clipboard!', 'success');
            });
        }

        async function deleteObject(objectId, s3Key, objectName) {
            if (!confirm(`Are you sure you want to delete "${objectName}"?`)) {
                return;
            }

            if (!window.userCredentials) {
                showResult('Please authenticate first', 'error');
                return;
            }

            try {
                const response = await fetch('/api/delete-object', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        email: window.userCredentials.email,
                        secret: window.userCredentials.secret,
                        objectId: objectId,
                        s3Key: s3Key
                    })
                });
                const data = await response.json();

                if (response.ok) {
                    showResult(data.message || 'Object deleted successfully', 'success');
                    authenticateAndLoad(); // Reload the list
                } else {
                    showResult(data.error || 'Delete failed', 'error');
                }
            } catch (error) {
                showResult('Network error', 'error');
            }
        }

        function showResult(message, type) {
            const result = document.getElementById('result');
            result.innerHTML = message;
            result.className = `result ${type}`;
            result.style.display = 'block';
        }

        function copyToClipboard(elementId) {
            const element = document.getElementById(elementId);
            const text = element.textContent;

            navigator.clipboard.writeText(text).then(() => {
                // Visual feedback
                const button = element.parentElement.querySelector('.copy-btn');
                const originalText = button.textContent;
                button.textContent = 'Copied!';
                button.style.background = '#28a745';

                setTimeout(() => {
                    button.textContent = originalText;
                    button.style.background = '#667eea';
                }, 2000);
            }).catch(() => {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);

                // Visual feedback
                const button = element.parentElement.querySelector('.copy-btn');
                const originalText = button.textContent;
                button.textContent = 'Copied!';
                button.style.background = '#28a745';

                setTimeout(() => {
                    button.textContent = originalText;
                    button.style.background = '#667eea';
                }, 2000);
            });
        }

        function copyFromRegistry(key, buttonElement) {
            const text = (window._copyRegistry || {})[key];
            if (text) copyTextToClipboard(text, buttonElement);
        }

        function copyTextToClipboard(text, buttonElement) {
            console.log('Copy function called with:', text, buttonElement);
            navigator.clipboard.writeText(text).then(() => {
                console.log('Copy successful');
                // Visual feedback
                const originalText = buttonElement.textContent;
                const originalBg = buttonElement.style.background;
                buttonElement.textContent = '✓';
                buttonElement.style.background = '#28a745';
                buttonElement.style.color = 'white';
                setTimeout(() => {
                    buttonElement.textContent = originalText;
                    buttonElement.style.background = originalBg;
                    buttonElement.style.color = '';
                }, 2000);
            }).catch((err) => {
                console.log('Clipboard API failed, using fallback:', err);
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);

                // Visual feedback
                const originalText = buttonElement.textContent;
                const originalBg = buttonElement.style.background;
                buttonElement.textContent = '✓';
                buttonElement.style.background = '#28a745';
                buttonElement.style.color = 'white';
                setTimeout(() => {
                    buttonElement.textContent = originalText;
                    buttonElement.style.background = originalBg;
                    buttonElement.style.color = '';
                }, 2000);
            });
        }
    </script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/crypto-js.min.js"></script>
    <div style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e1e5e9; text-align: center; font-size: 0.8rem; color: #999;">
        <a href="https://github.com/maimon33/trufo" target="_blank" rel="noopener noreferrer" style="color: #999; text-decoration: none; margin: 0 0.75rem;">Source</a>
        <a href="https://github.com/maimon33/chrome-extensions" target="_blank" rel="noopener noreferrer" style="color: #999; text-decoration: none; margin: 0 0.75rem;">Chrome Extension</a>
        <a href="https://www.maimons.dev" target="_blank" rel="noopener noreferrer" style="color: #999; text-decoration: none; margin: 0 0.75rem;">maimons.dev</a>
    </div>
</body>
</html>
    """