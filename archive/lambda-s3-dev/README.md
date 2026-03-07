# Trufo Lambda + S3 Architecture

A complete rewrite of Trufo using AWS Lambda and S3 for simplified, cost-effective object storage.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Lambda        │    │   S3 Bucket     │    │   Email         │
│   Function      │◄──►│   Storage       │    │   Validation    │
│                 │    │                 │    │                 │
│ • Web Interface │    │ • User Objects  │    │ • SMTP          │
│ • API Endpoints │    │ • Token Index   │    │ • Verification  │
│ • Auth System   │    │ • Encryption    │    │ • Codes         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📦 Components

- **Lambda Function**: Single Python function handling web UI and API
- **S3 Storage**: Object storage organized by user/type/name
- **Email Authentication**: SMTP-based email verification system
- **Web Interface**: HTML/CSS/JS served directly from Lambda

## 🚀 Initial Deployment

### Prerequisites
- AWS CLI installed and configured
- AWS SAM CLI installed
- Appropriate AWS permissions for Lambda, S3, and IAM

### Step 1: Deploy Infrastructure
```bash
cd lambda-s3

# Build the application
sam build

# Deploy with guided prompts (first time only)
sam deploy --guided

# Or deploy with parameters directly
sam deploy \
  --stack-name trufo-lambda-s3 \
  --region us-east-1 \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    BucketName="trufo-storage-$(date +%s)" \
    FromEmail="noreply@yourdomain.com" \
    DomainName="trufo.yourdomain.com" \
    HostedZoneId="Z1D633PJN98FT9" \
    GitHubOrg="your-github-username" \
    GitHubRepo="trufo"
```

### Step 2: Configure GitHub Repository
1. **Set up GitHub Variables** (not secrets):
   ```
   FROM_EMAIL        - Email address verified in SES
   DOMAIN_NAME       - Custom domain (optional, e.g., trufo.example.com)
   HOSTED_ZONE_ID    - Route53 Hosted Zone ID (optional)
   AWS_ROLE_ARN      - GitHub Actions IAM Role ARN (from CloudFormation output)
   ```

2. **No AWS credentials needed** - Uses OIDC role assumption

### Step 3: Enable Auto-Deployment
1. Push changes to the `lambda-s3/` directory
2. GitHub Actions will automatically deploy updates
3. Monitor deployment in the Actions tab

## 🔧 Configuration

### SES Email Setup
**Required**: Verify your email address in Amazon SES:

```bash
# Verify your from email address
aws ses verify-email-identity --email-address noreply@yourdomain.com

# For custom domains, verify the domain
aws ses verify-domain-identity --domain yourdomain.com

# Check verification status
aws ses get-identity-verification-attributes --identities noreply@yourdomain.com
```

**Production Access**: Request SES production access to remove sandbox limitations:
- Visit: https://console.aws.amazon.com/ses/
- Go to "Sending statistics" → "Request production access"

### Environment Variables
The Lambda function uses these environment variables:
- `S3_BUCKET_NAME`: S3 bucket for object storage
- `FROM_EMAIL`: From email address for notifications (must be verified in SES)
- `ENCRYPTION_KEY`: Key for content encryption (auto-generated)

### Custom Domain Setup
1. **Set parameters during deployment**:
   - `DomainName`: Your custom domain (e.g., trufo.example.com)
   - `HostedZoneId`: Route53 Hosted Zone ID

2. **Route53 records** are created automatically if HostedZoneId is provided

3. **Manual DNS setup** if not using Route53:
   - Create CNAME record: `trufo.example.com` → `{function-url-domain}`
   - Create CNAME record: `www.trufo.example.com` → `{function-url-domain}`

## 📁 S3 Storage Structure

```
s3://trufo-storage-bucket/
├── users/
│   ├── {user-hash}/
│   │   ├── strings/
│   │   │   └── {object-name}.json
│   │   ├── booleans/
│   │   │   └── {object-name}.json
│   │   └── toggles/
│   │       └── {object-name}.json
└── tokens/
    └── {token}.json → points to actual object
```

## 🌐 API Endpoints

### Web Interface
- `GET /` - Home/Create page
- `GET /create` - Object creation form
- `GET /access/{token}` - Object access page
- `GET /manage` - Object management dashboard

### REST API
- `POST /api/objects` - Create new object
- `GET /api/objects?name={name}&token={token}&secret={secret}` - Access object
- `GET /api/user-objects?email={email}` - List user objects
- `DELETE /api/objects?id={id}` - Delete object
- `POST /api/toggle` - Toggle boolean object
- `POST /api/validate-email` - Send email validation code
- `POST /api/verify-code` - Verify email validation code

## 🔐 Security Features

- **Email Verification**: Required for object creation
- **User Secrets**: Generated from email for access control
- **Content Encryption**: All content encrypted at rest
- **TOTP MFA**: Optional 2FA for sensitive objects
- **TTL Expiration**: Automatic object deletion
- **One-time Access**: Objects deleted after reading

## 🚀 Migration from DynamoDB

The new architecture provides:
- **100% feature parity** with existing DynamoDB version
- **Cost reduction** by eliminating DynamoDB charges
- **Simplified deployment** with single Lambda function
- **Better file handling** with native S3 support

### Migration Steps
1. Deploy new Lambda + S3 architecture
2. Export existing data from DynamoDB
3. Import data to new S3 structure
4. Update DNS/domain to point to new Function URL
5. Decommission old infrastructure

## 📊 Monitoring

Monitor your deployment through:
- **CloudWatch Logs**: Lambda function logs
- **CloudWatch Metrics**: Function performance metrics
- **S3 Metrics**: Storage usage and request metrics
- **GitHub Actions**: Deployment status and history

## 🛠️ Development

### Local Testing
```bash
# Start local API
sam local start-api

# Test specific function
sam local invoke TrufoLambdaFunction --event events/test-event.json
```

### Code Structure
- `lambda_function.py` - Main Lambda handler
- `templates.py` - HTML templates for web interface
- `cloudformation.yaml` - Infrastructure as Code
- `requirements.txt` - Python dependencies

## 📝 Cost Optimization

This architecture significantly reduces costs:
- **No DynamoDB charges**: Only S3 storage and requests
- **Lambda efficiency**: Pay per invocation, not continuous running
- **S3 pricing**: Much lower than DynamoDB for object storage
- **No CloudFront**: Direct Lambda Function URL access