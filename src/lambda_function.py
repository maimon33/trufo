import json
import boto3
import hashlib
import uuid
import time
import base64
import hmac
import secrets
import mimetypes
from datetime import datetime, timedelta
from urllib.parse import parse_qs, unquote
import os
from typing import Dict, Any, Optional, Tuple, List
from templates import serve_create_page, serve_access_page, serve_manage_page

# PWA static files directory (populated at build time by CI)
_PWA_DIR = os.path.join(os.path.dirname(__file__), 'pwa_static')

_TEXT_TYPES = {
    'application/javascript', 'application/json', 'image/svg+xml',
    'text/html', 'text/css', 'text/plain',
}

def _serve_pwa(file_path: str) -> Dict[str, Any]:
    """Serve a static file from pwa_static, with SPA fallback to index.html."""
    # Strip leading slash
    file_path = file_path.lstrip('/')

    full = os.path.join(_PWA_DIR, file_path)

    # Security: prevent path traversal
    if not os.path.abspath(full).startswith(os.path.abspath(_PWA_DIR)):
        return {'statusCode': 403, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': 'Forbidden'}

    # SPA fallback: unknown paths serve index.html (client-side routing)
    if not os.path.isfile(full):
        full = os.path.join(_PWA_DIR, 'index.html')

    content_type, _ = mimetypes.guess_type(full)
    content_type = content_type or 'application/octet-stream'

    # Long cache for hashed assets, no-cache for shell files
    is_hashed_asset = '/assets/' in full
    cache = 'public, max-age=31536000, immutable' if is_hashed_asset else 'no-cache'

    with open(full, 'rb') as f:
        raw = f.read()

    if content_type in _TEXT_TYPES:
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': content_type,
                'Cache-Control': cache,
                'Access-Control-Allow-Origin': '*',
            },
            'body': raw.decode('utf-8'),
        }
    else:
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': content_type,
                'Cache-Control': cache,
                'Access-Control-Allow-Origin': '*',
            },
            'body': base64.b64encode(raw).decode(),
            'isBase64Encoded': True,
        }

# AWS clients
s3_client = boto3.client('s3')
cloudwatch_client = boto3.client('cloudwatch')

# Configuration
BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'trufo-storage')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@trufo.com')
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', 'default-key-change-in-production-32b')
SESSION_SIGNING_KEY = os.environ.get('SESSION_SIGNING_KEY', '')

# AWS SES client
ses_client = boto3.client('ses')

def _auth_record_key(kind: str, identifier: str) -> str:
    return f'auth/{kind}/{identifier}.json'

def put_auth_record(kind: str, identifier: str, data: Dict[str, Any]) -> None:
    """Persist short-lived authentication challenges so cold starts are safe."""
    s3_client.put_object(Bucket=BUCKET_NAME, Key=_auth_record_key(kind, identifier),
                         Body=json.dumps(data), ContentType='application/json')

def get_auth_record(kind: str, identifier: str) -> Optional[Dict[str, Any]]:
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=_auth_record_key(kind, identifier))
        return json.loads(response['Body'].read())
    except s3_client.exceptions.NoSuchKey:
        return None

def delete_auth_record(kind: str, identifier: str) -> None:
    s3_client.delete_object(Bucket=BUCKET_NAME, Key=_auth_record_key(kind, identifier))

def get_anonymous_user_id(email: str) -> str:
    """Generate anonymous user ID from email for analytics"""
    return hashlib.sha256(email.encode()).hexdigest()[:8]

def calculate_size_category(content_size: int) -> str:
    """Categorize content size for analytics"""
    if content_size < 1024:  # < 1KB
        return 'small'
    elif content_size < 10240:  # < 10KB
        return 'medium'
    elif content_size < 102400:  # < 100KB
        return 'large'
    else:  # >= 100KB
        return 'xlarge'

def verify_user_auth(body: Dict[str, Any]) -> Tuple[bool, str, str]:
    """Verify a signed, short-lived owner session without a session database."""
    email = body.get('email')
    session = body.get('session')

    if not email or not session:
        return False, "Email and session are required", ""

    try:
        normalized_email = normalize_email(email)
        payload_b64, signature = session.split('.', 1)
        if not SESSION_SIGNING_KEY:
            return False, "Authentication is not configured", ""
        expected = hmac.new(SESSION_SIGNING_KEY.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return False, "Invalid authentication session", ""
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + '=' * (-len(payload_b64) % 4)))
        if payload.get('email') != normalized_email or payload.get('exp', 0) < int(time.time()):
            return False, "Authentication session expired", ""

        return True, "", normalized_email

    except ValueError as e:
        return False, str(e), ""
    except Exception:
        return False, "Authentication failed", ""

def track_metrics(event_type: str, **kwargs):
    """Track metrics to CloudWatch"""
    try:
        metrics = []

        # Basic event metric
        metrics.append({
            'MetricName': f'Total{event_type}',
            'Value': 1,
            'Unit': 'Count'
        })

        # Object type dimension
        if 'object_type' in kwargs:
            metrics.append({
                'MetricName': f'{event_type}ByType',
                'Value': 1,
                'Unit': 'Count',
                'Dimensions': [{
                    'Name': 'ObjectType',
                    'Value': kwargs['object_type']
                }]
            })

        # Security type dimension
        if 'security_type' in kwargs:
            metrics.append({
                'MetricName': f'{event_type}BySecurity',
                'Value': 1,
                'Unit': 'Count',
                'Dimensions': [{
                    'Name': 'SecurityType',
                    'Value': kwargs['security_type']
                }]
            })

        # Size category for object creation
        if event_type == 'ObjectCreated' and 'content_size' in kwargs:
            size_category = calculate_size_category(kwargs['content_size'])
            metrics.append({
                'MetricName': 'ObjectsBySize',
                'Value': 1,
                'Unit': 'Count',
                'Dimensions': [{
                    'Name': 'SizeCategory',
                    'Value': size_category
                }]
            })

            # Track average size
            metrics.append({
                'MetricName': 'ObjectSize',
                'Value': kwargs['content_size'],
                'Unit': 'Bytes'
            })

        # Email type dimension (for EmailSent events)
        if 'email_type' in kwargs:
            metrics.append({
                'MetricName': 'EmailSentByType',
                'Value': 1,
                'Unit': 'Count',
                'Dimensions': [{
                    'Name': 'EmailType',
                    'Value': kwargs['email_type']
                }]
            })

        # Anonymous user analytics
        if 'email' in kwargs:
            anon_user = get_anonymous_user_id(kwargs['email'])
            metrics.append({
                'MetricName': f'{event_type}ByUser',
                'Value': 1,
                'Unit': 'Count',
                'Dimensions': [{
                    'Name': 'AnonymousUser',
                    'Value': anon_user
                }]
            })

        # Send metrics to CloudWatch
        cloudwatch_client.put_metric_data(
            Namespace='Trufo',
            MetricData=metrics
        )

        print(f"Tracked {len(metrics)} metrics for {event_type}")

    except Exception as e:
        print(f"Failed to track metrics: {str(e)}")
        # Don't fail the main operation if metrics fail

