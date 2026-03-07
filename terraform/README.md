# Trufo Terraform Deployment

This directory contains Terraform configuration for deploying Trufo infrastructure to AWS.

## 🚀 Quick Start

### Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) >= 1.0
- [AWS CLI](https://aws.amazon.com/cli/) configured with appropriate permissions
- Python 3.9+ (for Lambda function)

### 1. Initialize Terraform

```bash
cd terraform
terraform init
```

### 2. Configure Variables

```bash
# Copy the example variables file
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your configuration
```

**Required Variables:**
```hcl
from_email = "noreply@yourdomain.com"  # Must verify in SES
```

**Optional Variables:**
```hcl
domain_name     = "trufo.yourdomain.com"  # Custom domain
hosted_zone_id  = "Z1D633PJN98FT9"        # Route53 zone ID
github_org      = "your-username"          # GitHub org/username
github_repo     = "trufo"                  # Repository name
```

### 3. Plan and Apply

```bash
# Review the planned changes
terraform plan

# Apply the configuration
terraform apply
```

### 4. Configure SES

After deployment, verify your email address:

```bash
# Use the output command from Terraform
terraform output -raw ses_configuration_commands | bash
```

## 📋 Configuration Options

### Basic Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `aws_region` | AWS region for resources | `us-east-1` | No |
| `project_name` | Project name for resource naming | `trufo` | No |
| `environment` | Environment (dev, staging, prod) | `prod` | No |
| `from_email` | SES verified email address | - | **Yes** |

### Domain Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `domain_name` | Custom domain name | `""` | No |
| `hosted_zone_id` | Route53 hosted zone ID | `""` | No |

### GitHub Integration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `github_org` | GitHub organization/username | `""` | No |
| `github_repo` | GitHub repository name | `""` | No |
| `create_github_oidc` | Create GitHub OIDC provider | `true` | No |
| `existing_github_oidc_arn` | Existing OIDC provider ARN | `""` | No |

### Advanced Options

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `s3_bucket_name` | Custom S3 bucket name | Auto-generated | No |
| `log_retention_days` | CloudWatch log retention | `14` | No |
| `lambda_timeout` | Lambda timeout (seconds) | `30` | No |
| `lambda_memory_size` | Lambda memory (MB) | `512` | No |

## 🌐 Deployment Scenarios

### Basic Deployment

Minimal configuration for testing:

```hcl
from_email = "your-email@gmail.com"
```

### Production with Custom Domain

Full production setup:

```hcl
from_email      = "noreply@yourdomain.com"
domain_name     = "trufo.yourdomain.com"
hosted_zone_id  = "Z1D633PJN98FT9"
github_org      = "your-org"
github_repo     = "trufo"
environment     = "prod"
```

### Multi-Environment

Deploy multiple environments:

```bash
# Development
terraform apply -var="environment=dev" -var="project_name=trufo-dev"

# Staging
terraform apply -var="environment=staging" -var="project_name=trufo-staging"

# Production
terraform apply -var="environment=prod" -var="project_name=trufo-prod"
```

## 📤 Outputs

After successful deployment, Terraform provides useful outputs:

```bash
# Get the Function URL
terraform output function_url

# Get the website URL (custom domain or Function URL)
terraform output website_url

# Get GitHub Actions role ARN
terraform output github_actions_role_arn

# Get complete deployment info
terraform output deployment_info

# Get SES setup commands
terraform output -raw ses_configuration_commands
```

## 🔧 Managing State

### Local State (Default)

Terraform state is stored locally in `terraform.tfstate`. **Keep this file secure and backed up.**

### Remote State (Recommended for Teams)

Configure remote state in S3:

```hcl
terraform {
  backend "s3" {
    bucket = "your-terraform-state-bucket"
    key    = "trufo/terraform.tfstate"
    region = "us-east-1"
  }
}
```

## 🚀 CI/CD Integration

### GitHub Actions

After deployment, configure these GitHub repository variables:

```bash
# Get the role ARN from Terraform output
AWS_ROLE_ARN=$(terraform output -raw github_actions_role_arn)

# Set in GitHub repository settings > Variables
FROM_EMAIL=your-verified-email@domain.com
DOMAIN_NAME=trufo.yourdomain.com  # Optional
HOSTED_ZONE_ID=Z1D633PJN98FT9    # Optional
AWS_ROLE_ARN=$AWS_ROLE_ARN
```

The existing GitHub workflow will automatically deploy changes using the Terraform-created IAM role.

## 🛠️ Development Workflow

### Making Changes

1. **Update Configuration**:
   ```bash
   # Edit terraform.tfvars or variables
   vim terraform.tfvars
   ```

2. **Plan Changes**:
   ```bash
   terraform plan
   ```

3. **Apply Changes**:
   ```bash
   terraform apply
   ```

### Updating Lambda Code

When you update Python files, Terraform will automatically detect changes and redeploy:

```bash
# After editing lambda_function.py or templates.py
terraform apply
```

## 🗑️ Cleanup

To destroy all resources:

```bash
terraform destroy
```

**Warning**: This will permanently delete all resources including the S3 bucket and stored objects.

## 🔐 Security Considerations

### IAM Permissions

The Terraform configuration creates minimal required permissions:

- **Lambda Role**: S3 and SES access only
- **GitHub Actions Role**: Limited to necessary AWS services
- **S3 Bucket**: Private with public access blocked

### Secrets Management

- **Email Configuration**: Store sensitive email settings as Terraform variables
- **Encryption**: Objects are encrypted at rest in S3
- **HTTPS**: All communication encrypted in transit

## 🆚 Terraform vs CloudFormation

| Feature | Terraform | CloudFormation |
|---------|-----------|----------------|
| **Multi-cloud** | ✅ Supports multiple providers | ❌ AWS only |
| **State Management** | ✅ Explicit state tracking | ❌ Implicit in AWS |
| **Syntax** | ✅ HCL (more readable) | ❌ JSON/YAML (verbose) |
| **Modules** | ✅ Rich module ecosystem | ❌ Limited |
| **Preview** | ✅ `terraform plan` | ✅ Change sets |
| **AWS Integration** | ❌ Third-party tool | ✅ Native AWS service |
| **Learning Curve** | ❌ Steeper for AWS users | ✅ AWS-native |

Choose **Terraform** for:
- Multi-cloud deployments
- Complex infrastructure
- Team collaboration
- Advanced state management

Choose **CloudFormation** for:
- AWS-only deployments
- Simple setups
- Native AWS integration
- Minimal tooling

## 🐛 Troubleshooting

### Common Issues

**1. Email Not Verified**
```bash
# Verify your email address
aws ses verify-email-identity --email-address your-email@domain.com
```

**2. Domain Issues**
```bash
# Check Route53 zone
aws route53 list-hosted-zones --query 'HostedZones[?Name==`yourdomain.com.`]'
```

**3. Permission Errors**
```bash
# Check AWS credentials
aws sts get-caller-identity
```

**4. State Issues**
```bash
# Refresh Terraform state
terraform refresh

# Force unlock if needed
terraform force-unlock LOCK_ID
```

### Getting Help

1. **Check Terraform Output**: `terraform output`
2. **Validate Configuration**: `terraform validate`
3. **Check AWS Console**: Review resources in AWS console
4. **CloudWatch Logs**: Check Lambda function logs

## 📚 Additional Resources

- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Lambda with Terraform](https://learn.hashicorp.com/tutorials/terraform/lambda-api-gateway)
- [Terraform Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/index.html)
- [AWS SES Documentation](https://docs.aws.amazon.com/ses/)