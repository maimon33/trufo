"""
Daily reporting and monitoring for Trufo
"""

import json
import boto3
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
import hashlib

# AWS clients
cloudwatch = boto3.client('cloudwatch')
s3_client = boto3.client('s3')
ses_client = boto3.client('ses')

# Configuration
BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'trufo-storage')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', '')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@trufo.com')
SES_CONFIG_SET = os.environ.get('SES_CONFIGURATION_SET', '')
STACK_NAME = os.environ.get('STACK_NAME', 'trufo-app')
LAMBDA_FUNCTION_NAME = os.environ.get('LAMBDA_FUNCTION_NAME', '')
API_GATEWAY_NAME = os.environ.get('API_GATEWAY_NAME', STACK_NAME)

# Lambda memory in MB (must match template.yaml TrufoLambdaFunction MemorySize)
LAMBDA_MEMORY_MB = 512

def daily_report_handler(event, context):
    """Generate and send daily usage report"""
    print(f"Generating daily report: {json.dumps(event)}")

    try:
        # Get metrics for the last 24 hours
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=1)

        storage = get_storage_stats()
        infra = get_infra_metrics(start_time, end_time)
        report_data = {
            'date': end_time.strftime('%Y-%m-%d'),
            'period': f"{start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%Y-%m-%d %H:%M')} UTC",
            'metrics': get_usage_metrics(start_time, end_time),
            'storage': storage,
            'errors': get_error_stats(start_time, end_time),
            'top_users': get_top_users_anonymous(start_time, end_time),
            'infra': infra,
            'costs': estimate_costs(infra, storage)
        }

        # Skip report if all key metrics are zero (no activity)
        m = report_data['metrics']
        infra = report_data['infra']
        all_zero = (
            m.get('objects_created', 0) == 0 and
            m.get('objects_accessed', 0) == 0 and
            m.get('objects_deleted', 0) == 0 and
            m.get('objects_toggled', 0) == 0 and
            infra.get('lambda_invocations', 0) == 0 and
            infra.get('api_requests', 0) == 0
        )

        # Send report email
        if ADMIN_EMAIL and not all_zero:
            send_daily_report(report_data)
            print(f"Daily report sent to {ADMIN_EMAIL}")
        elif all_zero:
            print("Skipping report: all metrics are zero")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': 'Daily report generated successfully',
                'metrics': report_data['metrics']
            })
        }

    except Exception as e:
        print(f"Error generating daily report: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def get_usage_metrics(start_time: datetime, end_time: datetime) -> Dict[str, Any]:
    """Get usage metrics from CloudWatch"""
    try:
        # Get basic metrics
        metrics = {}

        metric_queries = [
            ('TotalObjectCreated', 'Objects Created'),
            ('TotalObjectAccessed', 'Objects Accessed'),
            ('TotalObjectDeleted', 'Objects Deleted'),
            ('TotalObjectToggled', 'Objects Toggled')
        ]

        for metric_name, display_name in metric_queries:
            try:
                response = cloudwatch.get_metric_statistics(
                    Namespace='Trufo',
                    MetricName=metric_name,
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=86400,  # 24 hours
                    Statistics=['Sum']
                )

                total = sum(point['Sum'] for point in response['Datapoints'])
                metrics[display_name.lower().replace(' ', '_')] = int(total)

            except Exception as e:
                print(f"Error getting metric {metric_name}: {e}")
                metrics[display_name.lower().replace(' ', '_')] = 0

        # Get metrics by type
        metrics['by_type'] = get_metrics_by_dimension('ObjectType', start_time, end_time)
        metrics['by_security'] = get_metrics_by_dimension('SecurityType', start_time, end_time)

        return metrics

    except Exception as e:
        print(f"Error getting usage metrics: {e}")
        return {}

def get_metrics_by_dimension(dimension_name: str, start_time: datetime, end_time: datetime) -> Dict[str, int]:
    """Get metrics broken down by dimension"""
    try:
        # This is a simplified approach - in production, you'd want to query specific dimensions
        result = {}

        # Common dimension values
        if dimension_name == 'ObjectType':
            dimension_values = ['string', 'file']
        elif dimension_name == 'SecurityType':
            dimension_values = ['none', 'notice', 'totp']
        else:
            return {}

        for value in dimension_values:
            try:
                response = cloudwatch.get_metric_statistics(
                    Namespace='Trufo',
                    MetricName='ObjectCreatedByType' if dimension_name == 'ObjectType' else 'ObjectCreatedBySecurity',
                    Dimensions=[{
                        'Name': dimension_name,
                        'Value': value
                    }],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=86400,
                    Statistics=['Sum']
                )

                total = sum(point['Sum'] for point in response['Datapoints'])
                result[value] = int(total)

            except Exception as e:
                print(f"Error getting dimension {dimension_name}={value}: {e}")
                result[value] = 0

        return result

    except Exception as e:
        print(f"Error getting metrics by dimension {dimension_name}: {e}")
        return {}

def get_storage_stats() -> Dict[str, Any]:
    """Get S3 storage statistics"""
    try:
        stats = {
            'total_objects': 0,
            'active_objects': 0,
            'expired_objects': 0,
            'storage_size_mb': 0
        }

        # List all objects in bucket
        paginator = s3_client.get_paginator('list_objects_v2')
        current_time = int(datetime.utcnow().timestamp() * 1000)

        for page in paginator.paginate(Bucket=BUCKET_NAME):
            if 'Contents' not in page:
                continue

            for obj in page['Contents']:
                # Skip token files and directories
                if obj['Key'].startswith('tokens/') or obj['Key'].endswith('/'):
                    continue

                stats['total_objects'] += 1
                stats['storage_size_mb'] += obj['Size'] / (1024 * 1024)

                # Check if object is expired by reading its metadata
                try:
                    obj_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=obj['Key'])
                    obj_data = json.loads(obj_response['Body'].read())

                    if obj_data.get('ttl', 0) > current_time:
                        stats['active_objects'] += 1
                    else:
                        stats['expired_objects'] += 1

                except Exception:
                    # If we can't read the object, assume it's expired
                    stats['expired_objects'] += 1

        # Round storage size
        stats['storage_size_mb'] = round(stats['storage_size_mb'], 2)

        return stats

    except Exception as e:
        print(f"Error getting storage stats: {e}")
        return {
            'total_objects': 0,
            'active_objects': 0,
            'expired_objects': 0,
            'storage_size_mb': 0,
            'error': str(e)
        }

