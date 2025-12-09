# Initial Lambda Setup Guide

⚠️ **Run this ONCE before using GitHub Actions**

## Step 1: Deploy Infrastructure

Deploy the CloudFormation stack:

```bash
cd lambda
aws cloudformation deploy \
  --template-file cloudformation.yaml \
  --stack-name trufo-api-stack \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides AdminToken=your-super-secret-admin-token
```

## Step 2: Build and Upload Initial Code

```bash
# Install dependencies
npm install --production

# Create deployment package
zip -r trufo-api.zip . -x "*.md" "cloudformation.yaml" "initial-setup.md" "deploy.md"

# Upload the function code
aws lambda update-function-code \
  --function-name trufo-api \
  --zip-file fileb://trufo-api.zip
```

## Step 3: Get Your Function URL

```bash
aws cloudformation describe-stacks \
  --stack-name trufo-api-stack \
  --query 'Stacks[0].Outputs[?OutputKey==`FunctionUrl`].OutputValue' \
  --output text
```

Copy this URL - you'll need it for GitHub secrets.

## Step 4: Set GitHub Secrets

Add these secrets to your GitHub repository:

### Required for Lambda:
- `ADMIN_TOKEN`: Your admin token from Step 1
- `VITE_LAMBDA_API_URL`: The Function URL from Step 3

### Existing secrets (keep these):
- `VITE_GOOGLE_CLIENT_ID`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `S3_BUCKET`
- `CLOUDFRONT_DISTRIBUTION_ID` (optional)

## What This Creates:

- DynamoDB table: `trufo-objects`
- Lambda function: `trufo-api`
- Function URL with CORS enabled
- IAM roles and permissions

After this setup, GitHub Actions will automatically deploy Lambda updates on every push.