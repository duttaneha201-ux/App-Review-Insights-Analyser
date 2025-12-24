# SMTP Setup Instructions

## What is SMTP?

SMTP (Simple Mail Transfer Protocol) is the standard protocol for sending emails. This module uses Python's built-in `smtplib` to send emails through any SMTP server.

**Supported Providers:**
- ✅ Gmail
- ✅ Outlook/Hotmail
- ✅ Yahoo Mail
- ✅ Custom SMTP servers

---

## Step 1: Choose Your Email Provider

### Option A: Gmail (Recommended for Testing)

**SMTP Settings:**
- Host: `smtp.gmail.com`
- Port: `587` (TLS) or `465` (SSL)
- Username: Your Gmail address
- Password: **App Password** (not your regular password!)

**How to get Gmail App Password:**
1. Go to https://myaccount.google.com/
2. Click **Security**
3. Enable **2-Step Verification** (required)
4. Go to **App passwords**
5. Select **Mail** and **Other (Custom name)**
6. Enter "App Review Insights"
7. Copy the 16-character password

### Option B: Outlook/Hotmail

**SMTP Settings:**
- Host: `smtp-mail.outlook.com`
- Port: `587` (TLS)
- Username: Your Outlook email
- Password: Your Outlook password (or App Password if 2FA enabled)

### Option C: Yahoo Mail

**SMTP Settings:**
- Host: `smtp.mail.yahoo.com`
- Port: `587` (TLS) or `465` (SSL)
- Username: Your Yahoo email
- Password: **App Password** (generate in Yahoo Account Security)

### Option D: Custom SMTP Server

Use your organization's SMTP server or any email provider's SMTP settings.

---

## Step 2: Set Environment Variables

### Option A: Windows PowerShell
```powershell
$env:SMTP_HOST="smtp.gmail.com"
$env:SMTP_PORT="587"
$env:SMTP_USERNAME="your-email@gmail.com"
$env:SMTP_PASSWORD="your-app-password"
$env:SMTP_FROM_EMAIL="your-email@gmail.com"
$env:SMTP_FROM_NAME="App Review Insights"
```

### Option B: Windows Command Prompt
```cmd
set SMTP_HOST=smtp.gmail.com
set SMTP_PORT=587
set SMTP_USERNAME=your-email@gmail.com
set SMTP_PASSWORD=your-app-password
set SMTP_FROM_EMAIL=your-email@gmail.com
set SMTP_FROM_NAME=App Review Insights
```

### Option C: Linux/Mac
```bash
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USERNAME="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export SMTP_FROM_EMAIL="your-email@gmail.com"
export SMTP_FROM_NAME="App Review Insights"
```

### Option D: Create `.env` file (Recommended)
Create a `.env` file in the project root:
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=App Review Insights
```

The code will automatically load it using `python-dotenv`.

---

## Step 3: Quick Start Examples

### Gmail Example
```python
from app.services.email_service import EmailService
from app.services.weekly_synthesis import WeeklyPulse

# Initialize with Gmail settings
service = EmailService(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_username="your-email@gmail.com",
    smtp_password="your-app-password"  # App Password, not regular password!
)

# Or use environment variables
service = EmailService()  # Reads from env vars
```

### Outlook Example
```python
service = EmailService(
    smtp_host="smtp-mail.outlook.com",
    smtp_port=587,
    smtp_username="your-email@outlook.com",
    smtp_password="your-password"
)
```

### Custom SMTP Example
```python
service = EmailService(
    smtp_host="smtp.example.com",
    smtp_port=587,
    smtp_username="user@example.com",
    smtp_password="password",
    use_tls=True
)
```

---

## Step 4: Test Your Setup

```python
from app.services.email_service import EmailService
from app.services.weekly_synthesis import WeeklyPulse

# Initialize service
service = EmailService()  # Uses env vars

# Create a test pulse
pulse = WeeklyPulse(
    title="Test Email",
    overview="This is a test email to verify SMTP setup.",
    themes=[{"name": "Test Theme", "summary": "Testing email delivery"}],
    quotes=["Test quote"],
    actions=["Test action"]
)