def get_error_stats(start_time: datetime, end_time: datetime) -> Dict[str, Any]:
    """Get Lambda error statistics"""
    try:
        # Get Lambda errors
        lambda_errors = cloudwatch.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Errors',
            Dimensions=[{
                'Name': 'FunctionName',
                'Value': f'{STACK_NAME}-TrufoLambdaFunction-'  # Partial match
            }],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,  # 1 hour
            Statistics=['Sum']
        )

        total_errors = sum(point['Sum'] for point in lambda_errors['Datapoints'])

        return {
            'lambda_errors': int(total_errors),
            'error_rate_per_hour': round(total_errors / 24, 2) if total_errors > 0 else 0
        }

    except Exception as e:
        print(f"Error getting error stats: {e}")
        return {
            'lambda_errors': 0,
            'error_rate_per_hour': 0,
            'error': str(e)
        }

def get_top_users_anonymous(start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
    """Get top anonymous users (8-char hashes only)"""
    try:
        # This would require querying CloudWatch Logs or maintaining user metrics
        # For now, return placeholder
        return [
            {'user_hash': 'a1b2c3d4', 'objects_created': 'N/A'},
            {'user_hash': 'x9y8z7w6', 'objects_created': 'N/A'}
        ]

    except Exception as e:
        print(f"Error getting top users: {e}")
        return []

def get_infra_metrics(start_time: datetime, end_time: datetime) -> Dict[str, Any]:
    """Fetch Lambda, API Gateway, and email metrics from CloudWatch"""
    metrics = {}

    # Lambda invocations + duration
    if LAMBDA_FUNCTION_NAME:
        dims = [{'Name': 'FunctionName', 'Value': LAMBDA_FUNCTION_NAME}]
        try:
            r = cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda', MetricName='Invocations',
                Dimensions=dims, StartTime=start_time, EndTime=end_time,
                Period=86400, Statistics=['Sum'])
            metrics['lambda_invocations'] = int(sum(p['Sum'] for p in r['Datapoints']))
        except Exception as e:
            print(f"Error getting Lambda invocations: {e}")
            metrics['lambda_invocations'] = 0

        try:
            r = cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda', MetricName='Duration',
                Dimensions=dims, StartTime=start_time, EndTime=end_time,
                Period=86400, Statistics=['Sum'])
            metrics['lambda_duration_ms'] = round(sum(p['Sum'] for p in r['Datapoints']))
        except Exception as e:
            print(f"Error getting Lambda duration: {e}")
            metrics['lambda_duration_ms'] = 0
    else:
        metrics['lambda_invocations'] = 0
        metrics['lambda_duration_ms'] = 0

    # API Gateway request count (REST API v1 uses ApiName dimension)
    try:
        r = cloudwatch.get_metric_statistics(
            Namespace='AWS/ApiGateway', MetricName='Count',
            Dimensions=[{'Name': 'ApiName', 'Value': API_GATEWAY_NAME}],
            StartTime=start_time, EndTime=end_time,
            Period=86400, Statistics=['Sum'])
        metrics['api_requests'] = int(sum(p['Sum'] for p in r['Datapoints']))
    except Exception as e:
        print(f"Error getting API Gateway count: {e}")
        metrics['api_requests'] = 0

    # Emails sent — from our custom Trufo namespace
    try:
        r = cloudwatch.get_metric_statistics(
            Namespace='Trufo', MetricName='TotalEmailSent',
            StartTime=start_time, EndTime=end_time,
            Period=86400, Statistics=['Sum'])
        metrics['emails_sent'] = int(sum(p['Sum'] for p in r['Datapoints']))
    except Exception as e:
        print(f"Error getting email metrics: {e}")
        metrics['emails_sent'] = 0

    # Email breakdown by type
    email_breakdown = {}
    for email_type in ['verification', 'access_alert', 'magic_link']:
        try:
            r = cloudwatch.get_metric_statistics(
                Namespace='Trufo', MetricName='EmailSentByType',
                Dimensions=[{'Name': 'EmailType', 'Value': email_type}],
                StartTime=start_time, EndTime=end_time,
                Period=86400, Statistics=['Sum'])
            email_breakdown[email_type] = int(sum(p['Sum'] for p in r['Datapoints']))
        except Exception:
            email_breakdown[email_type] = 0
    metrics['emails_by_type'] = email_breakdown

    return metrics


