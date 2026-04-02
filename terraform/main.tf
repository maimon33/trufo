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
          "ses:GetSendStatistics",
          "ses:VerifyDomainIdentity",
          "ses:GetIdentityVerificationAttributes"
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
          "logs:*",
          "apigateway:*",
          "cloudwatch:*",
          "sns:*",
          "events:*",
          "acm:*"
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

# API Gateway REST API
resource "aws_api_gateway_rest_api" "trufo_api" {
  name        = "${var.project_name}-api-${var.environment}"
  description = "Trufo API Gateway"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  binary_media_types = ["*/*"]

  tags = {
    Name = "${var.project_name}-api"
  }
}

# API Gateway Resource (proxy)
resource "aws_api_gateway_resource" "trufo_proxy" {
  rest_api_id = aws_api_gateway_rest_api.trufo_api.id
  parent_id   = aws_api_gateway_rest_api.trufo_api.root_resource_id
  path_part   = "{proxy+}"
}

# API Gateway Method (root)
resource "aws_api_gateway_method" "trufo_method_root" {
  rest_api_id   = aws_api_gateway_rest_api.trufo_api.id
  resource_id   = aws_api_gateway_rest_api.trufo_api.root_resource_id
  http_method   = "ANY"
  authorization = "NONE"
}

# API Gateway Method (proxy)
resource "aws_api_gateway_method" "trufo_method_proxy" {
  rest_api_id   = aws_api_gateway_rest_api.trufo_api.id
  resource_id   = aws_api_gateway_resource.trufo_proxy.id
  http_method   = "ANY"
  authorization = "NONE"
}

# API Gateway Integration (root)
resource "aws_api_gateway_integration" "trufo_integration_root" {
  rest_api_id             = aws_api_gateway_rest_api.trufo_api.id
  resource_id             = aws_api_gateway_rest_api.trufo_api.root_resource_id
  http_method             = aws_api_gateway_method.trufo_method_root.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.trufo_function.invoke_arn
}

# API Gateway Integration (proxy)
resource "aws_api_gateway_integration" "trufo_integration_proxy" {
  rest_api_id             = aws_api_gateway_rest_api.trufo_api.id
  resource_id             = aws_api_gateway_resource.trufo_proxy.id
  http_method             = aws_api_gateway_method.trufo_method_proxy.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.trufo_function.invoke_arn
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "api_gateway_root" {
  statement_id  = "AllowExecutionFromAPIGatewayRoot"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.trufo_function.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.trufo_api.execution_arn}/*/*"
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "trufo_deployment" {
  depends_on = [
    aws_api_gateway_integration.trufo_integration_root,
    aws_api_gateway_integration.trufo_integration_proxy,
  ]

  rest_api_id = aws_api_gateway_rest_api.trufo_api.id
  stage_name  = "prod"

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.trufo_proxy.id,
      aws_api_gateway_method.trufo_method_root.id,
      aws_api_gateway_method.trufo_method_proxy.id,
      aws_api_gateway_integration.trufo_integration_root.id,
      aws_api_gateway_integration.trufo_integration_proxy.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

# CORS Gateway Responses
resource "aws_api_gateway_gateway_response" "cors_4xx" {
  rest_api_id   = aws_api_gateway_rest_api.trufo_api.id
  response_type = "DEFAULT_4XX"

  response_parameters = {
    "gatewayresponse.header.Access-Control-Allow-Origin"  = "'*'"
    "gatewayresponse.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
    "gatewayresponse.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
  }
}

resource "aws_api_gateway_gateway_response" "cors_5xx" {
  rest_api_id   = aws_api_gateway_rest_api.trufo_api.id
  response_type = "DEFAULT_5XX"

  response_parameters = {
    "gatewayresponse.header.Access-Control-Allow-Origin"  = "'*'"
    "gatewayresponse.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
    "gatewayresponse.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
  }
}

# SSL Certificate for custom domain
resource "aws_acm_certificate" "trufo_cert" {
  count           = var.domain_name != "" ? 1 : 0
  domain_name     = var.domain_name
  subject_alternative_names = ["www.${var.domain_name}"]
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${var.project_name}-certificate"
  }
}

# Certificate validation (only if using Route53)
resource "aws_acm_certificate_validation" "trufo_cert" {
  count           = var.domain_name != "" && var.hosted_zone_id != "" && !var.use_external_dns ? 1 : 0
  certificate_arn = aws_acm_certificate.trufo_cert[0].arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}

# Certificate validation records (only if using Route53)
resource "aws_route53_record" "cert_validation" {
  for_each = var.domain_name != "" && var.hosted_zone_id != "" && !var.use_external_dns ? {
    for dvo in aws_acm_certificate.trufo_cert[0].domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = var.hosted_zone_id
}

# API Gateway Custom Domain
resource "aws_api_gateway_domain_name" "trufo_domain" {
  count           = var.domain_name != "" ? 1 : 0
  domain_name     = var.domain_name
  regional_certificate_arn = aws_acm_certificate.trufo_cert[0].arn
  security_policy = "TLS_1_2"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  depends_on = [
    aws_acm_certificate_validation.trufo_cert
  ]

  tags = {
    Name = "${var.project_name}-domain"
  }
}

# API Gateway Base Path Mapping
resource "aws_api_gateway_base_path_mapping" "trufo_mapping" {
  count       = var.domain_name != "" ? 1 : 0
  api_id      = aws_api_gateway_rest_api.trufo_api.id
  stage_name  = aws_api_gateway_deployment.trufo_deployment.stage_name
  domain_name = aws_api_gateway_domain_name.trufo_domain[0].domain_name
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

# SES Domain Identity
resource "aws_ses_domain_identity" "trufo_domain" {
  count  = var.ses_domain != "" ? 1 : 0
  domain = var.ses_domain
}

# Route53 Records (conditional)
data "aws_route53_zone" "selected" {
  count   = var.domain_name != "" && var.hosted_zone_id != "" ? 1 : 0
  zone_id = var.hosted_zone_id
}

resource "aws_route53_record" "domain" {
  count   = var.domain_name != "" && var.hosted_zone_id != "" && !var.use_external_dns ? 1 : 0
  zone_id = var.hosted_zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_api_gateway_domain_name.trufo_domain[0].regional_domain_name
    zone_id                = aws_api_gateway_domain_name.trufo_domain[0].regional_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "www_domain" {
  count   = var.domain_name != "" && var.hosted_zone_id != "" && !var.use_external_dns ? 1 : 0
  zone_id = var.hosted_zone_id
  name    = "www.${var.domain_name}"
  type    = "A"

  alias {
    name                   = aws_api_gateway_domain_name.trufo_domain[0].regional_domain_name
    zone_id                = aws_api_gateway_domain_name.trufo_domain[0].regional_zone_id
    evaluate_target_health = false
  }
}