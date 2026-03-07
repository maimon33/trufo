# Lambda Function Deployment Guide

## Step 1: Deploy Infrastructure

Deploy the CloudFormation stack to create DynamoDB table and Lambda function:

```bash
aws cloudformation deploy \
  --template-file cloudformation.yaml \
  --stack-name trufo-api-stack \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides AdminToken=your-super-secret-admin-token
```

## Step 2: Build and Upload Lambda Code

1. Install dependencies:
```bash
cd lambda
npm install
```

2. Create deployment package:
```bash
zip -r trufo-api.zip . -x "*.md" "cloudformation.yaml"
```

3. Upload the function code:
```bash
aws lambda update-function-code \
  --function-name trufo-api \
  --zip-file fileb://trufo-api.zip
```

## Step 3: Get Function URL

Get your Lambda Function URL:

```bash
aws cloudformation describe-stacks \
  --stack-name trufo-api-stack \
  --query 'Stacks[0].Outputs[?OutputKey==`FunctionUrl`].OutputValue' \
  --output text
```

## Step 4: Update Environment Variables

Add this URL to your GitHub secrets as `VITE_LAMBDA_API_URL`:

```
https://abc123.lambda-url.us-east-1.on.aws
```

## Architecture Overview

```
React App → Lambda Function URL → Lambda → DynamoDB
```

**Benefits:**
- ✅ No API Gateway complexity or cost
- ✅ Direct HTTPS endpoint
- ✅ Built-in CORS handling
- ✅ Server-side security
- ✅ Scalable and cost-effective

## API Endpoints

- `POST /objects` - Create object
- `GET /objects?name=X&token=Y` - Access object
- `GET /user-objects?email=X` - Get user's objects
- `PUT /objects` - Update object
- `DELETE /objects?id=X` - Delete object
- `GET /admin/objects?adminToken=X` - Admin: get all objects
- `POST /admin/cleanup` - Admin: cleanup expired objects

## Cost Estimate

**DynamoDB:**
- 25 WCU/25 RCU free tier
- $0.25 per million reads after free tier

**Lambda:**
- 1M requests free per month
- $0.20 per 1M requests after free tier

**Total for low traffic:** ~$0-$2/month