def estimate_costs(infra: Dict[str, Any], storage: Dict[str, Any]) -> Dict[str, Any]:
    """Estimate daily AWS costs. Prices are us-east-1 on-demand as of 2025."""
    costs = {}

    # Lambda: $0.20 per 1M requests + $0.0000166667 per GB-second
    invocations = infra.get('lambda_invocations', 0)
    duration_ms = infra.get('lambda_duration_ms', 0)
    gb_seconds = (duration_ms / 1000) * (LAMBDA_MEMORY_MB / 1024)
    costs['lambda'] = round(invocations * 0.0000002 + gb_seconds * 0.0000166667, 6)

    # API Gateway REST: $3.50 per million calls
    costs['api_gateway'] = round(infra.get('api_requests', 0) * 0.0000035, 6)

    # S3 storage: $0.023 per GB/month → daily fraction
    storage_gb = storage.get('storage_size_mb', 0) / 1024
    costs['s3_storage'] = round(storage_gb * 0.023 / 30, 6)

    # SES: $0.10 per 1000 emails
    costs['ses'] = round(infra.get('emails_sent', 0) * 0.0001, 6)

    costs['total'] = round(sum(v for v in costs.values()), 6)
    return costs


def send_daily_report(report_data: Dict[str, Any]):
    """Send daily report via email"""
    try:
        subject = f"Trufo Daily Report - {report_data['date']}"

        # Generate HTML report
        html_body = generate_report_html(report_data)
        text_body = generate_report_text(report_data)

        # Email parameters
        email_params = {
            'Source': f"Trufo Admin Reports <{FROM_EMAIL}>",
            'Destination': {'ToAddresses': [ADMIN_EMAIL]},
            'Message': {
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': text_body,
                        'Charset': 'UTF-8'
                    },
                    'Html': {
                        'Data': html_body,
                        'Charset': 'UTF-8'
                    }
                }
            },
            'Tags': [
                {'Name': 'EmailType', 'Value': 'DailyReport'},
                {'Name': 'Application', 'Value': 'TrufoAdmin'}
            ]
        }

        # Add configuration set if configured
        if SES_CONFIG_SET:
            email_params['ConfigurationSetName'] = SES_CONFIG_SET

        response = ses_client.send_email(**email_params)
        print(f"Daily report email sent. MessageId: {response['MessageId']}")

    except Exception as e:
        print(f"Error sending daily report email: {e}")
        raise

