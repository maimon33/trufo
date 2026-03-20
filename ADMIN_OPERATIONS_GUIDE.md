# 🛡️ Trufo Admin Operations Guide

This guide covers monitoring, alerting, reporting, and emergency controls for Trufo administrators.

## 🚀 Deployment with Monitoring

### Deploy with Admin Features
```bash
sam deploy --parameter-overrides \
  AdminEmail="admin@yourcompany.com" \
  DailyUsageThreshold=1000 \
  MonthlyUsageThreshold=10000 \
  EnableKillSwitch=false
```

### Required Parameters:
- **AdminEmail**: Your email for alerts and reports
- **DailyUsageThreshold**: Alert when daily objects created > threshold
- **MonthlyUsageThreshold**: Alert when monthly objects created > threshold
- **EnableKillSwitch**: Pre-enable kill switch (normally false)

## 📊 Daily Reporting

### What You'll Receive
**Daily email at 8 AM UTC** with:
- 📈 **Usage Metrics**: Objects created/accessed/deleted
- 💾 **Storage Stats**: Total size, active/expired objects
- 🔒 **Security Breakdown**: Objects by security type
- ⚠️ **Error Summary**: Lambda errors and rates
- 📱 **Visual Dashboard**: HTML email with charts

### Sample Daily Report
```
📊 Trufo Daily Report - 2024-01-15

📈 Usage Metrics
├─ Objects Created: 1,247
├─ Objects Accessed: 3,891
├─ Objects Deleted: 234
└─ Active Objects: 8,752

💾 Storage: 1.2 GB (8,752 active, 127 expired)
🔒 Security: 60% None, 30% Notice, 10% TOTP
⚠️ Errors: 0 (0.0/hour)
```

## 🚨 Alert System

### Automatic Alerts Via SNS
You'll receive **immediate email alerts** for:

**1. High Daily Usage** (Default: 1,000+ objects/day)
```
Subject: [ALERT] Trufo High Daily Usage
Body: Daily object creation exceeded 1,000 threshold
Current: 1,247 objects created today
Action: Monitor for abuse or increase limits
```

**2. High Monthly Usage** (Default: 10,000+ objects/month)
```
Subject: [ALERT] Trufo High Monthly Usage
Body: Monthly object creation exceeded 10,000 threshold
Current: 12,450 objects created this month
Action: Consider usage plan upgrades
```

**3. High Error Rate** (10+ errors in 10 minutes)
```
Subject: [ALERT] Trufo High Error Rate
Body: Lambda function experiencing high error rate
Current: 15 errors in last 10 minutes
Action: Check CloudWatch logs immediately
```

### Customize Alert Thresholds
```bash
# Update thresholds
aws cloudformation update-stack \
  --stack-name trufo-app \
  --use-previous-template \
  --parameters ParameterKey=DailyUsageThreshold,ParameterValue=2000 \
              ParameterKey=MonthlyUsageThreshold,ParameterValue=20000
```

## 📈 Real-Time Monitoring

### CloudWatch Metrics Dashboard
Access via CloudFormation output: `MonitoringDashboard`
```bash
aws cloudformation describe-stacks --stack-name trufo-app \
  --query 'Stacks[0].Outputs[?OutputKey==`MonitoringDashboard`].OutputValue'
```

### Key Metrics to Monitor:
- **TotalObjectCreated**: Objects created per day/hour
- **TotalObjectAccessed**: Access frequency
- **ObjectsBySize**: Storage usage by size category
- **ObjectsBySecurity**: Security type distribution
- **ObjectCreatedByUser**: Anonymous user patterns
- **Lambda Duration**: Performance metrics
- **Lambda Errors**: Error rates

### Manual Metric Queries
```bash
# Get daily object creation
aws cloudwatch get-metric-statistics \
  --namespace Trufo \
  --metric-name TotalObjectCreated \
  --start-time $(date -d '24 hours ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Sum

# Get current error rate
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=trufo-app-TrufoLambdaFunction-XXXXX \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

## 🔴 Emergency Kill Switch

### Option 1: API Gateway Throttling (Recommended)
**Graceful degradation - returns 429 errors**

```bash
# GET USAGE PLAN ID
USAGE_PLAN_ID=$(aws cloudformation describe-stacks \
  --stack-name trufo-app \
  --query 'Stacks[0].Outputs[?OutputKey==`UsagePlanId`].OutputValue' \
  --output text)

# EMERGENCY STOP
aws apigateway update-usage-plan \
  --usage-plan-id $USAGE_PLAN_ID \
  --patch-ops op=replace,path=/throttle/rateLimit,value=0 \
           op=replace,path=/throttle/burstLimit,value=0

# RE-ENABLE (normal limits)
aws apigateway update-usage-plan \
  --usage-plan-id $USAGE_PLAN_ID \
  --patch-ops op=replace,path=/throttle/rateLimit,value=5000 \
           op=replace,path=/throttle/burstLimit,value=10000
```

### Option 2: Lambda Concurrency (Nuclear)
**Blocks ALL Lambda executions**

```bash
# GET FUNCTION NAME
FUNCTION_NAME=$(aws cloudformation describe-stacks \
  --stack-name trufo-app \
  --query 'Stacks[0].Outputs[?OutputKey==`TrufoLambdaFunction`].OutputValue' \
  --output text)

