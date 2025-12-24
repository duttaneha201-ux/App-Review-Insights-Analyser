# 🔐 Credentials Summary - Where to Set What

## Quick Answer

**For Streamlit Cloud deployment:** ❌ **NO** - You don't need GitHub secrets  
**For GitHub Actions scheduler:** ✅ **YES** - You need GitHub secrets (optional)

## 📍 Two Different Places for Two Different Purposes

### 1. Streamlit Cloud (Required for your app)

**Where:** Streamlit Cloud Dashboard (NOT GitHub)

**Purpose:** Your deployed Streamlit app needs these to run

**How to set:**
1. Go to https://share.streamlit.io/
2. Select your app → Settings → Secrets
3. Add all credentials there

**Secrets needed:**
- `DATABASE_URL`
- `GROQ_API_KEY`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
- `SMTP_FROM_EMAIL`, `SMTP_FROM_NAME` (optional)

### 2. GitHub Actions (Optional - for weekly scheduler)

**Where:** GitHub Repository → Settings → Secrets and variables → Actions

**Purpose:** Only needed if you want the automated weekly scheduler to run

**When to set:**
- ✅ Set these if you want automated weekly analysis (every Monday 8 AM IST)
- ❌ Skip if you only want the Streamlit app (manual analysis)

**Secrets needed (same as Streamlit):**
- `DATABASE_URL`
- `GROQ_API_KEY`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
- `SMTP_FROM_EMAIL`, `SMTP_FROM_NAME` (optional)

## 🎯 Recommendation

### For Streamlit Deployment Only:
1. ✅ **Set secrets in Streamlit Cloud** (required)
2. ❌ **Skip GitHub secrets** (not needed)

### For Full Automation:
1. ✅ **Set secrets in Streamlit Cloud** (for app)
2. ✅ **Set secrets in GitHub** (for weekly scheduler)

## 📝 Step-by-Step: GitHub Secrets (If Needed)

**Only do this if you want the weekly scheduler to run automatically.**

1. **Go to GitHub Repository**
   - Visit: https://github.com/duttaneha201-ux/App-Review-Insights-Analyser
   - Click "Settings" (top menu, right side)

2. **Navigate to Secrets**
   - Click "Secrets and variables" in left sidebar
   - Click "Actions"

3. **Add Each Secret**
   - Click "New repository secret"
   - Add one by one:

   **Required:**
   - Name: `GROQ_API_KEY`, Value: `gsk_your-key-here`
   - Name: `SMTP_HOST`, Value: `smtp.gmail.com`
   - Name: `SMTP_PORT`, Value: `587`
   - Name: `SMTP_USERNAME`, Value: `your-email@gmail.com`
   - Name: `SMTP_PASSWORD`, Value: `your-app-password`
   - Name: `DATABASE_URL`, Value: `postgresql://username:password@ep-xxxxx.neon.tech/neondb?sslmode=require`

   **Optional:**
   - Name: `SMTP_FROM_EMAIL`, Value: `your-email@gmail.com`
   - Name: `SMTP_FROM_NAME`, Value: `App Review Insights`

4. **Verify**
   - You should see all secrets listed
   - They're encrypted and secure

## ✅ Checklist

### For Streamlit App:
- [ ] Set secrets in Streamlit Cloud ✅ **REQUIRED**

### For Weekly Scheduler:
- [ ] Set secrets in GitHub Actions ⚠️ **OPTIONAL** (only if you want automation)

## 🎯 Bottom Line

**For deploying your Streamlit app:**  
→ Set secrets in **Streamlit Cloud** (not GitHub)

**For automated weekly scheduler:**  
→ Set secrets in **GitHub** (in addition to Streamlit Cloud)

**You can deploy and use the Streamlit app without any GitHub secrets!**

