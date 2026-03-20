# 📧 SES Email Deliverability Setup Guide

After deploying Trufo with a custom domain, follow this guide to configure DNS records for optimal email deliverability and avoid spam filters.

## 🎯 Quick Overview

Your Trufo deployment now includes:
- ✅ **DKIM signing** enabled
- ✅ **SES Configuration Set** for reputation tracking
- ✅ **TLS enforcement** for secure email delivery
- ✅ **Email tagging** for analytics

## 📋 Required DNS Records

After deployment, add these DNS records to your domain:

### 1. Domain Verification (Required)
```
Type: TXT
Name: _amazonses.yourdomain.com
Value: [Check CloudFormation outputs: SESDomainDNSRecord]
```

### 2. SPF Record (Highly Recommended)
```
Type: TXT
Name: yourdomain.com
Value: "v=spf1 include:amazonses.com ~all"
```

### 3. DMARC Record (Recommended)
```
Type: TXT
Name: _dmarc.yourdomain.com
Value: "v=DMARC1; p=quarantine; rua=mailto:dmarc-reports@yourdomain.com; ruf=mailto:dmarc-failures@yourdomain.com; fo=1"
```

### 4. DKIM Records (Auto-generated - Required)
After domain verification, AWS SES will provide 3 CNAME records:
```
Type: CNAME
Name: [string1]._domainkey.yourdomain.com
Value: [string1].dkim.amazonses.com

Type: CNAME
Name: [string2]._domainkey.yourdomain.com
Value: [string2].dkim.amazonses.com

Type: CNAME
Name: [string3]._domainkey.yourdomain.com
Value: [string3].dkim.amazonses.com
```

## 🚀 Step-by-Step Setup

### Step 1: Get DNS Values from CloudFormation
```bash
# Get domain verification token
aws cloudformation describe-stacks --stack-name trufo-app \
  --query 'Stacks[0].Outputs[?OutputKey==`SESDomainDNSRecord`].OutputValue' --output text

# Get complete DNS recommendations
aws cloudformation describe-stacks --stack-name trufo-app \
  --query 'Stacks[0].Outputs[?OutputKey==`RecommendedDNSRecords`].OutputValue' --output text
```

### Step 2: Add Records to Your DNS Provider

#### For Cloudflare:
1. Go to DNS → Records
2. Add each record from the output above
3. Set TTL to "Auto" or 300 seconds

#### For Route53:
1. Go to Hosted Zones → Your Domain
2. Create Record Set for each DNS record
3. Use TTL of 300 seconds

#### For Other Providers:
1. Access your DNS management console
2. Add TXT and CNAME records as specified
3. Use lowest available TTL (usually 300-600 seconds)

### Step 3: Verify Domain in SES
```bash
# Check verification status
aws ses get-identity-verification-attributes --identities yourdomain.com

# Wait for "Success" status before proceeding
```

### Step 4: Get DKIM Records
```bash
# Get DKIM tokens after domain verification
aws ses get-identity-dkim-attributes --identities yourdomain.com
```

### Step 5: Add DKIM CNAME Records
Use the tokens from Step 4 to create the 3 DKIM CNAME records in your DNS.

## 🔍 Verification Commands

### Check Domain Verification
```bash
aws ses get-identity-verification-attributes --identities yourdomain.com \
  --query 'VerificationAttributes.*.VerificationStatus' --output text
```

### Check DKIM Status
```bash
aws ses get-identity-dkim-attributes --identities yourdomain.com \
  --query 'DkimAttributes.*.DkimVerificationStatus' --output text
```

### Test Email Deliverability
```bash
# Send test email
aws ses send-email \
  --source "noreply@yourdomain.com" \
  --destination "ToAddresses=your-test-email@gmail.com" \
  --message "Subject={Data='Test from Trufo'},Body={Text={Data='Test message'}}"
```

## 📊 Monitor Email Performance

### SES Sending Statistics
```bash
aws ses get-send-statistics
```

### Configuration Set Events
```bash
aws ses describe-configuration-set --configuration-set-name trufo-app-trufo-config-set
```

### Reputation Tracking
- Monitor bounce rates (keep < 5%)
- Monitor complaint rates (keep < 0.1%)
- Check suppression lists regularly

## 🛡️ Security Best Practices

### 1. SPF Record Explained
- `v=spf1` - SPF version 1
- `include:amazonses.com` - Allow SES to send
- `~all` - Soft fail for others (recommended for new domains)
- Use `+all` for strict enforcement after testing

### 2. DMARC Policy Levels
- `p=none` - Monitor only (for testing)
- `p=quarantine` - Send suspicious emails to spam (recommended)
- `p=reject` - Reject all failing emails (strict)

### 3. DKIM Benefits
- ✅ Email authentication
- ✅ Anti-tampering protection
- ✅ Improved deliverability
- ✅ Domain reputation building

## 🎯 Deliverability Tips

### 1. Gradual Volume Increase
- Start with low email volumes
- Gradually increase sending rate
- Monitor reputation metrics

### 2. List Hygiene
- Remove bouncing addresses
- Handle unsubscribes properly
- Monitor engagement rates

### 3. Content Quality
- Avoid spam trigger words
- Use proper HTML structure
- Include plain text versions

## 🔧 Troubleshooting

### Common Issues:

**Domain verification pending**
- Check DNS propagation (up to 72 hours)
- Verify TXT record syntax
- Ensure no conflicting records

**DKIM verification failing**
- Confirm all 3 CNAME records are added
- Check for DNS caching issues
- Verify CNAME syntax

**Emails going to spam**
- Wait 24-48 hours after DNS setup
- Check SPF/DKIM/DMARC alignment
- Monitor SES reputation metrics

**High bounce rate**
- Clean email lists
- Use double opt-in
- Remove invalid addresses

## 📈 Production Readiness

### Request SES Production Access
1. Go to SES Console → Sending Statistics
2. Click "Request Production Access"
3. Fill out use case form
4. Wait for approval (24-48 hours)

### Benefits of Production Access:
- ✅ Remove sending limits
- ✅ Higher sending rates
- ✅ Better deliverability
- ✅ Support for dedicated IPs

## 📞 Support Resources

- **AWS SES Documentation**: https://docs.aws.amazon.com/ses/
- **Email Deliverability Guide**: https://docs.aws.amazon.com/ses/latest/dg/deliverability.html
- **DNS Checker Tools**: whatsmydns.net, dnschecker.org
- **Email Testing**: mail-tester.com, glockapps.com

---

## 🎉 Expected Results

After completing this setup:
- ✅ **Domain verified** in SES
- ✅ **DKIM enabled** and verified
- ✅ **SPF protection** active
- ✅ **DMARC monitoring** enabled
- ✅ **Inbox delivery** for Trufo verification emails
- ✅ **Professional reputation** building

Your Trufo emails will now have enterprise-grade deliverability! 📧✨