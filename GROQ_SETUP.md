# Groq Setup Instructions

## What is Groq?

Groq provides **free, fast access** to powerful LLM models like:
- **Llama 3.1 70B** (default) - Fast and capable
- **Mixtral 8x7B** - Great for complex tasks
- **Gemma 2 9B** - Lightweight and efficient

All models are **free to use** with generous rate limits!

---

## Step 1: Get Your Free API Key

1. Go to **https://console.groq.com/**
2. Sign up for a free account (Google/GitHub login available)
3. Navigate to **API Keys** section
4. Click **"Create API Key"**
5. Copy your API key (starts with `gsk_...`)

---

## Step 2: Set Environment Variable

### Option A: Windows (PowerShell)
```powershell
$env:GROQ_API_KEY="your-api-key-here"
```

### Option B: Windows (Command Prompt)
```cmd
set GROQ_API_KEY=your-api-key-here
```

### Option C: Linux/Mac
```bash
export GROQ_API_KEY="your-api-key-here"
```

### Option D: Create `.env` file (Recommended)
Create a `.env` file in the project root:
```
GROQ_API_KEY=your-api-key-here
```

The code will automatically load it using `python-dotenv`.

---

## Step 3: Install Groq Package

```bash
pip install groq
```

Or if using requirements.txt:
```bash
pip install -r requirements.txt
```

---

## Step 4: Verify Setup

Test your setup:

```python
from app.services.theme_chunker import ThemeChunker

# This will use GROQ_API_KEY from environment
chunker = ThemeChunker()

# Or pass directly
chunker = ThemeChunker(api_key="your-api-key-here")
```

---

## Available Models

You can use different models by passing the `model` parameter:

```python
# Default (Llama 3.1 70B - recommended)
chunker = ThemeChunker(model="llama-3.1-70b-versatile")

# Mixtral 8x7B (great for complex analysis)
chunker = ThemeChunker(model="mixtral-8x7b-32768")

# Gemma 2 9B (fast and lightweight)
chunker = ThemeChunker(model="gemma2-9b-it")
```

---

## Rate Limits

Groq provides generous free tier limits:
- **30 requests per minute** (default)
- **Fast response times** (usually < 1 second)
- **No credit card required**

If you hit rate limits, the code will automatically retry with exponential backoff.

---

## Troubleshooting

### Error: "Groq API key is required"
- Make sure you've set `GROQ_API_KEY` environment variable
- Or pass `api_key` parameter directly to `ThemeChunker()`
- Check that the key starts with `gsk_`

### Error: "groq package is required"
```bash
pip install groq
```

### Error: "Rate limit exceeded"
- Wait a minute and try again
- Groq resets rate limits every minute
- Consider using a different model (some have higher limits)

### Error: "Invalid API key"
- Verify your key at https://console.groq.com/
- Make sure there are no extra spaces in the key
- Try creating a new API key

---

## Example Usage

```python
from app.services.theme_chunker import ThemeChunker
from app.models.review import Review
from datetime import date, timedelta

# Initialize chunker (uses GROQ_API_KEY from environment)
chunker = ThemeChunker()

# Process reviews
reviews = [...]  # Your Review objects
start_date = date.today() - timedelta(days=84)
end_date = date.today() - timedelta(days=7)

# Get aggregated themes
themes = chunker.process_reviews(reviews, start_date, end_date)

for theme in themes:
    print(f"Theme: {theme.theme}")
    print(f"Key Points: {theme.key_points}")
    print(f"Quotes: {theme.candidate_quotes}")
    print()
```

---

## Cost

**100% FREE!** 🎉

Groq provides free access to all models. No credit card required, no hidden fees.

---

## Support

- **Groq Console**: https://console.groq.com/
- **Groq Documentation**: https://console.groq.com/docs
- **Groq Discord**: Join their community for help

