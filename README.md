# 🔒 Trufo - Secure Object Storage

Trufo is a serverless secret storage service built with AWS Lambda and S3. Create and share temporary encrypted objects with email validation, TOTP 2FA, and automatic expiration.

## Chrome Extension

Create secrets from any tab without leaving your browser. The extension stores your auth session for up to 30 days so one-click sharing is always one click away.

→ **[maimon33/chrome-extensions](https://github.com/maimon33/chrome-extensions)** — source and releases

## ✨ Features

- **🔐 Secure Storage**: Email validation and content encryption
- **⏰ Auto-Expiration**: Objects automatically deleted after TTL
- **🔑 TOTP 2FA**: Optional two-factor authentication
- **🔄 Toggle Objects**: Boolean objects that flip on each access
- **📱 One-Time Access**: Self-destructing objects
- **🌐 Web Interface**: Built-in HTML interface with secret management
- **📧 Email Validation**: Amazon SES integration with DKIM
- **📊 Admin Monitoring**: Daily reports, usage alerts, kill switches
- **🛡️ Enterprise Controls**: Real-time monitoring and operational dashboards
- **🏗️ Serverless**: AWS Lambda + S3 architecture
- **💰 Cost Effective**: No DynamoDB charges

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Lambda        │    │   S3 Bucket     │    │   Amazon        │
│   Function      │◄──►│   Storage       │    │   SES           │
│                 │    │                 │    │                 │
│ • Web Interface │    │ • User Objects  │    │ • Email         │
│ • API Endpoints │    │ • Token Index   │    │ • Validation    │
│ • Auth System   │    │ • Encryption    │    │ • Delivery      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Deployment

### Prerequisites
- AWS CLI configured with appropriate permissions
- AWS SAM CLI installed
- Python 3.9+

### 1. Deploy Infrastructure

Choose your preferred deployment method:

#### Option A: AWS SAM (Recommended for beginners)

```bash
# Clone the repository
git clone https://github.com/maimon33/trufo.git
cd trufo

# Build and deploy
cd sam
sam build
sam deploy --guided
```

#### Option B: Terraform (Recommended for infrastructure teams)

```bash
# Clone the repository
git clone https://github.com/maimon33/trufo.git
cd trufo/terraform

# Initialize Terraform
terraform init

# Configure variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your settings

# Deploy
terraform plan
terraform apply
```

### 2. Configure Parameters

#### For AWS SAM:
During `sam deploy --guided`, you'll be prompted for:

- **FromEmail**: Email address for notifications (must verify in SES)
- **AdminEmail**: Admin email for alerts and daily reports (optional)
- **DailyUsageThreshold**: Daily object creation threshold for alerts (default: 1000)
- **MonthlyUsageThreshold**: Monthly object creation threshold for alerts (default: 10000)
- **EnableKillSwitch**: Enable emergency kill switch (default: false)
- **DomainName**: Custom domain (optional, e.g., trufo.example.com)
- **HostedZoneId**: Route53 hosted zone ID (optional)
- **SESEmailDomain**: Domain for SES email deliverability (optional)

#### For Terraform:
Edit `terraform/terraform.tfvars` with your configuration:

```hcl
from_email      = "noreply@yourdomain.com"  # Required
domain_name     = "trufo.yourdomain.com"    # Optional
hosted_zone_id  = "Z1D633PJN98FT9"          # Optional
github_org      = "your-username"            # Optional
github_repo     = "trufo"                   # Optional
```

### 3. Verify SES Email

```bash
# Verify your email address in Amazon SES
aws ses verify-email-identity --email-address noreply@yourdomain.com

# Check verification status
aws ses get-identity-verification-attributes --identities noreply@yourdomain.com
```

### 4. Configure GitHub (Optional)

For automatic deployments, set these GitHub repository variables:

```
AWS_ROLE_ARN      # From CloudFormation output
FROM_EMAIL        # SES verified email
DOMAIN_NAME       # Custom domain (optional)
HOSTED_ZONE_ID    # Route53 zone ID (optional)
```

## 🌐 Usage

### Web Interface

After deployment, access your Trufo instance through:

1. **API Gateway** (default): Feature-complete interface
   - **Main Interface**: `https://{api-id}.execute-api.{region}.amazonaws.com/Prod/`
   - **Access Objects**: `https://{api-id}.execute-api.{region}.amazonaws.com/Prod/access/{token}`
   - **Secret Management**: `https://{api-id}.execute-api.{region}.amazonaws.com/Prod/secret/{token}`

2. **Custom Domain** (recommended): User-friendly URLs
   - **Main Interface**: `https://trufo.yourdomain.com/`
   - **Access Objects**: `https://trufo.yourdomain.com/access/{token}`
   - **Secret Management**: `https://trufo.yourdomain.com/secret/{token}`

#### Web Interface Features:
- **📧 Email Authentication**: Verify email to create secrets
- **📋 My Secrets**: List and manage your created secrets
- **🔄 Return Navigation**: Easy switching between create and list views
- **🔥 One-time Access**: Option to delete after first read
- **⚠️ TTL Configuration**: Set expiration from 1 hour to 1 year
- **🔒 Security Levels**: None, Email Notification, TOTP 2FA

### Get Your URLs

```bash
# Get Lambda Function URL
aws cloudformation describe-stacks --stack-name trufo-app \
  --query 'Stacks[0].Outputs[?OutputKey==`FunctionUrl`].OutputValue' --output text

# Get API Gateway URL
aws cloudformation describe-stacks --stack-name trufo-app \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' --output text

# Get Custom Domain URL (if configured)
aws cloudformation describe-stacks --stack-name trufo-app \
  --query 'Stacks[0].Outputs[?OutputKey==`WebsiteURL`].OutputValue' --output text
```

### API Endpoints

Use any of the base URLs above with these API paths:

```bash
# Create an object
curl -X POST https://your-base-url/api/objects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-secret",
    "type": "string",
    "content": "Hello World!",
    "ttl": "24h",
    "ownerEmail": "user@example.com",
    "security": "none",
    "oneTimeAccess": false
  }'

# Access an object
curl "https://your-base-url/api/access/abc123?secret=user-secret"

# List user secrets
curl -X POST https://your-base-url/api/list-secrets \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "secret": "user-secret"}'

# Send email validation
curl -X POST https://your-base-url/api/validate-email \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'

# Verify email code
curl -X POST https://your-base-url/api/verify-code \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "code": "123456"}'

# Toggle an object (for toggle type)
curl -X POST https://your-base-url/api/toggle \
  -H "Content-Type: application/json" \
  -d '{"token": "abc123", "secret": "user-secret"}'
```

## 📁 Project Structure

```
trufo/
├── src/                      # Application source code
│   ├── lambda_function.py    # Main Lambda handler
│   ├── templates.py          # HTML web interface
│   ├── reports.py            # Daily reporting system
│   └── requirements.txt      # Python dependencies
├── sam/                      # SAM deployment
│   └── template.yaml         # Infrastructure as Code (SAM)
├── terraform/                # Infrastructure as Code (Terraform)
│   ├── main.tf              # Main Terraform configuration
│   ├── variables.tf         # Input variables
│   ├── outputs.tf           # Output values
│   └── terraform.tfvars.example  # Example configuration
├── .github/workflows/        # CI/CD automation
│   └── deploy.yml           # SAM deployment workflow
├── README.md                # This file
├── ADMIN_OPERATIONS_GUIDE.md # Admin monitoring and operations
├── SES_SETUP_GUIDE.md       # Email deliverability setup
└── deploy.md               # Deployment instructions
```

## 🔧 Configuration

### Custom Domain Setup

#### With AWS SAM:
1. **With Route53** (automatic):
   ```bash
   sam deploy --parameter-overrides \
     DomainName="trufo.example.com" \
     HostedZoneId="Z1D633PJN98FT9"
   ```

2. **External DNS** (manual):
   ```bash
   # Get DNS target from CloudFormation outputs
   aws cloudformation describe-stacks --stack-name trufo-app \
     --query 'Stacks[0].Outputs[?OutputKey==`DNSTarget`].OutputValue' --output text

   # Get complete DNS instructions
   aws cloudformation describe-stacks --stack-name trufo-app \
     --query 'Stacks[0].Outputs[?OutputKey==`ExternalDNSInstructions`].OutputValue' --output text
   ```

#### With Terraform:
1. **With Route53** (automatic):
   ```hcl
   domain_name     = "trufo.example.com"
   hosted_zone_id  = "Z1D633PJN98FT9"
   ```

2. **External DNS** (manual):
   ```bash
   # Get DNS target from Terraform outputs
   terraform output function_url

   # Extract domain from Function URL
   terraform output -raw function_url | sed 's|https://||' | sed 's|/.*||'
   ```

### Admin Monitoring Setup

Deploy with monitoring features:

```bash
sam deploy --parameter-overrides \
  AdminEmail="admin@yourcompany.com" \
  DailyUsageThreshold=1000 \
  MonthlyUsageThreshold=10000 \
  EnableKillSwitch=false
```

This enables:
- **Daily Email Reports**: Usage statistics, storage stats, error summaries
- **Real-time Alerts**: High usage, high error rates via SNS
- **Emergency Kill Switch**: API Gateway throttling controls
- **CloudWatch Dashboard**: Monitoring metrics and trends

See [ADMIN_OPERATIONS_GUIDE.md](ADMIN_OPERATIONS_GUIDE.md) for complete operational procedures.

### SES Production Access

For production use, request SES production access:
1. Visit [AWS SES Console](https://console.aws.amazon.com/ses/)
2. Go to "Sending statistics" → "Request production access"
3. Complete the form with your use case

For email deliverability setup, see [SES_SETUP_GUIDE.md](SES_SETUP_GUIDE.md)

### Environment Variables

Lambda automatically receives these environment variables:

- `S3_BUCKET_NAME`: S3 bucket for object storage
- `FROM_EMAIL`: SES verified sender email
- `ENCRYPTION_KEY`: Auto-generated encryption key

## 🛠️ Development

### Local Development

Use the React development environment:

```bash
cd local-dev
npm install
npm run dev
```

### Testing Lambda Locally

#### With AWS SAM:
```bash
# Start local API
sam local start-api

# Test specific function
sam local invoke TrufoLambdaFunction --event events/test-event.json
```

#### With Terraform:
```bash
# Create a test Lambda package
cd terraform
terraform apply  # This creates lambda_function.zip

# Use AWS CLI to test
aws lambda invoke --function-name $(terraform output -raw lambda_function_name) \
  --payload '{"httpMethod":"GET","path":"/"}' \
  response.json
```

## 📊 Storage Structure

Objects are stored in S3 with this structure:

```
s3://bucket-name/
├── users/
│   ├── {email-hash}/
│   │   ├── strings/{name}.json
│   │   ├── booleans/{name}.json
│   │   └── toggles/{name}.json
└── tokens/
    └── {token}.json → reference to actual object
```

## 🔐 Security Features

- **Email Verification**: Required for object creation
- **Content Encryption**: All objects encrypted at rest
- **User Secrets**: Generated from email for access control
- **TOTP MFA**: Optional 2FA using authenticator apps
- **TTL Expiration**: Automatic cleanup of expired objects
- **One-Time Access**: Objects deleted after single read
- **HTTPS Only**: All communication encrypted in transit

## 💰 Cost Optimization

This architecture is optimized for cost:

- **No DynamoDB**: Only S3 storage costs (~$0.023/GB/month)
- **Lambda Efficiency**: Pay-per-request pricing
- **No CloudFront**: Direct Function URL access
- **Automatic Cleanup**: Expired objects removed automatically

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/maimon33/trufo/issues)
- **Documentation**: This README and inline code comments
- **AWS Support**: [AWS Documentation](https://docs.aws.amazon.com/)

---

Made with ❤️ using AWS Lambda + S3