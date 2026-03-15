import json
import boto3
import hashlib
import uuid
import time
import base64
import hmac
import secrets
from datetime import datetime, timedelta
from urllib.parse import parse_qs, unquote
import os
from typing import Dict, Any, Optional, Tuple
from templates import serve_create_page, serve_access_page, serve_manage_page

# AWS clients
s3_client = boto3.client('s3')

# Configuration
BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'trufo-storage')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@trufo.com')
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', 'default-key-change-in-production-32b')

# AWS SES client
ses_client = boto3.client('ses')

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

    if content_type == 'text/html':
        body = data if isinstance(data, str) else str(data)
    else:
        body = json.dumps(data)

    return {
        'statusCode': status_code,
        'headers': headers,
        'body': body
    }

def generate_user_secret(email: str) -> str:
    """Generate consistent user secret from email"""
    return hashlib.sha256(email.lower().encode()).hexdigest()

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
    user_hash = hashlib.md5(user_email.lower().encode()).hexdigest()
    return f"users/{user_hash}/{object_type}/{object_name}.json"

def generate_totp_secret() -> str:
    """Generate TOTP secret"""
    return base64.b32encode(secrets.token_bytes(20)).decode()

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

    # Create email hash for storage
    email_hash = hashlib.md5(email.lower().encode()).hexdigest()

    # Store code with expiration (5 minutes) and track last sent time
    email_codes[email_hash] = {
        'email': email,
        'code': code,
        'expires': time.time() + 300,
        'last_sent': time.time()
    }

    # Send email
    try:
        send_email(email, 'Trufo Verification Code', f'Your verification code is: {code}')
        return cors_response(200, {'message': 'Verification code sent'})
    except Exception as e:
        return cors_response(500, {'error': 'Failed to send email', 'details': str(e)})

def verify_email_code(body: Dict[str, Any]) -> Dict[str, Any]:
    """Verify email validation code"""
    email = body.get('email')
    code = body.get('code')

    if not email or not code:
        return cors_response(400, {'error': 'Email and code are required'})

    email_hash = hashlib.md5(email.lower().encode()).hexdigest()
    stored_data = email_codes.get(email_hash)
    if not stored_data:
        return cors_response(400, {'error': 'No code found for this email'})

    if time.time() > stored_data['expires']:
        del email_codes[email_hash]
        return cors_response(400, {'error': 'Code expired'})

    if stored_data['code'] != code:
        return cors_response(400, {'error': 'Invalid code'})

    # Code verified, remove from storage
    del email_codes[email_hash]

    # Generate user secret
    user_secret = generate_user_secret(email)

    return cors_response(200, {
        'verified': True,
        'userSecret': user_secret
    })

# S3 Storage Operations
def create_object(body: Dict[str, Any]) -> Dict[str, Any]:
    """Create new object in S3"""
    required_fields = ['name', 'type', 'content', 'ttlHours', 'ownerEmail']
    for field in required_fields:
        if field not in body:
            return cors_response(400, {'error': f'Missing required field: {field}'})

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

    # Prepare object data
    object_data = {
        'id': object_id,
        'name': body['name'],
        'type': body['type'],
        'content': encrypt_content(body['content']),
        'ttl': ttl,
        'token': token,
        'ownerEmail': body['ownerEmail'],
        'ownerName': body.get('ownerName', 'Anonymous'),
        'hitCount': 0,
        'createdAt': int(time.time() * 1000),
        'lastHit': None,
        'oneTimeAccess': body.get('oneTimeAccess', False),
        'totpSecret': generate_totp_secret() if body.get('enableMFA', False) else None
    }

    # Store in S3
    try:
        s3_key = generate_s3_key(body['ownerEmail'], body['type'], body['name'])
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

        user_secret = generate_user_secret(body['ownerEmail'])

        return cors_response(201, {
            'success': True,
            'object': object_data,
            'userSecret': user_secret
        })

    except Exception as e:
        return cors_response(500, {'error': 'Failed to create object', 'details': str(e)})

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

        # Verify user secret
        expected_secret = generate_user_secret(object_data['ownerEmail'])
        if secret != expected_secret:
            return cors_response(403, {'error': 'Invalid secret for this object'})

        # Check expiration
        if object_data['ttl'] <= int(time.time() * 1000):
            # Delete expired object
            s3_client.delete_object(Bucket=BUCKET_NAME, Key=token_data['s3_key'])
            s3_client.delete_object(Bucket=BUCKET_NAME, Key=token_key)
            return cors_response(410, {'error': 'Object has expired and has been deleted'})

        # Handle MFA
        if object_data.get('totpSecret'):
            if not totp_code:
                return cors_response(403, {
                    'error': 'TOTP verification required',
                    'requiresTOTP': True,
                    'totpQR': f"otpauth://totp/Trufo:{object_data['name']}?secret={object_data['totpSecret']}&issuer=Trufo" if object_data['hitCount'] == 0 else None
                })

            if not verify_totp_token(object_data['totpSecret'], totp_code):
                return cors_response(403, {'error': 'Invalid TOTP code'})

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

        return cors_response(200, {
            'content': response_content,
            'hits': object_data['hitCount']
        })

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
        user_hash = hashlib.md5(email.lower().encode()).hexdigest()
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

        response = ses_client.send_email(
            Source=f"Trufo Verification <{FROM_EMAIL}>",
            Destination={'ToAddresses': [to_email]},
            Message={
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
            Tags=[
                {
                    'Name': 'EmailType',
                    'Value': 'VerificationCode'
                }
            ]
        )
        print(f"Email sent successfully. MessageId: {response['MessageId']}")
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