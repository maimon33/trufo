output "api_gateway_url" {
  description = "API Gateway URL"
  value       = "https://${aws_api_gateway_rest_api.trufo_api.id}.execute-api.${var.aws_region}.amazonaws.com/prod"
}

output "bucket_name" {
  description = "S3 bucket name for object storage"
  value       = aws_s3_bucket.trufo_storage.bucket
}

output "website_url" {
  description = "Website URL (custom domain if configured, otherwise API Gateway URL)"
  value       = var.domain_name != "" ? "https://${var.domain_name}" : "https://${aws_api_gateway_rest_api.trufo_api.id}.execute-api.${var.aws_region}.amazonaws.com/prod"
}

output "dns_target_external" {
  description = "DNS target for external DNS providers"
  value       = var.use_external_dns && var.domain_name != "" ? {
    a_record = length(aws_api_gateway_domain_name.trufo_domain) > 0 ? aws_api_gateway_domain_name.trufo_domain[0].regional_domain_name : null
    cname_record = "https://${aws_api_gateway_rest_api.trufo_api.id}.execute-api.${var.aws_region}.amazonaws.com"
  } : null
}

output "ssl_certificate_validation" {
  description = "SSL Certificate DNS validation records (for external DNS)"
  value       = var.use_external_dns && var.domain_name != "" ? "Check ACM console for DNS validation records" : null
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

output "ses_domain_verification" {
  description = "SES domain verification information"
  value = var.ses_domain != "" ? {
    domain = var.ses_domain
    verification_token = aws_ses_domain_identity.trufo_domain[0].verification_token
    dns_record = "Add TXT record: _amazonses.${var.ses_domain} with value ${aws_ses_domain_identity.trufo_domain[0].verification_token}"
  } : null
}

output "deployment_info" {
  description = "Deployment information summary"
  value = {
    project_name      = var.project_name
    environment       = var.environment
    aws_region        = var.aws_region
    bucket_name       = aws_s3_bucket.trufo_storage.bucket
    api_gateway_url   = "https://${aws_api_gateway_rest_api.trufo_api.id}.execute-api.${var.aws_region}.amazonaws.com/prod"
    website_url       = var.domain_name != "" ? "https://${var.domain_name}" : "https://${aws_api_gateway_rest_api.trufo_api.id}.execute-api.${var.aws_region}.amazonaws.com/prod"
    custom_domain     = var.domain_name != "" ? var.domain_name : "Not configured"
    github_actions    = var.github_org != "" && var.github_repo != "" ? "Configured for ${var.github_org}/${var.github_repo}" : "Not configured"
  }
}

output "api_endpoints" {
  description = "API endpoint information"
  value = {
    base_url = var.domain_name != "" ? "https://${var.domain_name}" : "https://${aws_api_gateway_rest_api.trufo_api.id}.execute-api.${var.aws_region}.amazonaws.com/prod"
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
    ${var.ses_domain != "" ? "2. Add SES domain verification DNS record: _amazonses.${var.ses_domain} TXT ${aws_ses_domain_identity.trufo_domain[0].verification_token}" : ""}
    ${var.ses_domain != "" ? "3" : "2"}. Test the application: ${var.domain_name != "" ? "https://${var.domain_name}" : "https://${aws_api_gateway_rest_api.trufo_api.id}.execute-api.${var.aws_region}.amazonaws.com/prod"}
    ${var.ses_domain != "" ? "4" : "3"}. Configure GitHub Actions (if applicable): Set AWS_ROLE_ARN variable to ${var.github_org != "" && var.github_repo != "" ? aws_iam_role.github_actions_role[0].arn : "N/A"}
    ${var.ses_domain != "" ? "5" : "4"}. Request SES production access for high-volume email sending
    ${var.use_external_dns && var.domain_name != "" ? "${var.ses_domain != "" ? "6" : "5"}. Configure DNS with your external provider using the DNS targets from outputs" : ""}

    🌐 Access URLs:
    - Website: ${var.domain_name != "" ? "https://${var.domain_name}" : "https://${aws_api_gateway_rest_api.trufo_api.id}.execute-api.${var.aws_region}.amazonaws.com/prod"}
    - Create Page: ${var.domain_name != "" ? "https://${var.domain_name}" : "https://${aws_api_gateway_rest_api.trufo_api.id}.execute-api.${var.aws_region}.amazonaws.com/prod"}/create
    - Manage Page: ${var.domain_name != "" ? "https://${var.domain_name}" : "https://${aws_api_gateway_rest_api.trufo_api.id}.execute-api.${var.aws_region}.amazonaws.com/prod"}/manage
  EOT
}