def generate_report_html(data: Dict[str, Any]) -> str:
    """Generate HTML report"""
    metrics = data['metrics']
    storage = data['storage']
    errors = data['errors']
    infra = data.get('infra', {})
    costs = data.get('costs', {})

    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Trufo Daily Report</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; text-align: center; margin-bottom: 30px; }}
            .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
            .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 6px; text-align: center; }}
            .metric-value {{ font-size: 2em; font-weight: bold; color: #667eea; margin-bottom: 5px; }}
            .metric-label {{ color: #666; font-size: 0.9em; }}
            .section {{ margin: 30px 0; }}
            .section h2 {{ color: #495057; border-bottom: 2px solid #e9ecef; padding-bottom: 10px; }}
            .alert {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .error {{ background: #f8d7da; border: 1px solid #f5c6cb; }}
            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
            th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #dee2e6; }}
            th {{ background: #f8f9fa; font-weight: 600; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Trufo Daily Report</h1>
            <p><strong>Report Period:</strong> {data['period']}</p>

            <div class="section">
                <h2>📈 Usage Metrics</h2>
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-value">{metrics.get('objects_created', 0)}</div>
                        <div class="metric-label">Objects Created</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{metrics.get('objects_accessed', 0)}</div>
                        <div class="metric-label">Objects Accessed</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{metrics.get('objects_deleted', 0)}</div>
                        <div class="metric-label">Objects Deleted</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{storage.get('active_objects', 0)}</div>
                        <div class="metric-label">Active Objects</div>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>💾 Storage Statistics</h2>
                <table>
                    <tr><th>Metric</th><th>Value</th></tr>
                    <tr><td>Total Objects</td><td>{storage.get('total_objects', 0)}</td></tr>
                    <tr><td>Active Objects</td><td>{storage.get('active_objects', 0)}</td></tr>
                    <tr><td>Expired Objects</td><td>{storage.get('expired_objects', 0)}</td></tr>
                    <tr><td>Storage Size</td><td>{storage.get('storage_size_mb', 0)} MB</td></tr>
                </table>
            </div>

            <div class="section">
                <h2>🔒 Security Breakdown</h2>
                <table>
                    <tr><th>Security Type</th><th>Objects Created</th></tr>
    '''

    # Add security breakdown
    for sec_type, count in metrics.get('by_security', {}).items():
        html += f'<tr><td>{sec_type.title()}</td><td>{count}</td></tr>'

    html += f'''
                </table>
            </div>

            <div class="section">
                <h2>⚠️ Error Summary</h2>
                <div class="metric-grid">
                    <div class="metric-card {'error' if errors.get('lambda_errors', 0) > 0 else ''}">
                        <div class="metric-value">{errors.get('lambda_errors', 0)}</div>
                        <div class="metric-label">Lambda Errors</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{errors.get('error_rate_per_hour', 0)}</div>
                        <div class="metric-label">Errors/Hour</div>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>🖥️ Infrastructure Usage (24h)</h2>
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-value">{infra.get('lambda_invocations', 0):,}</div>
                        <div class="metric-label">Lambda Invocations</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{round(infra.get('lambda_duration_ms', 0) / 1000, 1):,}s</div>
                        <div class="metric-label">Lambda Total Duration</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{infra.get('api_requests', 0):,}</div>
                        <div class="metric-label">API Gateway Requests</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{infra.get('emails_sent', 0):,}</div>
                        <div class="metric-label">Emails Sent</div>
                    </div>
                </div>
                <table>
                    <tr><th>Email Type</th><th>Count</th></tr>
    '''

    for etype, count in infra.get('emails_by_type', {}).items():
        html += f'<tr><td>{etype.replace("_", " ").title()}</td><td>{count}</td></tr>'

    html += f'''
                </table>
            </div>

            <div class="section">
                <h2>💰 Estimated Cost (24h)</h2>
                <p style="color:#888; font-size:0.85em; margin-bottom:12px;">Based on us-east-1 on-demand pricing. Estimates only — actual billing may differ.</p>
                <table>
                    <tr><th>Service</th><th>Estimated Cost (USD)</th></tr>
                    <tr><td>Lambda</td><td>${costs.get('lambda', 0):.6f}</td></tr>
                    <tr><td>API Gateway</td><td>${costs.get('api_gateway', 0):.6f}</td></tr>
                    <tr><td>S3 Storage</td><td>${costs.get('s3_storage', 0):.6f}</td></tr>
                    <tr><td>SES (emails)</td><td>${costs.get('ses', 0):.6f}</td></tr>
                    <tr style="font-weight:bold; background:#f8f9fa;"><td>Total</td><td>${costs.get('total', 0):.6f}</td></tr>
                </table>
                <p style="color:#888; font-size:0.8em; margin-top:8px;">
                    Monthly projection: <strong>${round(costs.get('total', 0) * 30, 4):.4f}</strong>
                    &nbsp;|&nbsp; Free tier not factored in.
                </p>
            </div>

            <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #dee2e6; text-align: center; color: #6c757d;">
                <p>Generated on {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC</p>
                <p>Trufo Admin Dashboard | Stack: {STACK_NAME}</p>
            </div>
        </div>
    </body>
    </html>
    '''

    return html

def generate_report_text(data: Dict[str, Any]) -> str:
    """Generate plain text report"""
    metrics = data['metrics']
    storage = data['storage']
    errors = data['errors']
    infra = data.get('infra', {})
    costs = data.get('costs', {})

    text = f'''
TRUFO DAILY REPORT
==================

Report Period: {data['period']}

USAGE METRICS
-------------
Objects Created: {metrics.get('objects_created', 0)}
Objects Accessed: {metrics.get('objects_accessed', 0)}
Objects Deleted: {metrics.get('objects_deleted', 0)}
Objects Toggled: {metrics.get('objects_toggled', 0)}

STORAGE STATISTICS
------------------
Total Objects: {storage.get('total_objects', 0)}
Active Objects: {storage.get('active_objects', 0)}
Expired Objects: {storage.get('expired_objects', 0)}
Storage Size: {storage.get('storage_size_mb', 0)} MB

SECURITY BREAKDOWN
------------------
'''

    for sec_type, count in metrics.get('by_security', {}).items():
        text += f"{sec_type.title()}: {count}\n"

    text += f'''
ERROR SUMMARY
-------------
Lambda Errors: {errors.get('lambda_errors', 0)}
Error Rate: {errors.get('error_rate_per_hour', 0)} errors/hour

INFRASTRUCTURE USAGE (24h)
--------------------------
Lambda Invocations: {infra.get('lambda_invocations', 0):,}
Lambda Total Duration: {round(infra.get('lambda_duration_ms', 0) / 1000, 1):,}s
API Gateway Requests: {infra.get('api_requests', 0):,}
Emails Sent: {infra.get('emails_sent', 0):,}
'''

    for etype, count in infra.get('emails_by_type', {}).items():
        text += f"  {etype.replace('_', ' ').title()}: {count}\n"

    text += f'''
ESTIMATED COST (24h, us-east-1)
--------------------------------
Lambda:       ${costs.get('lambda', 0):.6f}
API Gateway:  ${costs.get('api_gateway', 0):.6f}
S3 Storage:   ${costs.get('s3_storage', 0):.6f}
SES:          ${costs.get('ses', 0):.6f}
Total:        ${costs.get('total', 0):.6f}
Monthly est.: ${round(costs.get('total', 0) * 30, 4):.4f}
(Free tier not factored in)

---
Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC
Stack: {STACK_NAME}
    '''

    return text