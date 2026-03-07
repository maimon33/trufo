terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "Trufo"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

locals {
  function_name = "${var.project_name}-lambda-${var.environment}"
  bucket_name   = var.s3_bucket_name != "" ? var.s3_bucket_name : "${var.project_name}-storage-${random_id.bucket_suffix.hex}"
}

# Random suffix for unique bucket naming
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# GitHub OIDC Provider
resource "aws_iam_openid_connect_provider" "github" {
  count = var.create_github_oidc ? 1 : 0

  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "sts.amazonaws.com",
  ]

  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
    "1c58a3a8518e8759bf075b76b750d4f2df264fcd"
  ]

  tags = {
    Name = "${var.project_name}-github-oidc"
  }
}

# S3 Bucket for object storage
resource "aws_s3_bucket" "trufo_storage" {
  bucket = local.bucket_name

  tags = {
    Name = "${var.project_name}-storage"
  }
}

resource "aws_s3_bucket_public_access_block" "trufo_storage" {
  bucket = aws_s3_bucket.trufo_storage.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "trufo_storage" {
  bucket = aws_s3_bucket.trufo_storage.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "trufo_storage" {
  bucket = aws_s3_bucket.trufo_storage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Lambda execution role
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-lambda-role"
  }
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_s3_policy" {
  name = "${var.project_name}-lambda-s3-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.trufo_storage.arn,
          "${aws_s3_bucket.trufo_storage.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_ses_policy" {
  name = "${var.project_name}-lambda-ses-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail",
          "ses:GetSendQuota",
          "ses:GetSendStatistics"
        ]
        Resource = "*"
      }
    ]
  })
}

# GitHub Actions IAM Role
resource "aws_iam_role" "github_actions_role" {
  count = var.github_org != "" && var.github_repo != "" ? 1 : 0
  name  = "${var.project_name}-github-actions-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = var.create_github_oidc ? aws_iam_openid_connect_provider.github[0].arn : var.existing_github_oidc_arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_org}/${var.github_repo}:*"
          }
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-github-actions-role"
  }
}

resource "aws_iam_role_policy" "github_actions_policy" {
  count = var.github_org != "" && var.github_repo != "" ? 1 : 0
  name  = "${var.project_name}-github-actions-policy"
  role  = aws_iam_role.github_actions_role[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudformation:*",
          "lambda:*",
          "iam:*",
          "s3:*",
          "ses:*",
          "route53:*",
          "logs:*"
        ]
        Resource = "*"
      }
    ]
  })
}

# Create Lambda deployment package
data "archive_file" "lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/lambda_function.zip"

  source {
    content = templatefile("${path.root}/lambda_function.py", {
      # Template variables if needed
    })
    filename = "lambda_function.py"
  }

  source {
    content = templatefile("${path.root}/templates.py", {
      # Template variables if needed
    })
    filename = "templates.py"
  }
}

# Lambda function
resource "aws_lambda_function" "trufo_function" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = local.function_name
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime         = "python3.9"
  timeout         = 30
  memory_size     = 512

  environment {
    variables = {
      S3_BUCKET_NAME = aws_s3_bucket.trufo_storage.bucket
      FROM_EMAIL     = var.from_email
      ENCRYPTION_KEY = "${var.project_name}-${data.aws_caller_identity.current.account_id}-key"
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy.lambda_s3_policy,
    aws_iam_role_policy.lambda_ses_policy,
    aws_cloudwatch_log_group.lambda_logs,
  ]

  tags = {
    Name = "${var.project_name}-function"
  }
}

# Lambda Function URL
resource "aws_lambda_function_url" "trufo_function_url" {
  function_name      = aws_lambda_function.trufo_function.function_name
  authorization_type = "NONE"

  cors {
    allow_credentials = false
    allow_headers     = ["content-type", "authorization"]
    allow_methods     = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_origins     = ["*"]
    expose_headers    = []
    max_age          = 86400
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${var.project_name}-lambda-logs"
  }
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# Route53 Records (conditional)
data "aws_route53_zone" "selected" {
  count   = var.domain_name != "" && var.hosted_zone_id != "" ? 1 : 0
  zone_id = var.hosted_zone_id
}

resource "aws_route53_record" "domain" {
  count   = var.domain_name != "" && var.hosted_zone_id != "" ? 1 : 0
  zone_id = var.hosted_zone_id
  name    = var.domain_name
  type    = "CNAME"
  ttl     = 300
  records = [replace(replace(aws_lambda_function_url.trufo_function_url.function_url, "https://", ""), "/", "")]
}

resource "aws_route53_record" "www_domain" {
  count   = var.domain_name != "" && var.hosted_zone_id != "" ? 1 : 0
  zone_id = var.hosted_zone_id
  name    = "www.${var.domain_name}"
  type    = "CNAME"
  ttl     = 300
  records = [replace(replace(aws_lambda_function_url.trufo_function_url.function_url, "https://", ""), "/", "")]
}