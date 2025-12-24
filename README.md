# App Review Insights Analyzer

A comprehensive system for extracting, analyzing, and synthesizing Google Play Store reviews into actionable weekly insights delivered via email.

## 🚀 Features

- **Automated Review Extraction**: Scrapes reviews from Google Play Store using Playwright
- **PII Scrubbing**: Automatically detects and removes personally identifiable information
- **Theme Identification**: Uses LLM (Groq) to identify and group review themes
- **Weekly Synthesis**: Generates executive-friendly weekly product pulse reports
- **Email Delivery**: Sends insights directly to subscribers via email
- **Scheduled Processing**: Automated weekly analysis every Monday at 8:00 AM IST
- **Web UI**: Simple interface for managing subscriptions
- **REST API**: FastAPI-based backend for programmatic access

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend development, optional)
- Groq API Key (free at https://console.groq.com/)
- SMTP credentials (Gmail App Password or SendGrid)

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd App-Review-Insights-Analyser
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Set Environment Variables

Create a `.env` file in the project root:

```env
# Required: Groq API Key (get from https://console.groq.com/)
GROQ_API_KEY=gsk_your-key-here

# Required: SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Database Configuration
# For local development with SQLite:
# DATABASE_URL=sqlite:///./data/reviews.db
# For production/Streamlit Cloud with Neon PostgreSQL:
# DATABASE_URL=postgresql://username:password@ep-xxxxx.neon.tech/neondb?sslmode=require
# See NEON_DATABASE_SETUP.md for detailed setup instructions

# Optional: Scheduler Configuration
SCHEDULER_ENABLED=true
SCHEDULER_TIMEZONE=Asia/Kolkata
```

See [DEPENDENCIES_AND_CREDENTIALS.md](./DEPENDENCIES_AND_CREDENTIALS.md) for detailed setup instructions.

**For Streamlit Cloud deployment**, see [NEON_DATABASE_SETUP.md](./NEON_DATABASE_SETUP.md) for PostgreSQL/Neon database setup.

### 4. Initialize Database

```bash
alembic upgrade head
```

## 🏃 Running the Application

### Option 1: Start Both Servers (Recommended)

**Windows:**
```bash
start_servers.bat
```

**Linux/Mac:**
```bash
chmod +x start_servers.sh
./start_servers.sh
```

### Option 2: Manual Start

**Backend API:**
```bash
python run_api_server.py
```

**Frontend (Simple HTML):**
```bash
python start_frontend_simple.py
```

**Frontend (Next.js - if installed):**
```bash
cd frontend
npm install
npm run dev
```

### Access the Application

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📁 Project Structure

```
App-Review-Insights-Analyser/
├── app/                      # Main application code
│   ├── api/                  # FastAPI endpoints
│   ├── db/                   # Database models, repositories, migrations
│   ├── models/               # Domain models
│   ├── scheduler/            # APScheduler configuration and jobs
│   ├── services/             # Core business logic services
│   └── pipeline.py           # End-to-end pipeline orchestration
├── alembic/                  # Database migrations
├── data/                     # SQLite databases (gitignored)
├── examples/                 # Example usage scripts
├── frontend/                 # Frontend UI (Next.js + HTML)
├── scripts/                  # Utility scripts
│   ├── cli_extract_reviews.py
│   └── view_subscriptions.py
├── tests/                    # Unit and integration tests
├── requirements.txt          # Python dependencies
├── run_api_server.py         # Main server entry point
└── README.md                 # This file
```

See [FOLDER_STRUCTURE.md](./FOLDER_STRUCTURE.md) for detailed structure documentation.

## 🧪 Testing

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

Run specific test suite:
```bash
pytest tests/test_pipeline.py -v
```

## 📚 Documentation

- **[Neon Database Setup](./NEON_DATABASE_SETUP.md)**: PostgreSQL/Neon database configuration for Streamlit Cloud
- **[GitHub Actions Setup](./GITHUB_ACTIONS_SETUP.md)**: Automated weekly scheduler configuration
- **[Dependencies & Credentials](./DEPENDENCIES_AND_CREDENTIALS.md)**: Setup guide for API keys and credentials
- **[Groq Setup](./GROQ_SETUP.md)**: Detailed Groq API setup instructions
- **[SMTP Setup](./SMTP_SETUP.md)**: Email service configuration
- **[Project Roadmap](./PROJECT_ROADMAP.md)**: Development roadmap and completed modules

## 🔧 Utility Scripts

### View Subscriptions
```bash
# From project root (recommended)
python scripts/view_subscriptions.py

# View by email instead of by app
python scripts/view_subscriptions.py --by-email

# Scripts work from any directory
cd scripts
python view_subscriptions.py
```

### Extract Reviews (CLI)
```bash
# From project root (recommended)
python scripts/cli_extract_reviews.py "https://play.google.com/store/apps/details?id=com.whatsapp" --weeks 4

# Scripts work from any directory
cd scripts
python cli_extract_reviews.py "https://play.google.com/store/apps/details?id=com.whatsapp" --weeks 4
```

**Note:** These scripts automatically add the project root to the Python path, so they work whether run from the project root or from within the `scripts/` directory.

## ⏰ Automated Scheduling (GitHub Actions)

The weekly review analysis runs automatically via GitHub Actions:

- **Schedule**: Every Monday at 08:00 IST (02:30 UTC)
- **Manual Trigger**: Available in GitHub Actions tab
- **Idempotent**: Safe to re-run, skips already-processed batches
- **Observable**: Full logs in GitHub Actions interface

**Setup:** See [GitHub Actions Setup Guide](./GITHUB_ACTIONS_SETUP.md) for:
- Required GitHub Secrets configuration
- Manual trigger instructions
- Troubleshooting guide
- IST to UTC conversion details

## 🚢 Deployment

See deployment options in [DEPLOYMENT.md](./DEPLOYMENT.md) (to be created).

Recommended platforms:
- **Railway**: Easy FastAPI deployment with persistent storage
- **Render**: Similar to Railway, good free tier
- **Fly.io**: Docker-based, great for background jobs
- **GitHub Actions**: Free scheduled jobs (already configured)

## 📝 API Usage

### Create Subscription

```bash
curl -X POST http://localhost:8000/api/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "playstore_url": "https://play.google.com/store/apps/details?id=com.whatsapp",
    "weeks": 4,
    "email": "user@example.com"
  }'
```

### Health Check

```bash
curl http://localhost:8000/health
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

[Add your license here]

## 🙏 Acknowledgments

- Groq for free LLM API access
- Playwright for browser automation
- FastAPI for the web framework