# EMERGENCY STOP
aws lambda put-reserved-concurrency-config \
  --function-name $FUNCTION_NAME \
  --reserved-concurrent-executions 0

# RE-ENABLE
aws lambda delete-reserved-concurrency-config \
  --function-name $FUNCTION_NAME
```

### Pre-Configured Kill Switch
Deploy with `EnableKillSwitch=true` to pre-configure throttling to 0:

```bash
sam deploy --parameter-overrides EnableKillSwitch=true
```

## 🔍 Operational Commands

### Get Current Status
```bash
# Stack status
aws cloudformation describe-stacks --stack-name trufo-app \
  --query 'Stacks[0].StackStatus'

# Function status
aws lambda get-function --function-name trufo-app-TrufoLambdaFunction-XXXXX \
  --query 'Configuration.State'

# Usage plan limits
aws apigateway get-usage-plan --usage-plan-id $USAGE_PLAN_ID
```

### Check Service Health
```bash
# Test API endpoint
curl -s "https://your-domain.com/api/check-health" || echo "Service Down"

# Check recent errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/trufo-app-TrufoLambdaFunction-XXXXX \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --filter-pattern "ERROR"
```

### Storage Management
```bash
# Check S3 bucket size
aws s3 ls s3://trufo-storage-bucket --recursive --human-readable --summarize

# Count objects by type
aws s3api list-objects-v2 --bucket trufo-storage-bucket \
  --query 'length(Contents[?contains(Key, `strings/`)])'

# Cleanup expired objects manually
aws lambda invoke --function-name trufo-app-TrufoLambdaFunction-XXXXX \
  --payload '{"httpMethod":"POST","path":"/api/cleanup"}' \
  response.json
```

## ⚡ Performance Optimization

### Scale Up for High Traffic
```bash
# Increase Lambda memory (faster processing)
aws lambda update-function-configuration \
  --function-name trufo-app-TrufoLambdaFunction-XXXXX \
  --memory-size 1024

# Increase API Gateway limits
aws apigateway update-usage-plan \
  --usage-plan-id $USAGE_PLAN_ID \
  --patch-ops op=replace,path=/throttle/rateLimit,value=10000 \
           op=replace,path=/throttle/burstLimit,value=20000
```

### Monitor Performance
```bash
# Check Lambda duration trends
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=trufo-app-TrufoLambdaFunction-XXXXX \
  --start-time $(date -d '1 day ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Average,Maximum
```

## 🔧 Troubleshooting

### Common Issues:

**High Error Rate**
1. Check CloudWatch logs for specific errors
2. Verify S3 bucket permissions
3. Check SES sending limits
4. Monitor Lambda memory usage

**Email Delivery Issues**
1. Verify SES domain authentication
2. Check DNS records (SPF, DKIM, DMARC)
3. Monitor SES reputation metrics
4. Check suppression lists

**Performance Issues**
1. Increase Lambda memory/timeout
2. Monitor S3 request patterns
3. Check API Gateway throttling
4. Review CloudWatch insights

**Kill Switch Not Working**
1. Verify Usage Plan ID is correct
2. Check API Gateway stage deployment
3. Confirm IAM permissions for updates
4. Test with direct Lambda invocation

### Emergency Contacts
```bash
# Get all CloudFormation outputs (includes URLs, IDs, instructions)
aws cloudformation describe-stacks --stack-name trufo-app \
  --query 'Stacks[0].Outputs'

# Get recent CloudWatch alarms
aws cloudwatch describe-alarms --state-value ALARM \
  --query 'MetricAlarms[?contains(AlarmName, `trufo`)]'
```

## 📋 Operational Checklist

### Daily Tasks:
- [ ] Review daily report email
- [ ] Check CloudWatch dashboard
- [ ] Monitor error rates < 1%
- [ ] Verify backup/cleanup jobs

### Weekly Tasks:
- [ ] Review usage trends
- [ ] Check storage growth rate
- [ ] Update alert thresholds if needed
- [ ] Test kill switch procedures

### Monthly Tasks:
- [ ] Review and update usage limits
- [ ] Analyze user behavior patterns
- [ ] Update emergency procedures
- [ ] Security audit and review

### Emergency Procedures:
1. **Immediate**: Activate kill switch
2. **Within 5 min**: Identify root cause
3. **Within 15 min**: Implement fix or containment
4. **Within 1 hour**: Full service restoration
5. **Within 24 hours**: Post-incident review

---

## 🆘 Emergency Hotline

**Quick Kill Switch:**
```bash
# Copy-paste this in emergency:
USAGE_PLAN_ID=$(aws cloudformation describe-stacks --stack-name trufo-app --query 'Stacks[0].Outputs[?OutputKey==`UsagePlanId`].OutputValue' --output text) && aws apigateway update-usage-plan --usage-plan-id $USAGE_PLAN_ID --patch-ops op=replace,path=/throttle/rateLimit,value=0
```

**Service Status Dashboard:**
- CloudWatch: Check `MonitoringDashboard` output
- Logs: `/aws/lambda/trufo-app-TrufoLambdaFunction-*`
- Alerts: Check email + SNS topic
- Metrics: Trufo namespace in CloudWatch

Your Trufo deployment now has **enterprise-grade monitoring and operational controls**! 🛡️🚀