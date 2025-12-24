# 🚀 Next Steps: Deploy to Streamlit Cloud

Follow these steps in order to deploy your App Review Insights Analyzer to Streamlit Cloud.

## ✅ Step 1: Set Up Neon Database (5 minutes)

1. **Sign up for Neon**
   - Go to https://neon.tech
   - Click "Sign Up" (free, no credit card needed)
   - Sign in with GitHub/Google

2. **Create Project**
   - Click "Create Project"
   - Name: `app-review-insights` (or any name)
   - Select region closest to you
   - Click "Create Project"
   - Wait ~30 seconds for setup

3. **Get Connection String**
   - In Neon dashboard, find "Connection Details"
   - Click "Copy" next to the connection string
   - Format: `postgresql://username:password@ep-xxxxx.neon.tech/neondb?sslmode=require`
   - **Save this** - you'll need it in Step 3

## ✅ Step 2: Install Dependencies Locally (2 minutes)

```bash
# Install PostgreSQL driver
pip install psycopg2-binary

# Or install all dependencies
pip install -r requirements.txt
```

## ✅ Step 3: Test Database Connection Locally (2 minutes)

1. **Create `.env` file** in project root:
   ```env
   DATABASE_URL=postgresql://username:password@ep-xxxxx.neon.tech/neondb?sslmode=require
   GROQ_API_KEY=gsk_your-key-here
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   ```

2. **Test connection:**
   ```bash
   python scripts/test_neon_connection.py
   ```

3. **Initialize database:**
   ```bash
   alembic upgrade head
   # OR
   python scripts/create_tables.py
   ```

## ✅ Step 4: Create Streamlit App (Already Done!)

The `streamlit_app.py` file has been created for you. It includes:
- ✅ Form for Play Store URL, weeks, and email
- ✅ Progress tracking
- ✅ Error handling
- ✅ Results display
- ✅ Database integration

## ✅ Step 5: Test Streamlit App Locally (5 minutes)

1. **Install Streamlit:**
   ```bash
   pip install streamlit
   ```

2. **Run locally:**
   ```bash
   streamlit run streamlit_app.py
   ```

3. **Test the app:**
   - Open http://localhost:8501
   - Enter a Play Store URL (e.g., `https://play.google.com/store/apps/details?id=com.whatsapp`)
   - Select weeks (1-12)
   - Enter your email
   - Click "Start Analysis"
   - Wait for processing (may take a few minutes)

4. **Verify:**
   - Check that database connection works
   - Verify analysis completes
   - Check email is sent

## ✅ Step 6: Push to GitHub (2 minutes)

If not already done:

```bash
# Add all files
git add .

# Commit
git commit -m "Add Streamlit app and Neon database support"

# Push
git push origin main
```

## ✅ Step 7: Deploy to Streamlit Cloud (5 minutes)

1. **Go to Streamlit Cloud**
   - Visit https://share.streamlit.io/
   - Sign in with GitHub

2. **New App**
   - Click "New app"
   - Select your repository
   - Branch: `main`
   - Main file path: `streamlit_app.py`
   - Click "Deploy"

3. **Wait for deployment**
   - First deployment takes 2-3 minutes
   - Watch the logs for any errors

## ✅ Step 8: Configure Secrets in Streamlit Cloud (3 minutes)

1. **In Streamlit Cloud Dashboard:**
   - Click your app
   - Click "⚙️ Settings" → "Secrets"

2. **Add all secrets:**
   ```toml
   DATABASE_URL = "postgresql://username:password@ep-xxxxx.neon.tech/neondb?sslmode=require"
   GROQ_API_KEY = "gsk_your-key-here"
   SMTP_HOST = "smtp.gmail.com"
   SMTP_PORT = "587"
   SMTP_USERNAME = "your-email@gmail.com"
   SMTP_PASSWORD = "your-app-password"
   SMTP_FROM_EMAIL = "your-email@gmail.com"
   SMTP_FROM_NAME = "App Review Insights"
   ```

3. **Save**
   - Click "Save"
   - App will restart automatically

## ✅ Step 9: Test Deployed App (2 minutes)

1. **Open your Streamlit app URL**
   - Format: `https://your-app-name.streamlit.app`

2. **Test functionality:**
   - Submit a test request
   - Verify database writes work
   - Check email delivery

3. **Check logs:**
   - Click "☰" menu → "Manage app" → "Logs"
   - Look for any errors

## ✅ Step 10: Initialize Database on Neon (One-time)

After first deployment, initialize the database:

**Option A: Use Streamlit app**
- The app will create tables automatically on first use

**Option B: Run migration script**
- Connect to Neon via their SQL editor
- Or run locally: `alembic upgrade head`

## 🎉 You're Done!

Your app is now live on Streamlit Cloud with:
- ✅ Neon PostgreSQL database
- ✅ Persistent data storage
- ✅ Email delivery
- ✅ Full analysis pipeline

## 📋 Quick Checklist

- [ ] Created Neon account and project
- [ ] Got Neon connection string
- [ ] Installed `psycopg2-binary`
- [ ] Created `.env` file locally
- [ ] Tested database connection locally
- [ ] Initialized database tables
- [ ] Tested Streamlit app locally
- [ ] Pushed code to GitHub
- [ ] Deployed to Streamlit Cloud
- [ ] Added secrets in Streamlit Cloud
- [ ] Tested deployed app

## 🆘 Troubleshooting

### Database connection fails
- Verify connection string is correct
- Check database is active (not paused) in Neon
- Ensure `?sslmode=require` is included

### App won't deploy
- Check `streamlit_app.py` exists in root
- Verify all imports work
- Check Streamlit Cloud logs

### Secrets not working
- Verify secrets are saved in Streamlit Cloud
- Check secret names match exactly (case-sensitive)
- Restart app after adding secrets

## 📚 Need Help?

- **Database setup**: See [NEON_DATABASE_SETUP.md](./NEON_DATABASE_SETUP.md)
- **Credentials**: See [CREDENTIALS_LOCATIONS.md](./CREDENTIALS_LOCATIONS.md)
- **Streamlit docs**: https://docs.streamlit.io/