def lambda_handler(event, context):
    """Main Lambda handler for Trufo API and web interface"""
    print(f"Event: {json.dumps(event, indent=2)}")

    # Log headers for debugging Cloudflare routing
    headers = event.get('headers', {})
    print(f"Request Headers: {json.dumps(headers, indent=2)}")

    # Get request method and path
    method = event.get('httpMethod', event.get('requestContext', {}).get('http', {}).get('method', 'GET'))
    path = event.get('path', event.get('requestContext', {}).get('http', {}).get('path', '/'))

    # Parse query parameters
    query_params = event.get('queryStringParameters') or {}

    # Parse request body
    body = {}
    if event.get('body'):
        try:
            raw_body = event['body']

            # Try to detect if body is base64 encoded
            if isinstance(raw_body, str) and not raw_body.startswith('{'):
                # Looks like it might be base64, try to decode
                try:
                    import base64
                    decoded_body = base64.b64decode(raw_body).decode('utf-8')
                    body = json.loads(decoded_body)
                    print(f"DEBUG - Decoded base64 body: {body}")
                except Exception:
                    # Not base64, treat as regular JSON
                    body = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
            else:
                # Regular JSON
                body = json.loads(raw_body) if isinstance(raw_body, str) else raw_body

        except (json.JSONDecodeError, Exception) as e:
            print(f"DEBUG - Error parsing body: {e}")
            body = {}

    try:
        # Route requests
        if method == 'OPTIONS':
            return cors_response(200, {'message': 'OK'})

        # PWA routes — serve static bundle from pwa_static/
        if path == '/app' or path == '/app/':
            return _serve_pwa('index.html')
        elif path.startswith('/app/'):
            return _serve_pwa(path[5:])  # strip '/app/' prefix

        # Web interface routes
        if path == '/' or path == '/create':
            return cors_response(200, serve_create_page(), 'text/html')
        elif path.startswith('/access/'):
            token = path.split('/access/')[1]
            return cors_response(200, serve_access_page(token, query_params), 'text/html')
        elif path == '/manage':
            return cors_response(200, serve_manage_page(), 'text/html')

        # API routes
        elif path == '/api/objects' and method == 'POST':
            return create_object(body)
        elif path == '/api/objects' and method == 'GET':
            return get_object(query_params)
        elif path.startswith('/api/access/') and method == 'GET':
            # Direct API access: /api/access/{token}?secret=xxx
            token = path.split('/api/access/')[1]
            query_params['token'] = token
            return get_object(query_params)
        elif path == '/api/list-objects' and method == 'POST':
            return list_user_objects(body)
        elif path == '/api/delete-object' and method == 'POST':
            return delete_user_object(body)
        elif path == '/api/update-object' and method == 'POST':
            return update_object(body)
        elif path == '/api/regenerate-recovery-codes' and method == 'POST':
            return regenerate_recovery_codes(body)
        elif path == '/api/get-object-content' and method == 'POST':
            return get_object_content(body)
        elif path == '/api/user-objects' and method == 'GET':
            return get_user_objects(query_params)
        elif path == '/api/objects' and method == 'DELETE':
            return delete_object(query_params)
        elif path == '/api/toggle' and method == 'POST':
            return toggle_object(body)
        elif path == '/api/validate-email' and method == 'POST':
            return send_email_validation(body)
        elif path == '/api/verify-code' and method == 'POST':
            return verify_email_code(body)
        elif path == '/api/cleanup' and method == 'POST':
            return cleanup_expired_objects(body)
        elif path == '/api/check-auth' and method == 'GET':
            return check_user_auth(event.get('headers', {}), query_params)
        elif path == '/api/list-secrets' and method == 'POST':
            return list_user_secrets(body)
        elif path == '/api/send-magic-link' and method == 'POST':
            return send_magic_link(body)
        elif path == '/api/verify-magic-link' and method == 'POST':
            return verify_magic_link(body)
        elif path.startswith('/api/info/') and method == 'GET':
            token = path.split('/api/info/')[1]
            return get_object_info(token)
        else:
            return cors_response(404, {'error': 'Not found'})

    except Exception as e:
        print(f"Error: {str(e)}")
        return cors_response(500, {'error': 'Internal server error', 'details': str(e)})

def cors_response(status_code: int, data: Dict[str, Any], content_type: str = 'application/json') -> Dict[str, Any]:
    """Helper to create CORS-enabled response"""
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Content-Type': content_type
    }

    if content_type in ('text/html', 'text/plain'):
        body = data if isinstance(data, str) else str(data)
    else:
        body = json.dumps(data)

    return {
        'statusCode': status_code,
        'headers': headers,
        'body': body
    }

def normalize_email(email: str) -> str:
    """Normalize email address to prevent abuse"""
    if not email:
        return email

    email = email.strip().lower()

    # Block emails with + character (alias abuse prevention)
    if '+' in email:
        raise ValueError('Email addresses with + characters are not allowed')

    # Block other potentially abusive characters
    blocked_chars = ['=', '&', '%', '$', '#']
    for char in blocked_chars:
        if char in email:
            raise ValueError(f'Email addresses with {char} characters are not allowed')

    # Split email into local and domain parts
    if '@' not in email:
        raise ValueError('Invalid email format')

    local, domain = email.rsplit('@', 1)

    # Gmail-style dot normalization (remove dots in local part)
    if domain in ['gmail.com', 'googlemail.com']:
        local = local.replace('.', '')

    # Block suspicious patterns
    if len(local) < 1 or len(domain) < 3:
        raise ValueError('Invalid email format')

    # Block disposable email domains
    disposable_domains = {
        '10minutemail.com', 'tempmail.org', 'guerrillamail.com', 'mailinator.com',
        'yopmail.com', 'temp-mail.org', 'throwaway.email', 'maildrop.cc',
        'getnada.com', 'tempmailo.com', '33mail.com', 'fakeinbox.com',
        'temporaryemail.us', 'dispostable.com', '20minutemail.com'
    }

    if domain.lower() in disposable_domains:
        raise ValueError('Disposable email addresses are not allowed')

    return f"{local}@{domain}"

def generate_user_secret(email: str) -> str:
    """Generate consistent user secret from email"""
    # Use normalized email for consistent secret generation
    normalized = normalize_email(email)
    return hashlib.sha256(normalized.encode()).hexdigest()

def generate_owner_session(email: str) -> str:
    """Create a 24-hour HMAC-signed owner session; no server state is retained."""
    if not SESSION_SIGNING_KEY:
        raise RuntimeError('SESSION_SIGNING_KEY is not configured')
    payload = {'email': normalize_email(email), 'exp': int(time.time()) + 86400}
    encoded = base64.urlsafe_b64encode(json.dumps(payload, separators=(',', ':')).encode()).decode().rstrip('=')
    signature = hmac.new(SESSION_SIGNING_KEY.encode(), encoded.encode(), hashlib.sha256).hexdigest()
    return f'{encoded}.{signature}'

def generate_object_secret(token: str, owner_email: str, created_at: int) -> str:
    """Generate a per-object access secret using HMAC-SHA256.
    Inputs: token (random, per-object) + owner email + creation timestamp.
    The server key ensures it cannot be forged without server-side knowledge.
    """
    message = f"{token}:{normalize_email(owner_email)}:{created_at}".encode()
    return hmac.new(ENCRYPTION_KEY.encode(), message, hashlib.sha256).hexdigest()

def get_base_url() -> str:
    """Get base URL for the application"""
    # For deployed version, we'll use the known domain
    return "https://trufo.maimons.dev"

def encrypt_content(content: Any) -> str:
    """Encrypt content for storage"""
    # Simple base64 encoding for now - implement proper encryption in production
    content_str = json.dumps(content)
    return base64.b64encode(content_str.encode()).decode()

