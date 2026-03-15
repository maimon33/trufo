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
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 12px;
            padding: 2rem;
            max-width: 600px;
            width: 100%;
            margin: 2rem auto;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        h1 { color: #333; margin-bottom: 1.5rem; text-align: center; }
        .form-group { margin-bottom: 1rem; }
        label { display: block; margin-bottom: 0.5rem; color: #555; font-weight: 500; }
        input, textarea, select {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #e1e5e9;
            border-radius: 6px;
            font-size: 1rem;
            transition: border-color 0.2s;
        }
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        textarea { min-height: 100px; resize: vertical; }
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
            padding: 1rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 1rem;
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
            border-radius: 6px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            border-left: 4px solid #667eea;
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
        .auth-button {
            background: #4285f4;
            margin-bottom: 0.5rem;
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
        .ttl-presets {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 0.75rem;
            flex-wrap: wrap;
        }
        .preset-btn {
            background: #f8f9fa;
            border: 2px solid #e1e5e9;
            border-radius: 4px;
            padding: 0.5rem 0.75rem;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.2s;
            color: #555;
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
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 Trufo - Create Secret</h1>

        <div class="intro-section">
            <p><strong>Welcome to Trufo!</strong> A secure way to share temporary secrets and sensitive data.</p>
            <p>You can create different types of secrets:</p>
            <ul>
                <li><strong>Text/String:</strong> Passwords, API keys, private notes</li>
                <li><strong>Boolean:</strong> True/false flags for configuration</li>
                <li><strong>Auto-Toggle:</strong> Values that flip between true/false on each access</li>
            </ul>
            <p>All secrets expire automatically and can be protected with TOTP 2FA.</p>
        </div>

        <div class="auth-section" id="authSection">
            <p>Choose authentication method:</p>
            <button type="button" class="auth-button" onclick="showEmailAuth()">Email Validation</button>
            <div class="email-form" id="emailForm">
                <div class="form-group">
                    <label for="email">Email Address</label>
                    <input type="email" id="email" placeholder="your@email.com" required>
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
                <label for="type">Object Type</label>
                <select id="type" required>
                    <option value="string">Text/String</option>
                    <option value="boolean">True/False</option>
                    <option value="toggle">Auto-Toggle</option>
                </select>
            </div>

            <div class="form-group">
                <label for="content">Content</label>
                <textarea id="content" placeholder="Your secret content here..." required></textarea>
            </div>

            <div class="form-group">
                <label for="ttl">Expires After</label>
                <div class="ttl-presets">
                    <button type="button" class="preset-btn" data-value="1h">1h</button>
                    <button type="button" class="preset-btn" data-value="6h">6h</button>
                    <button type="button" class="preset-btn" data-value="24h">24h</button>
                    <button type="button" class="preset-btn" data-value="7d">7d</button>
                    <button type="button" class="preset-btn" data-value="30d">30d</button>
                </div>
                <div class="ttl-custom">
                    <input type="text" id="ttl" placeholder="24h" value="24h" pattern="^\\d+[hHdDwWmMyY]$" required>
                    <small>Examples: 1h, 24h, 7d, 30d, 1y (max: 365d)</small>
                </div>
                <div id="ttlPreview" class="ttl-preview"></div>
            </div>

            <div class="form-group">
                <div class="checkbox-group">
                    <input type="checkbox" id="oneTimeAccess">
                    <label for="oneTimeAccess">One-time access (delete after reading)</label>
                </div>
                <div class="checkbox-group">
                    <input type="checkbox" id="enableMFA">
                    <label for="enableMFA">Enable TOTP 2FA</label>
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

        function showEmailAuth() {
            document.getElementById('emailForm').style.display = 'block';
            behavioralData.form_fill_start = Date.now();
        }

        async function sendVerificationCode() {
            const email = document.getElementById('email').value;
            if (!email) {
                showResult('Please enter an email address', 'error');
                return;
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

            const formData = {
                name: document.getElementById('name').value,
                type: document.getElementById('type').value,
                content: document.getElementById('content').value,
                ttlHours: ttlHours,
                ownerEmail: userEmail,
                ownerName: userEmail.split('@')[0],
                oneTimeAccess: document.getElementById('oneTimeAccess').checked,
                enableMFA: document.getElementById('enableMFA').checked
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
                    showResult(`<strong>Object created successfully!</strong><br><div class="access-info"><strong>Access URL:</strong><br><a href="${accessUrl}" target="_blank">${accessUrl}</a><br><br><strong>Token:</strong> ${data.object.token}<br><strong>Your Secret:</strong> ${userSecret}</div>`, 'success');
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

        // Handle boolean/toggle content
        document.getElementById('type').addEventListener('change', (e) => {
            const contentField = document.getElementById('content');
            if (e.target.value === 'boolean' || e.target.value === 'toggle') {
                contentField.value = 'true';
                contentField.placeholder = 'true or false';
            } else {
                contentField.placeholder = 'Your secret content here...';
            }
        });
    </script>
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

        <button onclick="accessObject()">Access Object</button>

        <div id="result" class="result"></div>
        <div id="content" class="content" style="display: none;"></div>
    </div>

    <script>
        const token = '{token}';
        let requiresTOTP = false;

        async function accessObject() {{
            const secret = document.getElementById('secret').value;
            const totpCode = document.getElementById('totpCode').value;

            if (!secret) {{
                showResult('Please enter your secret key', 'error');
                return;
            }}

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
                        ${{JSON.stringify(data.content, null, 2)}}<br><br>
                        <strong>Access Count:</strong> ${{data.hits}}
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

        <div class="auth-form">
            <div class="form-group">
                <label for="email">Email Address</label>
                <input type="email" id="email" placeholder="your@email.com">
                <button onclick="loadObjects()">Load My Objects</button>
            </div>
        </div>

        <div id="result" class="result"></div>
        <div id="objectsContainer" class="objects-grid"></div>
    </div>

    <script>
        async function loadObjects() {
            const email = document.getElementById('email').value;
            if (!email) {
                showResult('Please enter your email address', 'error');
                return;
            }

            try {
                const response = await fetch(`/api/user-objects?email=${encodeURIComponent(email)}`);
                const data = await response.json();

                if (response.ok) {
                    displayObjects(data.objects);
                    showResult(`Found ${data.objects.length} objects`, 'success');
                } else {
                    showResult(data.error, 'error');
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
                            <button class="btn-small btn-danger" onclick="deleteObject('${obj.id}')">Delete</button>
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

        async function deleteObject(objectId) {
            if (!confirm('Are you sure you want to delete this object?')) return;

            try {
                const response = await fetch(`/api/objects?id=${objectId}`, {
                    method: 'DELETE'
                });

                const data = await response.json();
                if (response.ok) {
                    showResult('Object deleted successfully', 'success');
                    loadObjects(); // Reload the list
                } else {
                    showResult(data.error, 'error');
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
    </script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/crypto-js.min.js"></script>
</body>
</html>
    """