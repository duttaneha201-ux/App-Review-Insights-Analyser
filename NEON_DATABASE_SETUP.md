# Neon Tech Database Setup Guide

This guide explains how to set up and configure Neon Tech PostgreSQL database for the App Review Insights Analyzer.

## 🎯 Why Neon?

- **Free tier available** - Perfect for development and small projects
- **Serverless PostgreSQL** - Auto-scales and pauses when not in use
- **Easy setup** - Get started in minutes
- **Persistent storage** - Data persists across deployments (unlike SQLite)
- **Perfect for Streamlit Cloud** - Works seamlessly with cloud deployments

## 📋 Step 1: Create Neon Database

1. **Sign up for Neon**
   - Go to https://neon.tech
   - Click "Sign Up" (free account)
   - Sign in with GitHub/Google (recommended)

2. **Create a Project**
   - Click "Create Project"
   - Choose a project name (e.g., "app-review-insights")
   - Select a region (closest to you)
   - Click "Create Project"

3. **Wait for Setup**
   - Neon will create your database (takes ~30 seconds)
   - You'll see a dashboard with connection details

## 🔑 Step 2: Get Connection String

1. **In Neon Dashboard:**
   - Go to your project
   - Click on "Connection Details" or "Connection String"
   - You'll see something like:
     ```
     postgresql://username:password@ep-xxxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
     ```

2. **Copy the Connection String**
   - Click "Copy" button next to the connection string
   - **Important**: Save this securely - you'll need it in multiple places

## 🔧 Step 3: Set Credentials

### Option A: Local Development (.env file)

Create or update `.env` file in project root:

```env
# Neon PostgreSQL Database
DATABASE_URL=postgresql://username:password@ep-xxxxx.us-east-2.aws.neon.tech/neondb?sslmode=require

# Groq API Key
GROQ_API_KEY=gsk_your-key-here

# SMTP Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=App Review Insights
```

