# Dependencies and Credentials Guide

## 📦 Python Dependencies

All dependencies are listed in `requirements.txt`. Install with:
```bash
pip install -r requirements.txt
```

### Core Dependencies

| Package | Purpose | Required? | Notes |
|---------|---------|-----------|-------|
| `requests` | HTTP client for URL validation | ✅ Yes | No credentials needed |
| `urllib3` | HTTP library | ✅ Yes | No credentials needed |
| `playwright` | Browser automation for scraping | ✅ Yes | **Requires browser installation** |
| `beautifulsoup4` | HTML parsing | ✅ Yes | No credentials needed |
| `lxml` | XML/HTML parser | ✅ Yes | No credentials needed |
| `dateparser` | Date parsing | ✅ Yes | No credentials needed |
| `thefuzz` | Fuzzy string matching | ✅ Yes | No credentials needed |
| `python-Levenshtein` | String similarity | ✅ Yes | No credentials needed |
| `regex` | Advanced regex | ✅ Yes | No credentials needed |
| `groq` | LLM API client | ✅ Yes | **Requires API key** |
| `pytest` | Testing framework | ⚠️ Dev | Only for running tests |
| `pytest-cov` | Test coverage | ⚠️ Dev | Only for running tests |
| `python-dotenv` | Environment variables | ✅ Yes | For loading .env files |

---

## 🔑 Credentials Required

### 1. Groq API Key (Module 4) ⭐ REQUIRED

**What it's for:** Theme identification using LLM

**Status:** ✅ **FREE** - No credit card required

**How to get:**
1. Go to https://console.groq.com/
2. Sign up (Google/GitHub login available)
3. Navigate to "API Keys"
4. Click "Create API Key"
5. Copy your key (starts with `gsk_...`)

**How to set:**
```bash
# Windows PowerShell
$env:GROQ_API_KEY="gsk_your-key-here"

# Windows Command Prompt
set GROQ_API_KEY=gsk_your-key-here

# Linux/Mac
export GROQ_API_KEY="gsk_your-key-here"

# Or create .env file in project root
GROQ_API_KEY=gsk_your-key-here
```

**Rate Limits:**
- 30 requests per minute (free tier)
- Fast response times (< 1 second)
- No cost, no credit card needed

**Modules using it:**
- ✅ Module 4: Theme Chunking Engine

---

## 🖥️ System Dependencies

### Playwright Browsers (Module 2) ⭐ REQUIRED

**What it's for:** Scraping reviews from Play Store

**Status:** ✅ **FREE** - Open source

**Installation:**
```bash
# After installing playwright package
playwright install chromium
```

**What gets installed:**
- Chromium browser binary (~200MB)
- Browser dependencies

**Modules using it:**
- ✅ Module 2: Review Extraction Service

**Note:** Playwright requires browser binaries to be installed separately after installing the Python package.

---

## 📋 Complete Setup Checklist

### Step 1: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Install Playwright Browsers
```bash
playwright install chromium
```

### Step 3: Set Groq API Key
```bash
# Option A: Environment variable
$env:GROQ_API_KEY="gsk_your-key-here"  # Windows PowerShell

# Option B: .env file (recommended)
# Create .env file in project root:
GROQ_API_KEY=gsk_your-key-here
```

### Step 4: Verify Setup
```bash
# Test URL validation (no credentials needed)
python -m pytest tests/test_url_validator.py -v

# Test review extraction (needs Playwright browsers)
python -m pytest tests/test_review_extractor.py -v

# Test theme chunking (needs Groq API key)
python -m pytest tests/test_theme_chunker.py -v
```

---

## 🔒 Security Best Practices

### ✅ DO:
- Store API keys in environment variables
- Use `.env` file (add to `.gitignore`)
- Never commit API keys to version control
- Rotate API keys if exposed

### ❌ DON'T:
- Hardcode API keys in source code
- Commit `.env` files to git
- Share API keys publicly
- Use production keys in development

---

