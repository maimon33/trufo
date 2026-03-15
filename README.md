# 🔒 Trufo - Secure Object Storage

Trufo is a serverless secret storage service built with AWS Lambda and S3. Create and share temporary encrypted objects with email validation, TOTP 2FA, and automatic expiration.

## ✨ Features

- **🔐 Secure Storage**: Email validation and content encryption
- **⏰ Auto-Expiration**: Objects automatically deleted after TTL
- **🔑 TOTP 2FA**: Optional two-factor authentication
- **🔄 Toggle Objects**: Boolean objects that flip on each access
- **📱 One-Time Access**: Self-destructing objects
- **🌐 Web Interface**: Built-in HTML interface (no build required)
- **📧 Email Validation**: Amazon SES integration
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
git clone https://github.com/your-username/trufo.git
cd trufo

# Build and deploy
sam build
sam deploy --guided
```

#### Option B: Terraform (Recommended for infrastructure teams)

```bash
# Clone the repository
git clone https://github.com/your-username/trufo.git
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
- **DomainName**: Custom domain (optional, e.g., trufo.example.com)
- **HostedZoneId**: Route53 hosted zone ID (optional)
- **GitHubOrg**: Your GitHub username/organization
- **GitHubRepo**: Repository name (for CI/CD)

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

1. **Lambda Function URL** (default): Direct access to your Lambda function
   - Main Interface: `https://{function-id}.lambda-url.{region}.on.aws/`
   - Create Objects: `https://{function-id}.lambda-url.{region}.on.aws/create`
   - Manage Objects: `https://{function-id}.lambda-url.{region}.on.aws/manage`
   - Access Objects: `https://{function-id}.lambda-url.{region}.on.aws/access/{token}`

2. **API Gateway** (when configured): More features and better performance
   - Main Interface: `https://{api-id}.execute-api.{region}.amazonaws.com/Prod/`
   - Create Objects: `https://{api-id}.execute-api.{region}.amazonaws.com/Prod/create`
   - Manage Objects: `https://{api-id}.execute-api.{region}.amazonaws.com/Prod/manage`
   - Access Objects: `https://{api-id}.execute-api.{region}.amazonaws.com/Prod/access/{token}`

3. **Custom Domain** (optional): User-friendly URLs
   - Main Interface: `https://trufo.yourdomain.com/`
   - Create Objects: `https://trufo.yourdomain.com/create`
   - Manage Objects: `https://trufo.yourdomain.com/manage`
   - Access Objects: `https://trufo.yourdomain.com/access/{token}`

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
    "ttlHours": 24,
    "ownerEmail": "user@example.com",
    "oneTimeAccess": false,
    "enableMFA": false
  }'

# Access an object (API Gateway)
curl "https://your-base-url/api/objects?name=my-secret&token=abc123&secret=user-secret"

# Access an object (no-GUI direct link)
curl "https://your-base-url/api/access/abc123?secret=user-secret"

# List user objects
curl "https://your-base-url/api/user-objects?email=user@example.com"

# Send email validation
curl -X POST https://your-base-url/api/send-email-validation \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'

# Verify email code
curl -X POST https://your-base-url/api/verify-email-code \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "code": "123456"}'
```

## 📁 Project Structure

```
trufo/
├── lambda_function.py     # Main Lambda handler
├── templates.py           # HTML web interface
├── requirements.txt       # Python dependencies
├── template.yaml          # Infrastructure as Code (SAM)
├── terraform/            # Infrastructure as Code (Terraform)
│   ├── main.tf           # Main Terraform configuration
│   ├── variables.tf      # Input variables
│   ├── outputs.tf        # Output values
│   ├── terraform.tfvars.example  # Example configuration
│   └── README.md         # Terraform deployment guide
├── .github/workflows/     # CI/CD automation
│   ├── deploy.yml        # SAM deployment workflow
│   └── terraform-deploy.yml  # Terraform deployment workflow
├── README.md             # This file
├── local-dev/            # React development environment
│   ├── src/              # React components
│   ├── package.json      # Node.js dependencies
│   └── README.md         # Local development guide
└── archive/              # Previous architectures
    ├── lambda-dynamodb/  # Original DynamoDB version
    └── lambda-s3-dev/    # Development version
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

### SES Production Access

For production use, request SES production access:
1. Visit [AWS SES Console](https://console.aws.amazon.com/ses/)
2. Go to "Sending statistics" → "Request production access"
3. Complete the form with your use case

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

- **Issues**: [GitHub Issues](https://github.com/your-username/trufo/issues)
- **Documentation**: This README and inline code comments
- **AWS Support**: [AWS Documentation](https://docs.aws.amazon.com/)

---

Made with ❤️ using AWS Lambda + S3