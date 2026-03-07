output "function_url" {
  description = "Lambda Function URL"
  value       = aws_lambda_function_url.trufo_function_url.function_url
}

output "bucket_name" {
  description = "S3 bucket name for object storage"
  value       = aws_s3_bucket.trufo_storage.bucket
}

output "website_url" {
  description = "Website URL (custom domain if configured, otherwise Function URL)"
  value       = var.domain_name != "" ? "https://${var.domain_name}" : aws_lambda_function_url.trufo_function_url.function_url
}

output "github_actions_role_arn" {
  description = "GitHub Actions IAM Role ARN for CI/CD"
  value       = var.github_org != "" && var.github_repo != "" ? aws_iam_role.github_actions_role[0].arn : null
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.trufo_function.function_name
}

output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.trufo_function.arn
}

output "ses_configuration_commands" {
  description = "AWS CLI commands to configure SES"
  value = <<-EOT
    # Verify your email address in Amazon SES
    aws ses verify-email-identity --email-address ${var.from_email}

    # Check verification status
    aws ses get-identity-verification-attributes --identities ${var.from_email}

    # For custom domains, verify the domain
    aws ses verify-domain-identity --domain ${var.domain_name != "" ? replace(var.from_email, "/^[^@]+@/", "") : "yourdomain.com"}
  EOT
}

output "deployment_info" {
  description = "Deployment information summary"
  value = {
    project_name      = var.project_name
    environment       = var.environment
    aws_region        = var.aws_region
    bucket_name       = aws_s3_bucket.trufo_storage.bucket
    function_url      = aws_lambda_function_url.trufo_function_url.function_url
    website_url       = var.domain_name != "" ? "https://${var.domain_name}" : aws_lambda_function_url.trufo_function_url.function_url
    custom_domain     = var.domain_name != "" ? var.domain_name : "Not configured"
    github_actions    = var.github_org != "" && var.github_repo != "" ? "Configured for ${var.github_org}/${var.github_repo}" : "Not configured"
  }
}

output "api_endpoints" {
  description = "API endpoint information"
  value = {
    base_url = aws_lambda_function_url.trufo_function_url.function_url
    endpoints = [
      "GET  / - Main interface",
      "GET  /create - Object creation page",
      "GET  /manage - Object management page",
      "GET  /access/{token} - Object access page",
      "POST /api/objects - Create object",
      "GET  /api/objects - Access object",
      "GET  /api/user-objects - List user objects",
      "DELETE /api/objects - Delete object",
      "POST /api/toggle - Toggle boolean object",
      "POST /api/validate-email - Send email validation",
      "POST /api/verify-code - Verify email code"
    ]
  }
}

output "next_steps" {
  description = "Next steps after deployment"
  value = <<-EOT
    🎉 Deployment completed successfully!

    📋 Next Steps:
    1. Verify your email in SES: aws ses verify-email-identity --email-address ${var.from_email}
    2. Test the application: ${var.domain_name != "" ? "https://${var.domain_name}" : aws_lambda_function_url.trufo_function_url.function_url}
    3. Configure GitHub Actions (if applicable): Set AWS_ROLE_ARN variable to ${var.github_org != "" && var.github_repo != "" ? aws_iam_role.github_actions_role[0].arn : "N/A"}
    4. Request SES production access for high-volume email sending

    🌐 Access URLs:
    - Website: ${var.domain_name != "" ? "https://${var.domain_name}" : aws_lambda_function_url.trufo_function_url.function_url}
    - Create Page: ${var.domain_name != "" ? "https://${var.domain_name}" : aws_lambda_function_url.trufo_function_url.function_url}create
    - Manage Page: ${var.domain_name != "" ? "https://${var.domain_name}" : aws_lambda_function_url.trufo_function_url.function_url}manage
  EOT
}