**Important Notes:**
- Replace `username:password@ep-xxxxx...` with your actual Neon connection string
- The `?sslmode=require` part is important for Neon (SSL required)
- Never commit `.env` file to Git (it's already in `.gitignore`)

### Option B: Streamlit Cloud (Secrets)

1. **Go to Streamlit Cloud Dashboard**
   - Visit https://share.streamlit.io/
   - Select your app
   - Click "Settings" (⚙️ icon) or "Secrets"

2. **Add Secrets**
   - Click "Edit secrets" or "Add secret"
   - Add each secret as a key-value pair:

   ```
   DATABASE_URL=postgresql://username:password@ep-xxxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
   GROQ_API_KEY=gsk_your-key-here
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   SMTP_FROM_EMAIL=your-email@gmail.com
   SMTP_FROM_NAME=App Review Insights
   ```

3. **Save Secrets**
   - Click "Save"
   - Your app will automatically restart with new secrets

### Option C: GitHub Actions (Secrets)

1. **Go to GitHub Repository**
   - Navigate to your repository
   - Click "Settings" → "Secrets and variables" → "Actions"

2. **Add Repository Secret**
   - Click "New repository secret"
   - Name: `DATABASE_URL`
   - Value: Your Neon connection string
   - Click "Add secret"

3. **Repeat for other secrets** (GROQ_API_KEY, SMTP_*, etc.)

## ✅ Step 4: Test Connection

### Test Locally

Run the test script:

```bash
python scripts/test_neon_connection.py
```

Or test manually:

```python
# test_connection.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not set in .env file")
    exit(1)

print(f"Connecting to Neon database...")
try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"✅ Connected successfully!")
        print(f"PostgreSQL version: {version}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    exit(1)
```

### Expected Output

```
Connecting to Neon database...
✅ Connected successfully!
PostgreSQL version: PostgreSQL 15.x on x86_64-pc-linux-gnu...
```

## 🗄️ Step 5: Initialize Database Schema

After setting up the connection, create the database tables:

### Option A: Using Alembic (Recommended)

```bash
# Make sure DATABASE_URL is set in .env
alembic upgrade head
```

### Option B: Direct Creation

```python
# create_tables.py
import os
from dotenv import load_dotenv
from app.db.database import init_db

load_dotenv()
init_db()
print("✅ Database tables created successfully!")
```

Run:
```bash
python create_tables.py
```

## 🔍 Step 6: Verify Setup

Check that tables were created:

```python
# verify_tables.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))
inspector = inspect(engine)

tables = inspector.get_table_names()
print(f"✅ Found {len(tables)} tables:")
for table in sorted(tables):
    print(f"  - {table}")

# Expected tables:
# - apps
# - subscriptions
# - weekly_batches
# - reviews
# - theme_summaries
# - weekly_pulse_notes
```

## 🚨 Troubleshooting

### Issue: "No module named 'psycopg2'"

**Solution:**
```bash
pip install psycopg2-binary
# Or
pip install -r requirements.txt
```

### Issue: "Connection refused" or "Timeout"

**Possible causes:**
1. **Wrong connection string** - Double-check you copied the full string
2. **Network/firewall** - Neon should be accessible from anywhere
3. **Database paused** - Neon pauses inactive databases; first connection may take a few seconds

**Solution:**
- Verify connection string format
- Try connecting from Neon dashboard's SQL editor first
- Check if database is active (not paused)

### Issue: "SSL connection required"

**Solution:**
- Make sure your connection string includes `?sslmode=require`
- Neon requires SSL connections

### Issue: "Authentication failed"

**Solution:**
- Verify username and password in connection string
- Check if you copied the entire string correctly
- Try resetting password in Neon dashboard

### Issue: "Database does not exist"

**Solution:**
- Use the default database name from Neon (usually `neondb` or `defaultdb`)
- Or create a new database in Neon dashboard

## 📝 Connection String Format

Neon connection strings follow this format:

```
postgresql://[username]:[password]@[host]:[port]/[database]?sslmode=require
```

Example:
```
postgresql://myuser:mypassword@ep-cool-darkness-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
```

## 🔐 Security Best Practices

1. **Never commit secrets**
   - `.env` is already in `.gitignore`
   - Use Streamlit Cloud secrets for production
   - Use GitHub Secrets for CI/CD

2. **Rotate passwords regularly**
   - Change database password in Neon dashboard
   - Update all places where you use it

3. **Use connection pooling**
   - SQLAlchemy handles this automatically
   - Neon supports connection pooling

4. **Monitor usage**
   - Check Neon dashboard for usage stats
   - Free tier has generous limits

## 📊 Neon Free Tier Limits

- **Storage**: 0.5 GB (plenty for this app)
- **Compute**: 0.5 vCPU
- **Connections**: Unlimited
- **Auto-pause**: After 5 minutes of inactivity
- **Auto-resume**: On first connection after pause

## 🎯 Quick Checklist

- [ ] Created Neon account and project
- [ ] Copied connection string from Neon dashboard
- [ ] Added `psycopg2-binary` to requirements.txt
- [ ] Set `DATABASE_URL` in `.env` file (local)
- [ ] Set `DATABASE_URL` in Streamlit Cloud secrets (production)
- [ ] Tested connection locally
- [ ] Ran database migrations (`alembic upgrade head`)
- [ ] Verified tables were created
- [ ] Tested app with Neon database

## 🔗 Useful Links

- **Neon Dashboard**: https://console.neon.tech
- **Neon Documentation**: https://neon.tech/docs
- **Connection String Guide**: https://neon.tech/docs/connect/connect-from-any-app

## 💡 Tips

1. **Auto-pause**: Neon pauses your database after 5 minutes of inactivity. First connection after pause may take 2-3 seconds.

2. **Connection String**: Keep it secure. You can reset it anytime in Neon dashboard.

3. **Multiple Environments**: Use different Neon projects for dev/staging/production.

4. **Backup**: Neon automatically backs up your database. Check dashboard for restore options.

5. **Monitoring**: Use Neon dashboard to monitor queries, connections, and storage usage.