# Send test email
result = service.send_weekly_pulse(
    to_emails=["your-email@example.com"],  # Use your own email for testing
    pulse=pulse,
    app_name="Test App"
)

print(f"Success: {result['success']}")
print(f"Sent: {result['sent_count']}")
print(f"Failed: {result['failed_count']}")
```

---

## Troubleshooting

### "SMTP username is required"
- Set `SMTP_USERNAME` environment variable
- Or pass `smtp_username` parameter

### "SMTP password is required"
- Set `SMTP_PASSWORD` environment variable
- Or pass `smtp_password` parameter
- **For Gmail**: Use App Password, not regular password!

### "SMTPAuthenticationError: Authentication failed"
- **Gmail**: Make sure you're using an App Password, not your regular password
- **Gmail**: Enable 2-Step Verification first
- Check username and password are correct
- Some providers require App Passwords when 2FA is enabled

### "Email not received"
- Check spam/junk folder
- Verify SMTP settings are correct
- Check firewall isn't blocking SMTP port
- Gmail may require "Less secure app access" (deprecated) or App Password

### "Connection refused" or "Timeout"
- Check SMTP host and port are correct
- Verify firewall allows SMTP connections
- Try different port (587 vs 465)
- Some networks block SMTP ports

### Gmail Rate Limits
- **Free Gmail**: 500 emails/day
- **Google Workspace**: 2000 emails/day
- If exceeded, wait 24 hours or upgrade

---

## Common SMTP Settings

| Provider | Host | Port | TLS | Notes |
|----------|------|------|-----|-------|
| **Gmail** | smtp.gmail.com | 587 | Yes | Requires App Password |
| **Gmail** | smtp.gmail.com | 465 | SSL | Requires App Password |
| **Outlook** | smtp-mail.outlook.com | 587 | Yes | Regular password OK |
| **Yahoo** | smtp.mail.yahoo.com | 587 | Yes | Requires App Password |
| **Yahoo** | smtp.mail.yahoo.com | 465 | SSL | Requires App Password |

---

## Security Best Practices

✅ **DO:**
- Use App Passwords (Gmail, Yahoo) instead of regular passwords
- Store credentials in `.env` file (add to `.gitignore`)
- Use environment variables in production
- Enable 2FA on your email account
- Use TLS encryption (port 587)

❌ **DON'T:**
- Commit credentials to version control
- Share passwords publicly
- Use regular passwords if App Passwords are available
- Disable TLS unless absolutely necessary

---

## Rate Limits

| Provider | Free Tier Limit |
|----------|----------------|
| **Gmail** | 500 emails/day |
| **Outlook** | 300 emails/day |
| **Yahoo** | 500 emails/day |

**Note**: These are per-account limits. For higher volumes, consider:
- Multiple email accounts
- Email service providers (SendGrid, Mailgun, etc.)
- Custom SMTP server

---

## Quick Reference

**Required Environment Variables:**
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

**Optional Environment Variables:**
```
SMTP_FROM_EMAIL=your-email@gmail.com  # Defaults to SMTP_USERNAME
SMTP_FROM_NAME=App Review Insights    # Defaults to "App Review Insights"
```

**Default Values:**
- `SMTP_HOST`: `smtp.gmail.com`
- `SMTP_PORT`: `587`
- `use_tls`: `True`

---

## Cost

**100% FREE!** 🎉

- Gmail: Free (500 emails/day)
- Outlook: Free (300 emails/day)
- Yahoo: Free (500 emails/day)

No external service required - uses your existing email account!

---

## Next Steps

Once SMTP is configured:
1. ✅ Module 7 is ready to use
2. ✅ You can send weekly pulse emails
3. ⏳ Module 8 (Scheduler) will automate weekly emails

---

## Support

- **Gmail App Passwords**: https://support.google.com/accounts/answer/185833
- **Outlook SMTP**: https://support.microsoft.com/en-us/office/pop-imap-and-smtp-settings-8361e398-8af4-4e97-b147-6c6c4ac95353
- **Python smtplib Docs**: https://docs.python.org/3/library/smtplib.html

