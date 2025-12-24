# GitHub Actions Scheduler Setup

This document explains how to set up and use the GitHub Actions-based weekly scheduler for the App Review Insights Analyzer.

## 🎯 Overview

The weekly scheduler runs automatically every Monday at 08:00 IST (02:30 UTC) to:
- Process all active subscriptions
- Extract and analyze reviews from the last complete week
- Generate weekly product pulse reports
- Send emails to subscribers

## ⏰ Cron Timing

**IST to UTC Conversion:**
- IST (Indian Standard Time) = UTC + 5:30
- Monday 08:00 IST = Monday 02:30 UTC
- Cron expression: `30 2 * * 1` (Monday at 02:30 UTC)

**Why 02:30 UTC?**
- IST is UTC+5:30
- 08:00 IST - 5:30 = 02:30 UTC
- GitHub Actions uses UTC for cron schedules

## 🔐 Required GitHub Secrets

Configure these secrets in your GitHub repository:

**Settings → Secrets and variables → Actions → New repository secret**

### Required Secrets

1. **`GROQ_API_KEY`**
   - Your Groq API key from https://console.groq.com/
   - Format: `gsk_...`

2. **`SMTP_HOST`**
   - SMTP server hostname
   - Example: `smtp.gmail.com`

3. **`SMTP_PORT`**
   - SMTP server port
   - Example: `587` (TLS) or `465` (SSL)

4. **`SMTP_USERNAME`**
   - SMTP username (usually your email address)
   - Example: `your-email@gmail.com`

5. **`SMTP_PASSWORD`**
   - SMTP password (use App Password for Gmail)
   - For Gmail: Generate App Password at https://myaccount.google.com/apppasswords

### Optional Secrets

6. **`SMTP_FROM_EMAIL`**
   - From email address (defaults to `SMTP_USERNAME` if not set)

7. **`SMTP_FROM_NAME`**
   - From name (defaults to "App Review Insights" if not set)

8. **`DATABASE_URL`** (Recommended)
   - Database connection string
   - **Important**: SQLite files are ephemeral in GitHub Actions and won't persist between runs
   - **Recommended**: Use a remote database for production
   - Examples:
     - PostgreSQL: `postgresql://user:pass@host:5432/dbname`
     - Railway: Get connection string from Railway dashboard
     - Render: Get connection string from Render dashboard
     - Supabase: Get connection string from Supabase dashboard
   - If not set, defaults to `sqlite:///./data/reviews.db` (not recommended for GitHub Actions)

## 🚀 Manual Trigger

You can manually trigger the workflow for testing:

1. Go to **Actions** tab in your GitHub repository
2. Select **Weekly Review Analysis Scheduler** workflow
3. Click **Run workflow** button
4. Select branch (usually `main`)
5. Click **Run workflow**

This is useful for:
- Testing the workflow
- Debugging issues
- Running analysis outside the scheduled time

## 📊 Workflow Steps

The workflow performs these steps:

1. **Checkout repository** - Gets the latest code
2. **Set up Python** - Installs Python 3.11
3. **Install system dependencies** - Installs browser dependencies for Playwright
4. **Install Python dependencies** - Installs packages from `requirements.txt`
5. **Install Playwright browsers** - Installs Chromium browser
6. **Set up environment variables** - Validates secrets are set
7. **Run weekly scheduler** - Executes `scripts/run_weekly_scheduler.py`

## 🔍 Observability

### Logs

All logs are visible in the GitHub Actions run:
- Job start time
- Number of subscriptions processed
- Success/failure status
- Error details (if any)
- Execution duration

### Failure Handling

- **No automatic retries** - Failures are logged and visible
- **Non-zero exit code** - Workflow marked as failed
- **Artifact upload** - Logs uploaded on failure (retained 7 days)
- **Clear error messages** - Stack traces included in logs

### Success Indicators

- ✅ Workflow completes with exit code 0
- ✅ Logs show "Weekly job completed successfully"
- ✅ `processed_count` > 0 (if subscriptions exist)

## 🔒 Idempotency

The scheduler is **safe to re-run**:

- **Database checks** - Skips already-processed batches
- **Batch status** - Checks `WeeklyBatch.status == 'processed'`
- **Pulse note check** - Verifies `WeeklyPulseNote` exists
- **No duplicate work** - Same week won't be processed twice

If you manually trigger the workflow multiple times:
- First run: Processes the week
- Subsequent runs: Skips with "Batch already processed" message

## 🛠️ Troubleshooting

### Workflow Fails Immediately

**Check:**
- All required secrets are set
- Secret names match exactly (case-sensitive)
- Secrets contain valid values (no extra spaces)

### "Missing required environment variables"

**Solution:**
- Verify all required secrets are configured
- Check secret names match the workflow file
- Re-enter secrets if needed

### "No reviews found"

**Possible causes:**
- App has no reviews in the date range
- Play Store URL is incorrect
- Date range calculation issue

**Solution:**
- Check subscription in database
- Verify app URL is correct
- Check review extraction logs

### Email Not Sent

**Check:**
- SMTP credentials are correct
- SMTP server allows connections from GitHub Actions IPs
- Email service logs for errors
- Note: Email failures don't fail the whole job (partial success)

### Database Connection Issues

**If using SQLite:**
- ⚠️ **SQLite files are ephemeral in GitHub Actions**
- Each workflow run starts with a fresh filesystem
- Database won't persist between runs
- Idempotency checks won't work across runs

**Solution:**
- **Required for production**: Set `DATABASE_URL` secret to a remote database
- Use services like:
  - **Railway**: PostgreSQL (free tier available)
  - **Render**: PostgreSQL (free tier available)
  - **Supabase**: PostgreSQL (free tier available)
  - **Neon**: Serverless PostgreSQL (free tier available)
- Get connection string from your database provider
- Format: `postgresql://user:password@host:port/database`

## 📝 Environment Variables Reference

For local development, create a `.env` file:

```env
# Required
GROQ_API_KEY=gsk_your-key-here
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Optional
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=App Review Insights
DATABASE_URL=sqlite:///./data/reviews.db
```

## 🔄 Migration from Local Scheduler

If you were using the local APScheduler:

1. **Disable local scheduler** - Set `SCHEDULER_ENABLED=false` in your local `.env`
2. **Set up GitHub Actions** - Follow this guide
3. **Test manually** - Trigger workflow manually first
4. **Monitor first run** - Check logs on next Monday 08:00 IST

The GitHub Actions scheduler replaces the local cron job while maintaining the same functionality.

## 📚 Related Documentation

- [Scheduler Module README](./app/scheduler/README.md) - Detailed scheduler implementation
- [Dependencies & Credentials](./DEPENDENCIES_AND_CREDENTIALS.md) - API key setup
- [SMTP Setup](./SMTP_SETUP.md) - Email configuration

