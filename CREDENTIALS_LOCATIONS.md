# Where to Provide Credentials

This document shows exactly where to set your credentials for different deployment scenarios.

## 🎯 Quick Reference

| Credential | Local (.env) | Streamlit Cloud | GitHub Actions |
|------------|-------------|------------------|----------------|
| `DATABASE_URL` | ✅ Yes | ✅ Yes | ✅ Yes |
| `GROQ_API_KEY` | ✅ Yes | ✅ Yes | ✅ Yes |
| `SMTP_HOST` | ✅ Yes | ✅ Yes | ✅ Yes |
| `SMTP_PORT` | ✅ Yes | ✅ Yes | ✅ Yes |
| `SMTP_USERNAME` | ✅ Yes | ✅ Yes | ✅ Yes |
| `SMTP_PASSWORD` | ✅ Yes | ✅ Yes | ✅ Yes |
| `SMTP_FROM_EMAIL` | ✅ Optional | ✅ Optional | ✅ Optional |
| `SMTP_FROM_NAME` | ✅ Optional | ✅ Optional | ✅ Optional |

## 📍 Location 1: Local Development (.env file)

**File:** `.env` (in project root)

**How to create:**
1. Create a file named `.env` in the project root directory
2. Copy the template below
3. Fill in your actual values

**Template:**
```env
# Neon PostgreSQL Database
DATABASE_URL=postgresql://username:password@ep-xxxxx.us-east-2.aws.neon.tech/neondb?sslmode=require

# Groq API Key
GROQ_API_KEY=gsk_your-groq-api-key-here

# SMTP Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=App Review Insights
```

**Important:**
- ✅ `.env` is already in `.gitignore` (won't be committed)
- ✅ Loaded automatically by `python-dotenv`
- ✅ Used for local development and testing

**Example Neon connection string:**
```
DATABASE_URL=postgresql://neondb_owner:AbCdEf123456@ep-cool-darkness-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
```

## 📍 Location 2: Streamlit Cloud (Secrets)

**Where:** Streamlit Cloud Dashboard → Your App → Settings → Secrets

**How to set:**
1. Go to https://share.streamlit.io/
2. Sign in and select your app
3. Click "Settings" (⚙️ icon) or "Secrets" in the sidebar
4. Click "Edit secrets" or "Add secret"
5. Add each credential as a key-value pair
6. Click "Save"

**Format (TOML format):**
```toml
DATABASE_URL = "postgresql://username:password@ep-xxxxx.neon.tech/neondb?sslmode=require"
GROQ_API_KEY = "gsk_your-groq-api-key-here"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = "587"
SMTP_USERNAME = "your-email@gmail.com"
SMTP_PASSWORD = "your-app-password"
SMTP_FROM_EMAIL = "your-email@gmail.com"
SMTP_FROM_NAME = "App Review Insights"
```

**Important:**
- ✅ Values are encrypted and secure
- ✅ App restarts automatically after saving
- ✅ Accessible via `os.getenv()` in your Streamlit app
- ✅ Never visible in code or logs

**Screenshot locations:**
- Main menu: Click your app → "⚙️ Settings" → "Secrets"
- Or: Click "☰" menu → "Settings" → "Secrets"

## 📍 Location 3: GitHub Actions (Repository Secrets)

**Where:** GitHub Repository → Settings → Secrets and variables → Actions

**How to set:**
1. Go to your GitHub repository
2. Click "Settings" (top menu)
3. Click "Secrets and variables" → "Actions"
4. Click "New repository secret"
5. Enter name (e.g., `DATABASE_URL`)
6. Enter value (your connection string)
7. Click "Add secret"
8. Repeat for all credentials

**Required secrets:**
- `DATABASE_URL`
- `GROQ_API_KEY`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM_EMAIL` (optional)
- `SMTP_FROM_NAME` (optional)

**Important:**
- ✅ Used by `.github/workflows/weekly_scheduler.yml`
- ✅ Accessible via `${{ secrets.SECRET_NAME }}`
- ✅ Encrypted and secure
- ✅ Only accessible to workflows

## 🔑 Getting Your Neon Connection String

1. **Go to Neon Dashboard**
   - Visit https://console.neon.tech
   - Sign in to your account

2. **Select Your Project**
   - Click on your project name

3. **Get Connection String**
   - Look for "Connection Details" or "Connection String"
   - Click "Copy" button
   - Format: `postgresql://username:password@ep-xxxxx.neon.tech/neondb?sslmode=require`

4. **Use It**
   - Paste into `.env` file (local)
   - Paste into Streamlit Cloud secrets (production)
   - Paste into GitHub Actions secrets (CI/CD)

## ✅ Verification Steps

### Test Local Connection
```bash
python scripts/test_neon_connection.py
```

### Test Streamlit Cloud
1. Deploy app to Streamlit Cloud
2. Check app logs for connection errors
3. Try submitting a form to test database writes

### Test GitHub Actions
1. Manually trigger workflow
2. Check workflow logs
3. Verify no "DATABASE_URL not set" errors

## 🔐 Security Best Practices

1. **Never commit secrets**
   - `.env` is in `.gitignore` ✅
   - Don't hardcode in source code
   - Use environment variables or secrets

2. **Use different credentials for different environments**
   - Local: `.env` file
   - Production: Streamlit Cloud secrets
   - CI/CD: GitHub Actions secrets

3. **Rotate credentials regularly**
   - Change passwords periodically
   - Update all locations when rotating

4. **Limit access**
   - Only share credentials with trusted team members
   - Use least privilege principle

## 📝 Quick Checklist

### For Local Development
- [ ] Created `.env` file in project root
- [ ] Added all required credentials
- [ ] Tested connection: `python scripts/test_neon_connection.py`
- [ ] Ran migrations: `alembic upgrade head`

### For Streamlit Cloud
- [ ] Created Neon database
- [ ] Got connection string from Neon
- [ ] Added all secrets in Streamlit Cloud dashboard
- [ ] Deployed app
- [ ] Tested app functionality

### For GitHub Actions
- [ ] Added all secrets in GitHub repository settings
- [ ] Verified workflow can access secrets
- [ ] Tested workflow manually
- [ ] Checked workflow logs for errors

## 🆘 Troubleshooting

### "DATABASE_URL not set"
- **Local**: Check `.env` file exists and has `DATABASE_URL=...`
- **Streamlit**: Verify secrets are saved in dashboard
- **GitHub Actions**: Check repository secrets are set

### "Connection failed"
- Verify connection string is correct
- Check database is active (not paused) in Neon
- Ensure `?sslmode=require` is included
- Test connection: `python scripts/test_neon_connection.py`

### "Module not found: psycopg2"
- Install: `pip install psycopg2-binary`
- Or: `pip install -r requirements.txt`

## 📚 Related Documentation

- **[NEON_DATABASE_SETUP.md](./NEON_DATABASE_SETUP.md)**: Detailed Neon setup guide
- **[DEPENDENCIES_AND_CREDENTIALS.md](./DEPENDENCIES_AND_CREDENTIALS.md)**: General credentials guide
- **[GITHUB_ACTIONS_SETUP.md](./GITHUB_ACTIONS_SETUP.md)**: GitHub Actions configuration

