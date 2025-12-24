# 🚀 Streamlit Cloud Deployment Guide

Complete step-by-step guide to deploy your App Review Insights Analyzer to Streamlit Cloud.

## ✅ Prerequisites Completed

- [x] Neon database created and configured
- [x] Database tables initialized
- [x] Code pushed to GitHub
- [x] All dependencies in `requirements.txt`

## 📋 Deployment Steps

### Step 1: Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud**
   - Visit: https://share.streamlit.io/
   - Click "Sign in" and authorize with GitHub

2. **Create New App**
   - Click "New app" button (top right)
   - Fill in the form:
     - **Repository**: `duttaneha201-ux/App-Review-Insights-Analyser`
     - **Branch**: `main`
     - **Main file path**: `streamlit_app.py`
   - Click "Deploy"

3. **Wait for Deployment**
   - First deployment takes 2-3 minutes
   - Watch the build logs
   - You'll see a URL like: `https://app-review-insights-analyser.streamlit.app`

### Step 2: Configure Secrets

1. **Open App Settings**
   - In Streamlit Cloud dashboard, click your app
   - Click "⚙️ Settings" (or "☰" menu → "Settings")
   - Click "Secrets" in the sidebar

2. **Add All Secrets**
   Open the secrets editor and paste this (replace with your actual values):

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

3. **Save and Restart**
   - Click "Save" button
   - App will automatically restart
   - Wait for restart to complete

### Step 3: Verify Deployment

1. **Check App Status**
   - App should show "Running" status
   - Click "Open app" to view your deployed app

2. **Test the App**
   - Enter a Play Store URL
   - Select weeks (1-12)
   - Enter your email
   - Click "Start Analysis"
   - Wait for processing

3. **Check Logs**
   - Click "☰" menu → "Manage app" → "Logs"
   - Look for any errors
   - Verify database connection messages

## 🔍 Troubleshooting

### App Won't Deploy

**Error: "Module not found"**
- Check `requirements.txt` includes all dependencies
- Verify `streamlit>=1.28.0` is in requirements.txt
- Check build logs for missing packages

**Error: "File not found: streamlit_app.py"**
- Verify `streamlit_app.py` is in the root directory
- Check the main file path in deployment settings

### Secrets Not Working

**Error: "DATABASE_URL not set"**
- Verify secrets are saved (check Settings → Secrets)
- Ensure secret names match exactly (case-sensitive)
- Restart app after adding secrets

**Error: "Connection failed"**
- Verify DATABASE_URL is correct
- Check Neon database is active (not paused)
- Ensure `?sslmode=require` is in connection string

### Database Issues

**Error: "Table does not exist"**
- Tables should be created automatically on first use
- Or run `python scripts/create_tables.py` locally first
- Check Neon dashboard SQL editor to verify tables

## 📊 Monitoring

### Check App Health
- **Status**: Dashboard shows "Running" or "Error"
- **Logs**: View real-time logs in Streamlit Cloud
- **Usage**: Monitor app usage and performance

### Check Database
- **Neon Dashboard**: https://console.neon.tech
- **SQL Editor**: Run queries to check data
- **Connection**: Verify active connections

## 🎯 Your App URL

After deployment, your app will be available at:
```
https://your-app-name.streamlit.app
```

Share this URL with users!

## 📝 Quick Checklist

- [ ] Deployed to Streamlit Cloud
- [ ] Added all secrets in Settings
- [ ] App shows "Running" status
- [ ] Tested form submission
- [ ] Verified database connection
- [ ] Confirmed email delivery works

## 🎉 Success!

Your app is now live! Users can:
- Submit Play Store URLs
- Get weekly insights via email
- Access analysis results

## 🔗 Useful Links

- **Streamlit Cloud**: https://share.streamlit.io/
- **Neon Dashboard**: https://console.neon.tech
- **GitHub Repo**: https://github.com/duttaneha201-ux/App-Review-Insights-Analyser
- **Streamlit Docs**: https://docs.streamlit.io/

