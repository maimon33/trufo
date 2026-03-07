variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name of the project (used for resource naming)"
  type        = string
  default     = "trufo"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "s3_bucket_name" {
  description = "S3 bucket name for object storage (leave empty for auto-generated)"
  type        = string
  default     = ""
}

variable "from_email" {
  description = "Email address for SES notifications (must be verified in SES)"
  type        = string
}

variable "domain_name" {
  description = "Custom domain name for the application (optional)"
  type        = string
  default     = ""
}

variable "hosted_zone_id" {
  description = "Route53 hosted zone ID for the domain (optional)"
  type        = string
  default     = ""
}

variable "github_org" {
  description = "GitHub organization or username for OIDC trust policy"
  type        = string
  default     = ""
}

variable "github_repo" {
  description = "GitHub repository name for OIDC trust policy"
  type        = string
  default     = ""
}

variable "create_github_oidc" {
  description = "Whether to create GitHub OIDC provider (set to false if it already exists)"
  type        = bool
  default     = true
}

variable "existing_github_oidc_arn" {
  description = "ARN of existing GitHub OIDC provider (used when create_github_oidc is false)"
  type        = string
  default     = ""
}

variable "log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 14
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 512
}