def decrypt_content(encrypted_content: str) -> Any:
    """Decrypt content from storage"""
    try:
        content_str = base64.b64decode(encrypted_content.encode()).decode()
        return json.loads(content_str)
    except:
        return encrypted_content

def generate_s3_key(user_email: str, object_type: str, object_name: str) -> str:
    """Generate S3 key for object storage"""
    normalized_email = normalize_email(user_email)
    user_hash = hashlib.md5(normalized_email.encode()).hexdigest()
    return f"users/{user_hash}/{object_type}/{object_name}.json"

def generate_totp_secret() -> str:
    """Generate TOTP secret"""
    return base64.b32encode(secrets.token_bytes(20)).decode()

def generate_recovery_codes(count: int = 8) -> List[str]:
    """Generate backup recovery codes"""
    codes = []
    for _ in range(count):
        # Generate 8-character alphanumeric codes
        code = ''.join(secrets.choice('ABCDEFGHIJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
        # Format as XXXX-XXXX
        formatted_code = f"{code[:4]}-{code[4:]}"
        codes.append(formatted_code)
    return codes

def verify_recovery_code(stored_codes: List[str], provided_code: str) -> bool:
    """Verify and consume a recovery code"""
    formatted_code = provided_code.upper().replace(' ', '').replace('-', '')
    if len(formatted_code) == 8:
        formatted_code = f"{formatted_code[:4]}-{formatted_code[4:]}"

    if formatted_code in stored_codes:
        stored_codes.remove(formatted_code)  # One-time use
        return True
    return False

def verify_totp_token(secret: str, token: str) -> bool:
    """Verify TOTP token"""
    if not secret or not token:
        return False

    # Simple time-based validation (30-second windows)
    current_time = int(time.time() // 30)

    for i in range(-1, 2):  # Check current and ±1 window
        time_window = current_time + i
        expected_token = generate_totp_for_time(secret, time_window)
        if expected_token == token:
            return True

    return False

def generate_totp_for_time(secret: str, time_window: int) -> str:
    """Generate TOTP token for specific time window"""
    key = base64.b32decode(secret)
    time_bytes = time_window.to_bytes(8, byteorder='big')
    hash_value = hmac.new(key, time_bytes, hashlib.sha1).digest()

    offset = hash_value[-1] & 0x0f
    code = ((hash_value[offset] & 0x7f) << 24 |
            (hash_value[offset + 1] & 0xff) << 16 |
            (hash_value[offset + 2] & 0xff) << 8 |
            (hash_value[offset + 3] & 0xff)) % 1000000

    return str(code).zfill(6)

# Email validation system
email_codes = {}  # In production, use DynamoDB or Redis
magic_links = {}  # Store magic link tokens

def analyze_bot_behavior(behavioral_data: Dict[str, Any]) -> bool:
    """Analyze behavioral data to detect bot-like patterns"""
    if not behavioral_data:
        return False  # No data to analyze, assume human

    bot_score = 0

    # 1. Mouse movement analysis (more lenient for humans)
    mouse_moves = behavioral_data.get('mouse_moves', [])
    if len(mouse_moves) == 0:
        bot_score += 50  # Absolutely no mouse movement is very suspicious
    elif len(mouse_moves) < 2:
        bot_score += 15  # Very few movements, but might be mobile/focused user
    elif len(mouse_moves) > 150:
        bot_score += 30  # Extremely many movements
    else:
        # Check for linear/perfect movements (bot-like)
        linear_moves = 0
        for i in range(1, len(mouse_moves)):
            prev = mouse_moves[i-1]
            curr = mouse_moves[i]
            if abs(prev.get('x', 0) - curr.get('x', 0)) + abs(prev.get('y', 0) - curr.get('y', 0)) == 0:
                linear_moves += 1
        if linear_moves > len(mouse_moves) * 0.9:  # 90% same position (was 80%)
            bot_score += 40

    # 2. Typing rhythm analysis
    keystrokes = behavioral_data.get('keystrokes', [])
    if len(keystrokes) > 2:
        intervals = []
        for i in range(1, len(keystrokes)):
            interval = keystrokes[i].get('timestamp', 0) - keystrokes[i-1].get('timestamp', 0)
            intervals.append(interval)

        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            # Check for too consistent typing (robotic)
            if avg_interval < 50:  # Faster than human possible
                bot_score += 50
            elif 80 <= avg_interval <= 120:  # Too consistent
                variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
                if variance < 10:  # Very low variance = robotic
                    bot_score += 30

    # 3. Timing analysis
    page_load_time = behavioral_data.get('page_load_time', 0)
    form_fill_time = behavioral_data.get('form_fill_time', 0)

    if form_fill_time < 1000:  # Filled form in less than 1 second
        bot_score += 40
    elif form_fill_time < 3000:  # Filled form very quickly
        bot_score += 20

    # 4. Interaction patterns
    click_events = behavioral_data.get('click_events', [])
    if len(click_events) == 1:  # Only clicked submit, no other interactions
        bot_score += 25

    # 5. Focus events
    focus_events = behavioral_data.get('focus_events', [])
    if len(focus_events) < 2:  # Didn't focus on multiple fields
        bot_score += 15

    # 6. Perfect targeting (clicking exactly on center of buttons)
    perfect_clicks = 0
    for click in click_events:
        target = click.get('target', {})
        if target.get('perfect_center', False):
            perfect_clicks += 1
    if perfect_clicks > len(click_events) * 0.7:  # 70% perfect clicks
        bot_score += 30

    print(f"Behavioral analysis score: {bot_score} (threshold: 70)")
    return bot_score >= 70  # Threshold for bot detection

def check_user_has_active_secrets(email: str) -> bool:
    """Check if user has any active (non-expired) secrets"""
    try:
        current_time = int(time.time() * 1000)

        # List all objects for this user
        user_prefix = generate_s3_key(email, "", "").split('/')[0] + '/' + generate_s3_key(email, "", "").split('/')[1] + '/'
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=user_prefix)

        if 'Contents' not in response:
            return False

        # Check if any objects are still active (not expired)
        for obj in response['Contents']:
            try:
                obj_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=obj['Key'])
                obj_data = json.loads(obj_response['Body'].read())

                # If object hasn't expired, user has active secrets
                if obj_data.get('ttl', 0) > current_time:
                    print(f"Found active secret for {email}: {obj_data.get('name', 'unknown')}")
                    return True

            except Exception as e:
                print(f"Error checking object {obj['Key']}: {str(e)}")
                continue

        return False

    except Exception as e:
        print(f"Error checking active secrets for {email}: {str(e)}")
        return False  # If we can't check, don't block the user

def send_email_validation(body: Dict[str, Any]) -> Dict[str, Any]:
    """Send email validation code with behavioral analysis"""
    print(f"DEBUG - Email validation body: {json.dumps(body)}")
    email = body.get('email')
    behavioral_data = body.get('behavioral_data', {})

    print(f"DEBUG - Extracted email: {email}")
    if not email:
        print(f"DEBUG - Email validation failed, body was: {body}")
        return cors_response(400, {'error': 'Email is required'})

    # Normalize and validate email
    try:
        normalized_email = normalize_email(email)
        print(f"DEBUG - Normalized email: {normalized_email}")
    except ValueError as e:
        print(f"DEBUG - Email validation failed: {str(e)}")
        return cors_response(400, {'error': str(e)})

    # Check if user has active secrets - skip behavioral analysis for existing users
    has_active_secrets = check_user_has_active_secrets(email)

    if not has_active_secrets:
        # Only check behavioral data for new/inactive users
        is_bot_like = analyze_bot_behavior(behavioral_data)

        if is_bot_like:
            print(f"Bot-like behavior detected for {email}: {behavioral_data}")
            return cors_response(429, {'error': 'Rate limited. Please try again later.'})
    else:
        print(f"Existing user with active secrets, skipping behavioral analysis: {email}")

    # Generate 6-digit code
    code = str(secrets.randbelow(900000) + 100000)

    # Create email hash for storage using normalized email
    email_hash = hashlib.md5(normalized_email.encode()).hexdigest()

    # Store code with expiration (5 minutes) and track last sent time
    put_auth_record('otp', email_hash, {
        'email': normalized_email,
        'code': code,
        'expires': time.time() + 300,
        'last_sent': time.time()
    })

    # Send email
    try:
        send_email(email, 'Your Trufo sign-in code', f'Your verification code is: {code}')

        return cors_response(200, {'message': 'Verification code sent'})
    except Exception as e:
        return cors_response(500, {'error': 'Failed to send email', 'details': str(e)})

def verify_email_code(body: Dict[str, Any]) -> Dict[str, Any]:
    """Verify email validation code"""
    email = body.get('email')
    code = body.get('code')

    if not email or not code:
        return cors_response(400, {'error': 'Email and code are required'})

    # Normalize email first
    try:
        normalized_email = normalize_email(email)
    except ValueError as e:
        return cors_response(400, {'error': str(e)})

    email_hash = hashlib.md5(normalized_email.encode()).hexdigest()
    stored_data = get_auth_record('otp', email_hash)
    if not stored_data:
        return cors_response(400, {'error': 'No code found for this email'})

    if time.time() > stored_data['expires']:
        delete_auth_record('otp', email_hash)
        return cors_response(400, {'error': 'Code expired'})

    if stored_data['code'] != code:
        return cors_response(400, {'error': 'Invalid code'})

    # Code verified, remove from storage
    delete_auth_record('otp', email_hash)

    return cors_response(200, {
        'verified': True,
        'email': normalized_email,
        'session': generate_owner_session(normalized_email)
    })

def send_magic_link(body: Dict[str, Any]) -> Dict[str, Any]:
    """Send magic link for instant authentication"""
    email = body.get('email')
    return_url = body.get('returnUrl', 'https://trufo.maimons.dev')

    if not email:
        return cors_response(400, {'error': 'Email is required'})

    # Normalize email first
    try:
        normalized_email = normalize_email(email)
    except ValueError as e:
        return cors_response(400, {'error': str(e)})

    # Generate magic link token
    magic_token = secrets.token_urlsafe(32)

    # Store magic link token with expiration (10 minutes)
    put_auth_record('magic', magic_token, {
        'email': normalized_email,
        'expires': time.time() + 600  # 10 minutes
    })

    # Generate magic link URL
    magic_url = f"{return_url}?auth={magic_token}"

    # Send email
    try:
        subject = "Your Trufo sign-in link"
        body_text = f"""
🔒 Trufo Magic Link Authentication

Click the link below to instantly access your Trufo account:

{magic_url}

This link will expire in 10 minutes for security.

If you didn't request this, you can safely ignore this email.
        """

        body_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #667eea;">Your Trufo sign-in link</h2>
            <p>Tap the button below to instantly access your Trufo account. You'll be brought straight back into the app.</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{magic_url}" target="_self"
                   style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                          color: white; text-decoration: none; padding: 15px 30px;
                          border-radius: 8px; display: inline-block; font-weight: bold;">
                    🚀 Open Trufo
                </a>
            </div>
            <p><small>This link will expire in 10 minutes for security.</small></p>
            <p><small>If you didn't request this, you can safely ignore this email.</small></p>
        </div>
        """

        ses_client.send_email(
            Source=f"Trufo <{FROM_EMAIL}>",
            Destination={'ToAddresses': [email]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Text': {'Data': body_text, 'Charset': 'UTF-8'},
                    'Html': {'Data': body_html, 'Charset': 'UTF-8'}
                }
            }
        )

        return cors_response(200, {'success': True, 'message': 'Magic link sent'})

    except Exception as e:
        print(f"Error sending magic link email: {str(e)}")
        return cors_response(500, {'error': 'Failed to send magic link'})

def verify_magic_link(body: Dict[str, Any]) -> Dict[str, Any]:
    """Verify magic link token and authenticate user"""
    token = body.get('token')

    if not token:
        return cors_response(400, {'error': 'Token is required'})

    # Check if token exists and is valid
    magic_data = get_auth_record('magic', token)
    if not magic_data:
        return cors_response(400, {'error': 'Invalid or expired magic link'})

    # Check if token is expired
    if time.time() > magic_data['expires']:
        delete_auth_record('magic', token)
        return cors_response(400, {'error': 'Magic link has expired'})

    # Token is valid, authenticate user
    email = magic_data['email']
    # Clean up used token
    delete_auth_record('magic', token)

    return cors_response(200, {
        'success': True,
        'email': email,
        'session': generate_owner_session(email)
    })

def check_user_auth(headers: Dict[str, Any], query_params: Dict[str, Any]) -> Dict[str, Any]:
    """Check if user is already authenticated via cookie"""
    email = query_params.get('email')
    if not email:
        return cors_response(400, {'error': 'Email parameter required'})

    # Check cookie
    cookie_header = headers.get('Cookie', headers.get('cookie', ''))
    if cookie_header:
        # Parse cookies
        cookies = {}
        for cookie in cookie_header.split(';'):
            if '=' in cookie:
                name, value = cookie.strip().split('=', 1)
                cookies[name] = value

        trufo_verified = cookies.get('trufo_verified')
        if trufo_verified:
            # Verify cookie matches user
            expected_cookie = generate_user_secret(email)[:16]
            if trufo_verified == expected_cookie:
                # Check if user still has active secrets
                if check_user_has_active_secrets(email):
                    return cors_response(200, {
                        'authenticated': True,
                        'userSecret': generate_user_secret(email)
                    })

    return cors_response(200, {'authenticated': False})

def list_user_secrets(body: Dict[str, Any]) -> Dict[str, Any]:
    """List all secrets for authenticated user"""
    try:
        is_valid, error_msg, email = verify_user_auth(body)
        if not is_valid:
            return cors_response(401, {'error': error_msg})

        # Get user hash for searching (use MD5 to match storage structure)
        normalized_email = normalize_email(email)
        user_hash = hashlib.md5(normalized_email.encode()).hexdigest()

        # List all objects for this user (use correct prefix structure)
        response = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix=f'users/{user_hash}/',
            MaxKeys=1000
        )

        current_time = int(time.time() * 1000)
        secrets = []

        if 'Contents' in response:
            for obj in response['Contents']:
                try:
                    # Get object data
                    obj_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=obj['Key'])
                    obj_data = json.loads(obj_response['Body'].read())

                    # Objects are already filtered by S3 prefix, so all belong to this user

                    # Get basic info (decrypt content for preview)
                    encrypted_content = obj_data.get('content', '')
                    try:
                        decrypted_content = decrypt_content(encrypted_content)
                        preview = decrypted_content[:100] + '...' if len(decrypted_content) > 100 else decrypted_content
                    except:
                        preview = '[Content preview unavailable]'

                    # Compute per-object access secret
                    obj_token = obj_data.get('token')
                    obj_created = obj_data.get('createdAt', 0)
                    obj_access_secret = generate_object_secret(
                        obj_token,
                        obj_data.get('ownerEmail', ''),
                        obj_created
                    )

                    # Create secret info
                    secret_info = {
                        'token': obj_token,
                        'name': obj_data.get('name', ''),
                        'access_secret': obj_access_secret,
                        'type': obj_data.get('type', 'string'),
                        'security': obj_data.get('securityType', 'none'),
                        'ttl': obj_data.get('ttl'),
                        'preview': preview,
                        'created': obj_created,
                        'one_time': obj_data.get('oneTimeAccess', False),
                        'access_count': obj_data.get('hitCount', 0),
                        'access_url': f"{get_base_url()}/access/{obj_token}?secret={obj_access_secret}",
                        's3_key': obj['Key'],
                        'totp_secret': obj_data.get('totpSecret') if obj_data.get('securityType') == 'totp' else None,
                    }

                    secrets.append(secret_info)

                except Exception as e:
                    print(f"Error reading object {obj['Key']}: {e}")
                    continue

        # Sort by creation time (newest first)
        secrets.sort(key=lambda x: x.get('created', 0), reverse=True)

        return cors_response(200, {
            'success': True,
            'secrets': secrets,
            'total': len(secrets)
        })

    except Exception as e:
        print(f"Error listing user secrets: {str(e)}")
        return cors_response(500, {'error': 'Internal server error'})

def count_user_objects(email: str) -> int:
    """Count active objects for a user"""
    try:
        normalized_email = normalize_email(email)
        user_hash = hashlib.md5(normalized_email.encode()).hexdigest()
        current_time = int(time.time() * 1000)

        # List all objects for this user
        response = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix=f'users/{user_hash}/'
        )

        count = 0
        if 'Contents' in response:
            for obj in response['Contents']:
                try:
                    # Skip directories
                    if obj['Key'].endswith('/'):
                        continue

                    obj_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=obj['Key'])
                    obj_data = json.loads(obj_response['Body'].read())

                    # Only count non-expired objects
                    if obj_data.get('ttl', 0) > current_time:
                        count += 1
                except Exception as e:
                    print(f"Error checking object {obj['Key']}: {e}")
                    continue

        return count
    except Exception as e:
        print(f"Error counting user objects: {e}")
        return 0

# S3 Storage Operations
def create_object(body: Dict[str, Any]) -> Dict[str, Any]:
    """Create new object in S3"""
    print(f"DEBUG - create_object body: {json.dumps(body, indent=2)}")

    is_valid, error_msg, normalized_email = verify_user_auth(body)
    if not is_valid:
        return cors_response(401, {'error': error_msg})

    # All security types require email authentication to CREATE
    # "None" just means no verification needed to ACCESS later
    required_fields = ['name', 'type', 'content', 'ttlHours', 'ownerEmail']

    for field in required_fields:
        if field not in body:
            print(f"DEBUG - Missing field: {field}, body keys: {list(body.keys())}")
            return cors_response(400, {'error': f'Missing required field: {field}'})

    # Validate content size (1MB limit)
    content = body.get('content', '')
    if len(str(content).encode('utf-8')) > 1024 * 1024:  # 1MB
        return cors_response(400, {'error': 'Content too large. Maximum size is 1MB.'})

    # Check user object count limit (30 per email)
    try:
        user_objects_count = count_user_objects(body['ownerEmail'])
        if user_objects_count >= 30:
            return cors_response(400, {'error': 'Maximum 30 objects per email address. Please delete some existing objects first.'})
    except Exception as e:
        print(f"Error checking user object count: {e}")
        # Continue without blocking if we can't check

    # Validate TTL
    try:
        ttl_hours = float(body['ttlHours'])
        if ttl_hours <= 0 or ttl_hours > 24 * 365:  # Max 365 days
            return cors_response(400, {'error': 'TTL must be between 0.1 and 8760 hours (365 days)'})
    except (ValueError, TypeError):
        return cors_response(400, {'error': 'Invalid TTL value'})

    # Generate object metadata
    object_id = f"obj_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    token = secrets.token_hex(16)
    ttl = int(time.time() + (ttl_hours * 3600)) * 1000  # Convert to milliseconds

    # Get security type and generate appropriate security data
    security_type = body.get('securityType', 'basic')
    totp_secret = None
    recovery_codes = None

    if security_type == 'totp':
        totp_secret = generate_totp_secret()
        recovery_codes = generate_recovery_codes()

    # Prepare object data
    object_data = {
        'id': object_id,
        'name': body['name'],
        'type': body['type'],
        'securityType': security_type,
        'content': encrypt_content(body['content']),
        'ttl': ttl,
        'token': token,
        'ownerEmail': normalized_email,
        'ownerName': body.get('ownerName', 'Anonymous'),
        'hitCount': 0,
        'createdAt': int(time.time() * 1000),
        'lastHit': None,
        'oneTimeAccess': body.get('oneTimeAccess', False),
        'totpSecret': totp_secret,
        'recoveryCodes': recovery_codes
    }

    # Store in S3
    try:
        # Use pathType (type-security combination) for S3 path organization
        path_type = body.get('pathType', body['type'])
        # Object names are display metadata, not storage paths: this avoids
        # duplicate-name overwrites and path-like names creating odd prefixes.
        user_hash = hashlib.md5(normalized_email.encode()).hexdigest()
        s3_key = f"users/{user_hash}/{path_type}/{object_id}.json"
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=json.dumps(object_data),
            ContentType='application/json'
        )

        # Also store by token for easy lookup
        token_key = f"tokens/{token}.json"
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=token_key,
            Body=json.dumps({'s3_key': s3_key}),
            ContentType='application/json'
        )

        access_secret = generate_object_secret(token, normalized_email, object_data['createdAt'])

        # Prepare response with security info (shown only once)
        response_data = {
            'success': True,
            'object': {
                'token': token,
                'accessSecret': access_secret,
                'name': body['name'],
                'type': body['type'],
                'securityType': security_type,
                'oneTimeAccess': body.get('oneTimeAccess', False),
                'hitCount': 0,
                'createdAt': object_data['createdAt'],
                'ttl': ttl
            },
            'session': body['session']
        }

        # Include security data only on creation (show once)
        if security_type == 'totp' and totp_secret and recovery_codes:
            qr_url = f"otpauth://totp/Trufo:{body['name']}?secret={totp_secret}&issuer=Trufo"
            response_data['security'] = {
                'totpSecret': totp_secret,
                'totpQR': qr_url,
                'recoveryCodes': recovery_codes
            }

        # Track metrics for object creation
        content_size = len(str(body.get('content', '')).encode('utf-8'))
        track_metrics('ObjectCreated',
                     email=body['ownerEmail'],
                     object_type=body['type'],
                     security_type=security_type,
                     content_size=content_size)

        return cors_response(201, response_data)

    except Exception as e:
        return cors_response(500, {'error': 'Failed to create object', 'details': str(e)})

def get_object_info(token: str) -> Dict[str, Any]:
    """Return object metadata (oneTimeAccess, type) without consuming the secret"""
    try:
        token_key = f"tokens/{token}.json"
        token_obj = s3_client.get_object(Bucket=BUCKET_NAME, Key=token_key)
        token_data = json.loads(token_obj['Body'].read())

        object_obj = s3_client.get_object(Bucket=BUCKET_NAME, Key=token_data['s3_key'])
        object_data = json.loads(object_obj['Body'].read())

        return cors_response(200, {
            'oneTimeAccess': object_data.get('oneTimeAccess', False),
            'type': object_data.get('type'),
            'securityType': object_data.get('securityType', 'none')
        })
    except s3_client.exceptions.NoSuchKey:
        return cors_response(404, {'error': 'Object not found or invalid token'})
    except Exception as e:
        return cors_response(500, {'error': 'Failed to retrieve object info', 'details': str(e)})


def get_object(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """Get object by token"""
    name = query_params.get('name')  # Optional for backwards compatibility
    token = query_params.get('token')
    secret = query_params.get('secret')
    totp_code = query_params.get('totpCode')

    if not all([token, secret]):
        return cors_response(400, {'error': 'Token and secret are required'})

    try:
        # Get object by token first
        token_key = f"tokens/{token}.json"
        token_obj = s3_client.get_object(Bucket=BUCKET_NAME, Key=token_key)
        token_data = json.loads(token_obj['Body'].read())

        # Get actual object
        object_obj = s3_client.get_object(Bucket=BUCKET_NAME, Key=token_data['s3_key'])
        object_data = json.loads(object_obj['Body'].read())

        # Verify name matches (if provided for backwards compatibility)
        if name and object_data['name'] != name:
            return cors_response(404, {'error': 'Object not found or invalid token'})

        # Every shared link requires its per-object secret. "none" means no
        # second factor, never that the URL token alone is sufficient.
        security_type = object_data.get('securityType', 'basic')
        expected_secret = generate_object_secret(
            token,
            object_data['ownerEmail'],
            object_data.get('createdAt', 0)
        )
        if not hmac.compare_digest(secret, expected_secret):
            return cors_response(403, {'error': 'Invalid secret for this object'})

        # Check expiration
        if object_data['ttl'] <= int(time.time() * 1000):
            # Delete expired object
            s3_client.delete_object(Bucket=BUCKET_NAME, Key=token_data['s3_key'])
            s3_client.delete_object(Bucket=BUCKET_NAME, Key=token_key)
            return cors_response(410, {'error': 'Object has expired and has been deleted'})

        # Handle different security types
        if security_type == 'none':
            # No additional security for "none" type
            pass

        elif security_type == 'basic':
            # Send notification email for notice-type objects
            try:
                if object_data['ownerEmail'] != 'anonymous@trufo.local':
                    send_email(object_data['ownerEmail'], 'Trufo Access Alert',
                              f'Your secret "{object_data["name"]}" was accessed at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} UTC')
            except Exception as e:
                print(f"Failed to send notification email: {e}")

        elif security_type == 'totp':
            # Handle TOTP and recovery codes
            if not totp_code:
                return cors_response(403, {
                    'error': 'TOTP verification required',
                    'requiresTOTP': True,
                    'message': 'Enter your TOTP code from authenticator app or use a backup code'
                })

            # Check if it's a recovery code first
            recovery_codes = object_data.get('recoveryCodes', [])
            if verify_recovery_code(recovery_codes, totp_code):
                # Update object with remaining codes
                object_data['recoveryCodes'] = recovery_codes
                print(f"Recovery code used. Remaining codes: {len(recovery_codes)}")
            elif not verify_totp_token(object_data['totpSecret'], totp_code):
                return cors_response(403, {'error': 'Invalid TOTP code or backup code'})

        # Update hit count
        object_data['hitCount'] += 1
        object_data['lastHit'] = int(time.time() * 1000)

        # Handle different object types
        decrypted_content = decrypt_content(object_data['content'])
        response_content = decrypted_content

        if object_data['type'] == 'toggle':
            response_content = decrypted_content
            # Toggle for next access (if not one-time)
            if not object_data.get('oneTimeAccess', False):
                toggled_content = not decrypted_content
                object_data['content'] = encrypt_content(toggled_content)

        # Save updated object (if not one-time access)
        if not object_data.get('oneTimeAccess', False):
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=token_data['s3_key'],
                Body=json.dumps(object_data),
                ContentType='application/json'
            )
        else:
            # Delete one-time access object
            s3_client.delete_object(Bucket=BUCKET_NAME, Key=token_data['s3_key'])
            s3_client.delete_object(Bucket=BUCKET_NAME, Key=token_key)

        # Track metrics for object access
        track_metrics('ObjectAccessed',
                     email=object_data.get('ownerEmail'),
                     object_type=object_data.get('type'),
                     security_type=object_data.get('securityType', 'none'))

        if query_params.get('raw') == 'true':
            return cors_response(200, str(response_content), content_type='text/plain')

        response_body = {
            'content': response_content,
            'hits': object_data['hitCount'],
            'oneTimeAccess': object_data.get('oneTimeAccess', False)
        }
        if object_data.get('oneTimeAccess', False):
            response_body['warning'] = 'This secret has been permanently deleted. It will never be shown again.'

        return cors_response(200, response_body)

    except s3_client.exceptions.NoSuchKey:
        return cors_response(404, {'error': 'Object not found or invalid token'})
    except Exception as e:
        return cors_response(500, {'error': 'Failed to retrieve object', 'details': str(e)})

def get_user_objects(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """Get all objects for a user"""
    email = query_params.get('email')
    if not email:
        return cors_response(400, {'error': 'Email is required'})

    try:
        normalized_email = normalize_email(email)
        user_hash = hashlib.md5(normalized_email.encode()).hexdigest()
        prefix = f"users/{user_hash}/"

        # List all objects for user
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
        objects = []

        if 'Contents' in response:
            for obj in response['Contents']:
                try:
                    obj_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=obj['Key'])
                    obj_data = json.loads(obj_response['Body'].read())
                    objects.append(obj_data)
                except:
                    continue

        return cors_response(200, {'objects': objects})

    except Exception as e:
        return cors_response(500, {'error': 'Failed to get user objects', 'details': str(e)})

def delete_object(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """Delete object by ID"""
    object_id = query_params.get('id')
    if not object_id:
        return cors_response(400, {'error': 'Object ID is required'})

    try:
        # Find object by ID (scan approach - not ideal but works for now)
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix='users/')

        if 'Contents' in response:
            for obj in response['Contents']:
                try:
                    obj_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=obj['Key'])
                    obj_data = json.loads(obj_response['Body'].read())

                    if obj_data.get('id') == object_id:
                        # Delete object and token
                        s3_client.delete_object(Bucket=BUCKET_NAME, Key=obj['Key'])
                        token_key = f"tokens/{obj_data['token']}.json"
                        try:
                            s3_client.delete_object(Bucket=BUCKET_NAME, Key=token_key)
                        except:
                            pass

                        return cors_response(200, {'success': True})
                except:
                    continue

        return cors_response(404, {'error': 'Object not found'})

    except Exception as e:
        return cors_response(500, {'error': 'Failed to delete object', 'details': str(e)})

def toggle_object(body: Dict[str, Any]) -> Dict[str, Any]:
    """Toggle boolean object"""
    name = body.get('name')
    token = body.get('token')

    if not name or not token:
        return cors_response(400, {'error': 'Name and token are required'})

    try:
        # Get object by token
        token_key = f"tokens/{token}.json"
        token_obj = s3_client.get_object(Bucket=BUCKET_NAME, Key=token_key)
        token_data = json.loads(token_obj['Body'].read())

        object_obj = s3_client.get_object(Bucket=BUCKET_NAME, Key=token_data['s3_key'])
        object_data = json.loads(object_obj['Body'].read())

        # Verify name and type
        if object_data['name'] != name:
            return cors_response(404, {'error': 'Object not found or invalid token'})

        if object_data['type'] != 'boolean':
            return cors_response(400, {'error': 'Toggle only supported for boolean objects'})

        # Check expiration
        if object_data['ttl'] <= int(time.time() * 1000):
            s3_client.delete_object(Bucket=BUCKET_NAME, Key=token_data['s3_key'])
            s3_client.delete_object(Bucket=BUCKET_NAME, Key=token_key)
            return cors_response(410, {'error': 'Object has expired and has been deleted'})

        # Toggle content
        current_content = decrypt_content(object_data['content'])
        toggled_content = not current_content

        # Update object
        object_data['content'] = encrypt_content(toggled_content)
        object_data['hitCount'] += 1
        object_data['lastHit'] = int(time.time() * 1000)

        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=token_data['s3_key'],
            Body=json.dumps(object_data),
            ContentType='application/json'
        )

        # Track metrics for toggle access
        track_metrics('ObjectToggled',
                     email=object_data.get('ownerEmail'),
                     object_type=object_data.get('type'),
                     security_type=object_data.get('securityType', 'none'))

        return cors_response(200, {
            'content': toggled_content,
            'hits': object_data['hitCount']
        })

    except s3_client.exceptions.NoSuchKey:
        return cors_response(404, {'error': 'Object not found or invalid token'})
    except Exception as e:
        return cors_response(500, {'error': 'Failed to toggle object', 'details': str(e)})

def send_email(to_email: str, subject: str, body: str):
    """Send email using Amazon SES with anti-spam headers"""
    try:
        is_access_alert = 'Access Alert' in subject
        if is_access_alert:
            html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f8f9fa; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #333; margin-bottom: 20px;">🔔 Trufo Access Alert</h2>
                <p style="color: #555; font-size: 16px; line-height: 1.5;">{body}</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #888; font-size: 12px; text-align: center;">
                    This email was sent by Trufo - Secure Secret Sharing<br>
                    <a href="https://trufo.maimons.dev" style="color: #667eea;">trufo.maimons.dev</a>
                </p>
            </div>
        </body>
        </html>
        """
        else:
            html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f8f9fa; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #333; margin-bottom: 20px;">🔒 Trufo Verification Code</h2>
                <p style="color: #555; font-size: 16px; line-height: 1.5;">Your verification code is:</p>
                <div style="background: #667eea; color: white; font-size: 24px; font-weight: bold; text-align: center; padding: 15px; border-radius: 6px; margin: 20px 0; letter-spacing: 3px;">
                    {body.split(': ')[1] if ': ' in body else body}
                </div>
                <p style="color: #666; font-size: 14px; margin-top: 20px;">
                    This code will expire in 5 minutes. If you didn't request this, please ignore this email.
                </p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #888; font-size: 12px; text-align: center;">
                    This email was sent by Trufo - Secure Secret Sharing<br>
                    <a href="https://trufo.maimons.dev" style="color: #667eea;">trufo.maimons.dev</a>
                </p>
            </div>
        </body>
        </html>
        """

        # Use configuration set if available for better deliverability
        email_params = {
            'Source': f"Trufo <{FROM_EMAIL}>",
            'Destination': {'ToAddresses': [to_email]},
            'Message': {
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': body,
                        'Charset': 'UTF-8'
                    },
                    'Html': {
                        'Data': html_body,
                        'Charset': 'UTF-8'
                    }
                }
            },
            'Tags': [
                {
                    'Name': 'EmailType',
                    'Value': 'VerificationCode'
                },
                {
                    'Name': 'Application',
                    'Value': 'Trufo'
                }
            ]
        }

        # Add configuration set if configured (for reputation tracking)
        config_set_name = os.environ.get('SES_CONFIGURATION_SET')
        if config_set_name:
            email_params['ConfigurationSetName'] = config_set_name

        response = ses_client.send_email(**email_params)
        print(f"Email sent successfully. MessageId: {response['MessageId']}")

        # Track email send as custom metric
        if 'Access Alert' in subject:
            email_type = 'access_alert'
        elif 'Magic Link' in subject:
            email_type = 'magic_link'
        else:
            email_type = 'verification'
        track_metrics('EmailSent', email_type=email_type)

    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        raise e

def cleanup_expired_objects(body: Dict[str, Any]) -> Dict[str, Any]:
    """Clean up expired objects from S3"""
    # Simple authentication check for cleanup endpoint
    cleanup_key = body.get('cleanup_key')
    expected_key = f"{ENCRYPTION_KEY}cleanup"

    if cleanup_key != expected_key:
        return cors_response(403, {'error': 'Invalid cleanup key'})

    try:
        current_time = int(time.time() * 1000)
        deleted_count = 0

        # List all user objects
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix='users/')

        if 'Contents' in response:
            for obj in response['Contents']:
                try:
                    obj_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=obj['Key'])
                    obj_data = json.loads(obj_response['Body'].read())

                    # Check if object is expired
                    if obj_data.get('ttl', 0) <= current_time:
                        # Delete object and its token
                        s3_client.delete_object(Bucket=BUCKET_NAME, Key=obj['Key'])

                        token_key = f"tokens/{obj_data['token']}.json"
                        try:
                            s3_client.delete_object(Bucket=BUCKET_NAME, Key=token_key)
                        except:
                            pass

                        deleted_count += 1
                        print(f"Deleted expired object: {obj_data.get('name', 'unknown')}")

                except Exception as e:
                    print(f"Error processing object {obj['Key']}: {str(e)}")
                    continue

        return cors_response(200, {
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Cleaned up {deleted_count} expired objects'
        })

    except Exception as e:
        return cors_response(500, {'error': 'Cleanup failed', 'details': str(e)})

def list_user_objects(body: Dict[str, Any]) -> Dict[str, Any]:
    """List all objects for authenticated user - STRICT AUTH REQUIRED"""
    # Strict authentication check
    is_valid, error_msg, normalized_email = verify_user_auth(body)
    if not is_valid:
        track_metrics('UnauthorizedListAttempt', email=body.get('email', 'unknown'))
        return cors_response(401, {'error': error_msg})

    try:
        normalized_email = normalize_email(normalized_email)
        user_hash = hashlib.md5(normalized_email.encode()).hexdigest()
        prefix = f"users/{user_hash}/"

        current_time = int(time.time() * 1000)
        objects = []

        # List all user objects from S3
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)

        if 'Contents' in response:
            for obj in response['Contents']:
                try:
                    # Skip directories and tokens
                    if obj['Key'].endswith('/') or 'tokens/' in obj['Key']:
                        continue

                    obj_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=obj['Key'])
                    obj_data = json.loads(obj_response['Body'].read())

                    # Only include non-expired objects
                    if obj_data.get('ttl', 0) > current_time:
                        obj_token = obj_data.get('token')
                        obj_created = obj_data.get('createdAt', 0)
                        obj_access_secret = generate_object_secret(
                            obj_token,
                            normalized_email,
                            obj_created
                        )
                        objects.append({
                            'id': obj_data.get('id'),
                            'name': obj_data.get('name'),
                            'type': obj_data.get('type'),
                            'securityType': obj_data.get('securityType', 'none'),
                            'createdAt': obj_created,
                            'ttl': obj_data.get('ttl'),
                            'hitCount': obj_data.get('hitCount', 0),
                            'oneTimeAccess': obj_data.get('oneTimeAccess', False),
                            's3Key': obj['Key'],
                            'token': obj_token,
                            'accessSecret': obj_access_secret
                        })
                except Exception as e:
                    print(f"Error reading object {obj['Key']}: {e}")
                    continue

        # Track successful list operation
        track_metrics('ObjectsListed',
                     email=normalized_email,
                     object_count=len(objects))

        return cors_response(200, {
            'success': True,
            'objects': objects,
            'total': len(objects)
        })

    except Exception as e:
        print(f"Error listing user objects: {e}")
        return cors_response(500, {'error': 'Failed to list objects', 'details': str(e)})

def delete_user_object(body: Dict[str, Any]) -> Dict[str, Any]:
    """Delete specific object for authenticated user - STRICT AUTH REQUIRED"""
    # Strict authentication check
    is_valid, error_msg, normalized_email = verify_user_auth(body)
    if not is_valid:
        track_metrics('UnauthorizedDeleteAttempt', email=body.get('email', 'unknown'))
        return cors_response(401, {'error': error_msg})

    object_id = body.get('objectId')
    s3_key = body.get('s3Key')

    if not object_id or not s3_key:
        return cors_response(400, {'error': 'Object ID and S3 key are required'})

    try:
        # Verify the object belongs to the authenticated user
        user_hash = hashlib.md5(normalized_email.encode()).hexdigest()
        expected_prefix = f"users/{user_hash}/"

        if not s3_key.startswith(expected_prefix):
            return cors_response(403, {'error': 'Access denied - object does not belong to user'})

        # Get object to verify ownership and get token for cleanup
        try:
            obj_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=s3_key)
            obj_data = json.loads(obj_response['Body'].read())

            # Double-check ownership
            if obj_data.get('ownerEmail') != normalized_email:
                return cors_response(403, {'error': 'Access denied - ownership mismatch'})

            object_token = obj_data.get('token')
        except s3_client.exceptions.NoSuchKey:
            return cors_response(404, {'error': 'Object not found'})

        # Delete the main object
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=s3_key)

        # Delete the token reference if it exists
        if object_token:
            try:
                token_key = f"tokens/{object_token}.json"
                s3_client.delete_object(Bucket=BUCKET_NAME, Key=token_key)
            except Exception as e:
                print(f"Warning: Could not delete token reference {token_key}: {e}")

        # Track successful deletion
        track_metrics('ObjectDeleted',
                     email=normalized_email,
                     object_type=obj_data.get('type'),
                     security_type=obj_data.get('securityType', 'none'))

        return cors_response(200, {
            'success': True,
            'message': f'Object "{obj_data.get("name", "unknown")}" deleted successfully'
        })

    except Exception as e:
        print(f"Error deleting object: {e}")
        return cors_response(500, {'error': 'Failed to delete object', 'details': str(e)})

def get_object_content(body: Dict[str, Any]) -> Dict[str, Any]:
    """Return full decrypted content of an owned object for editing — STRICT AUTH REQUIRED"""
    is_valid, error_msg, normalized_email = verify_user_auth(body)
    if not is_valid:
        return cors_response(401, {'error': error_msg})

    s3_key = body.get('s3Key')
    if not s3_key:
        return cors_response(400, {'error': 'S3 key is required'})

    user_hash = hashlib.md5(normalized_email.encode()).hexdigest()
    if not s3_key.startswith(f"users/{user_hash}/"):
        return cors_response(403, {'error': 'Access denied'})

    try:
        obj_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        obj_data = json.loads(obj_response['Body'].read())

        if obj_data.get('ownerEmail') != normalized_email:
            return cors_response(403, {'error': 'Access denied'})

        decrypted = decrypt_content(obj_data.get('content', ''))
        return cors_response(200, {'content': decrypted})

    except s3_client.exceptions.NoSuchKey:
        return cors_response(404, {'error': 'Object not found'})
    except Exception as e:
        return cors_response(500, {'error': 'Failed to get content', 'details': str(e)})

def update_object(body: Dict[str, Any]) -> Dict[str, Any]:
    """Update content of an owned object — STRICT AUTH REQUIRED"""
    is_valid, error_msg, normalized_email = verify_user_auth(body)
    if not is_valid:
        return cors_response(401, {'error': error_msg})

    s3_key = body.get('s3Key')
    new_content = body.get('content')

    if not s3_key or new_content is None:
        return cors_response(400, {'error': 'S3 key and content are required'})

    if len(str(new_content).encode('utf-8')) > 1024 * 1024:
        return cors_response(400, {'error': 'Content too large. Maximum size is 1MB.'})

    user_hash = hashlib.md5(normalized_email.encode()).hexdigest()
    if not s3_key.startswith(f"users/{user_hash}/"):
        return cors_response(403, {'error': 'Access denied'})

    try:
        obj_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        obj_data = json.loads(obj_response['Body'].read())

        if obj_data.get('ownerEmail') != normalized_email:
            return cors_response(403, {'error': 'Access denied'})

        if obj_data.get('ttl', 0) <= int(time.time() * 1000):
            return cors_response(410, {'error': 'Object has expired'})

        obj_data['content'] = encrypt_content(new_content)

        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=json.dumps(obj_data),
            ContentType='application/json'
        )

        return cors_response(200, {'success': True})

    except s3_client.exceptions.NoSuchKey:
        return cors_response(404, {'error': 'Object not found'})
    except Exception as e:
        return cors_response(500, {'error': 'Failed to update object', 'details': str(e)})

def regenerate_recovery_codes(body: Dict[str, Any]) -> Dict[str, Any]:
    """Replace the recovery-code set for an owned TOTP secret."""
    is_valid, error_msg, normalized_email = verify_user_auth(body)
    if not is_valid:
        return cors_response(401, {'error': error_msg})

    s3_key = body.get('s3Key')
    user_hash = hashlib.md5(normalized_email.encode()).hexdigest()
    if not s3_key:
        return cors_response(400, {'error': 'S3 key is required'})
    if not s3_key.startswith(f"users/{user_hash}/"):
        return cors_response(403, {'error': 'Access denied'})

    try:
        obj_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        obj_data = json.loads(obj_response['Body'].read())
        if obj_data.get('ownerEmail') != normalized_email:
            return cors_response(403, {'error': 'Access denied'})
        if obj_data.get('securityType') != 'totp':
            return cors_response(400, {'error': 'This secret does not use TOTP'})
        if obj_data.get('ttl', 0) <= int(time.time() * 1000):
            return cors_response(410, {'error': 'Object has expired'})

        codes = generate_recovery_codes()
        obj_data['recoveryCodes'] = codes
        s3_client.put_object(Bucket=BUCKET_NAME, Key=s3_key,
                             Body=json.dumps(obj_data), ContentType='application/json')
        return cors_response(200, {'success': True, 'recoveryCodes': codes})
    except s3_client.exceptions.NoSuchKey:
        return cors_response(404, {'error': 'Object not found'})
    except Exception as e:
        return cors_response(500, {'error': 'Failed to regenerate recovery codes', 'details': str(e)})
