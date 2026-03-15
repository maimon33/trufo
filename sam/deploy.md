# 🚀 Quick Deployment Guide

## Step 1: Basic Deployment (No GitHub Actions)

```bash
cd sam
sam build
sam deploy --guided
```

**When prompted, use these settings:**
- Stack Name: `trufo-app`
- AWS Region: `us-east-1` (or your preferred region)
- FromEmail: `your-email@domain.com` (must verify in SES later)
- DomainName: `` (leave empty for now)
- HostedZoneId: `` (leave empty for now)
- GitHubOrg: `` (leave empty for now)
- GitHubRepo: `` (leave empty for now)
- **CreateGitHubRole: `false`** ⚠️ **Important: Set to false**

## Step 2: Verify Email in SES

After deployment, verify your email:

```bash
aws ses verify-email-identity --email-address your-email@domain.com
```

## Step 3: Test Your Application

Get your Function URL from the CloudFormation outputs:

```bash
aws cloudformation describe-stacks --stack-name trufo-app --query 'Stacks[0].Outputs[?OutputKey==`FunctionUrl`].OutputValue' --output text
```

Visit the URL to test your Trufo application!

## Optional: GitHub Actions Setup

If you want GitHub Actions later:

### 1. Create OIDC Provider (One-time setup)

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

### 2. Update Stack with GitHub Role

```bash
sam deploy --parameter-overrides \
  CreateGitHubRole=true \
  GitHubOrg=your-username \
  GitHubRepo=trufo
```

### 3. Configure GitHub Variables

Set these in your GitHub repository settings:
- `AWS_ROLE_ARN`: From CloudFormation outputs
- `FROM_EMAIL`: Your verified email address

## Troubleshooting

**Issue**: OIDC Provider error
**Solution**: Set `CreateGitHubRole=false` during first deployment

**Issue**: SES email not working
**Solution**: Run `aws ses verify-email-identity --email-address your-email@domain.com`

**Issue**: Function timeout
**Solution**: Check CloudWatch logs for details