## 📝 Environment Variables Summary

| Variable | Required | Purpose | Default |
|----------|----------|---------|---------|
| `GROQ_API_KEY` | ✅ Yes (for Module 4) | Groq API authentication | None |
| `PLAYWRIGHT_BROWSERS_PATH` | ⚠️ Optional | Custom browser path | Auto-detect |

---

## 🧪 Testing Without Credentials

You can test most modules without credentials:

### ✅ No Credentials Needed:
- **Module 1**: URL Validation (uses requests, no auth)
- **Module 3**: Cleaning Service (local processing)

### ⚠️ Partial Testing:
- **Module 2**: Review Extraction (needs Playwright browsers, but can mock)
- **Module 4**: Theme Chunking (needs Groq API key, but can mock in tests)

**Run tests without credentials:**
```bash
# These work without any credentials
python -m pytest tests/test_url_validator.py -v
python -m pytest tests/test_cleaning_service.py -v

# These need setup but tests mock the APIs
python -m pytest tests/test_review_extractor.py -v
python -m pytest tests/test_theme_chunker.py -v
```

---

## 💰 Cost Summary

| Service | Cost | Notes |
|---------|------|-------|
| **Groq API** | ✅ FREE | Free tier with generous limits |
| **Playwright** | ✅ FREE | Open source, no cost |
| **All other dependencies** | ✅ FREE | Open source packages |

**Total Cost: $0.00** 🎉

---

## 🚨 Troubleshooting

### "Groq API key is required"
- Set `GROQ_API_KEY` environment variable
- Or pass `api_key` parameter to `ThemeChunker()`
- Verify key at https://console.groq.com/

### "playwright install chromium" fails
- Check internet connection
- Try: `python -m playwright install chromium`
- On Linux, may need: `sudo apt-get install libnss3 libatk-bridge2.0-0`

### "ModuleNotFoundError: No module named 'groq'"
```bash
pip install groq
```

### "ModuleNotFoundError: No module named 'playwright'"
```bash
pip install playwright
playwright install chromium
```

---

## 📦 Quick Install Script

Create `setup.sh` (Linux/Mac) or `setup.ps1` (Windows):

**Windows (setup.ps1):**
```powershell
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Prompt for Groq API key
$apiKey = Read-Host "Enter your Groq API key (get from https://console.groq.com/)"
[Environment]::SetEnvironmentVariable("GROQ_API_KEY", $apiKey, "User")

Write-Host "Setup complete! Restart your terminal for environment variable to take effect."
```

**Linux/Mac (setup.sh):**
```bash
#!/bin/bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Prompt for Groq API key
read -p "Enter your Groq API key (get from https://console.groq.com/): " api_key
echo "export GROQ_API_KEY=$api_key" >> ~/.bashrc

echo "Setup complete! Run: source ~/.bashrc"
```

---

## ✅ Verification

After setup, verify everything works:

```python
# Test 1: URL Validation (no credentials)
from app.services.url_validator import PlayStoreURLValidator
validator = PlayStoreURLValidator()
result = validator.validate_and_verify("https://play.google.com/store/apps/details?id=com.whatsapp")
print(f"URL Valid: {result['valid']}")

# Test 2: Theme Chunking (needs Groq API key)
from app.services.theme_chunker import ThemeChunker
chunker = ThemeChunker()  # Should work if GROQ_API_KEY is set
print(f"Theme Chunker initialized: {chunker.model}")
```

---

## 📚 Additional Resources

- **Groq Setup**: See `GROQ_SETUP.md`
- **Playwright Docs**: https://playwright.dev/python/
- **Environment Variables**: Use `.env` file with `python-dotenv`

---

## Summary

**Required Credentials:**
- ✅ **Groq API Key** (FREE) - For Module 4 only

**Required System Setup:**
- ✅ **Playwright Browsers** (FREE) - For Module 2 only

**All Other Dependencies:**
- ✅ Standard Python packages (no credentials needed)

**Total Cost: $0.00** 🎉

