# Project Roadmap - What's Done & What's Next

## ✅ Completed Modules

### Module 1: URL Validation Service ✅
- **Status**: Complete with tests
- **Files**: `app/services/url_validator.py`, `tests/test_url_validator.py`
- **Features**: URL validation, app ID extraction, app existence verification

### Module 2: Review Extraction Service ✅
- **Status**: Complete with tests
- **Files**: `app/services/review_extractor.py`, `tests/test_review_extractor.py`
- **Features**: Playwright scraping, date filtering, sampling, modal extraction

### Module 3: Cleaning & PII Scrubber ✅
- **Status**: Complete with tests, integrated into Module 2
- **Files**: `app/services/cleaning_service.py`, `tests/test_cleaning_service.py`
- **Features**: Text cleaning, PII detection/rewriting, fuzzy deduplication

### Module 4: Theme Chunking Engine ✅
- **Status**: Complete with tests
- **Files**: `app/services/theme_chunker.py`, `tests/test_theme_chunker.py`
- **Features**: Week-based chunking, LLM theme identification (Groq), aggregation

### Pipeline Integration ✅
- **Status**: Complete
- **Files**: `app/pipeline.py`, `cli_extract_reviews.py`
- **Features**: End-to-end pipeline, CLI tool

---

## 🚧 Next Steps (In Order)

### Module 5: Weekly Synthesis Engine ⭐ **NEXT PRIORITY**

**What it does:**
- Takes aggregated themes from Module 4
- Generates a single "Weekly Product Pulse" using LLM
- Outputs executive-friendly summary (≤250 words)
- Includes: title, overview, top 3 themes, quotes, actions

**Requirements:**
- [ ] Aggregate theme summaries into one LLM call
- [ ] Select Top 3 themes based on frequency & impact
- [ ] Generate concise weekly pulse (≤250 words)
- [ ] Executive-friendly, neutral tone
- [ ] Automatic compression if word count exceeds 250
- [ ] Output JSON format with title, overview, themes, quotes, actions

**Dependencies:**
- Uses Groq API (already set up)
- Input: AggregatedTheme objects from Module 4

**Estimated Complexity:** Medium
**Estimated Time:** 2-3 hours

---

### Module 6: Storage Layer

**What it does:**
- Stores reviews week-by-week
- Stores weekly pulse artifacts
- Manages subscriptions

**Requirements:**
- [ ] Database schema design (SQLite/PostgreSQL)
- [ ] ORM models (SQLAlchemy)
- [ ] CRUD operations for reviews
- [ ] CRUD operations for weekly pulses
- [ ] Subscription management
- [ ] Migration scripts

**Options:**
- SQLite (simple, file-based)
- PostgreSQL (production-ready)
- Airtable (if preferred)

**Estimated Complexity:** Medium
**Estimated Time:** 2-3 hours

---

### Module 7: Email Composer & Sender

**What it does:**
- Generates HTML email from weekly pulse
- Sends emails via email service
- Formats for different audiences (Product, Support, Leadership)

**Requirements:**
- [ ] HTML email templates
- [ ] Email service integration (SendGrid/SMTP/AWS SES)
- [ ] Audience-specific formatting
- [ ] Email validation
- [ ] Error handling

**Dependencies:**
- Email service API key (SendGrid recommended - free tier available)

**Estimated Complexity:** Medium
**Estimated Time:** 2-3 hours

---

### Module 8: Scheduler / Cron Jobs

**What it does:**
- Triggers weekly analysis every Monday at 8am IST
- Manages recurring jobs
- Handles job failures and retries

**Requirements:**
- [ ] Task queue setup (Celery/APScheduler)
- [ ] IST timezone conversion
- [ ] Weekly job triggers
- [ ] Job monitoring/logging
- [ ] Failure notifications

**Options:**
- APScheduler (simple, in-process)
- Celery + Redis (production-ready, distributed)

**Estimated Complexity:** Medium-High
**Estimated Time:** 3-4 hours

---

### Module 9: Frontend UI

**What it does:**
- User interface for entering Play Store URL
- Time range selector (1-12 weeks)
- Email subscription form
- Status dashboard

**Requirements:**
- [ ] Web framework (Flask/FastAPI)
- [ ] HTML templates
- [ ] Form handling
- [ ] API endpoints
- [ ] Error display
- [ ] Loading states

**Options:**
- Flask + Bootstrap (simple)
- FastAPI + React (modern)

**Estimated Complexity:** Medium-High
**Estimated Time:** 4-5 hours

---

## 📊 Current Status Summary

| Module | Status | Tests | Integration |
|--------|--------|-------|-------------|
| 1. URL Validation | ✅ Complete | ✅ 27 tests | ✅ Integrated |
| 2. Review Extraction | ✅ Complete | ✅ 37 tests | ✅ Integrated |
| 3. Cleaning & PII | ✅ Complete | ✅ 17 tests | ✅ Integrated |
| 4. Theme Chunking | ✅ Complete | ✅ 16 tests | ✅ Ready |
| 5. Weekly Synthesis | ⏳ **NEXT** | ⏳ Pending | ⏳ Pending |
| 6. Storage Layer | ⏳ Pending | ⏳ Pending | ⏳ Pending |
| 7. Email Service | ⏳ Pending | ⏳ Pending | ⏳ Pending |
| 8. Scheduler | ⏳ Pending | ⏳ Pending | ⏳ Pending |
| 9. Frontend | ⏳ Pending | ⏳ Pending | ⏳ Pending |

**Total Progress: 4/9 modules (44%)**

---

## 🎯 Recommended Next Steps

### Option A: Continue Core Logic (Recommended)
**Build Module 5: Weekly Synthesis Engine**
- Completes the analysis pipeline
- Can test end-to-end: Extract → Clean → Theme → Synthesize
- No new dependencies needed (uses existing Groq setup)

### Option B: Add Storage
**Build Module 6: Storage Layer**
- Enables persistence of reviews and insights
- Required before scheduling/email
- Can use SQLite for simplicity

### Option C: Add Frontend
**Build Module 9: Frontend UI**
- Makes system user-friendly
- Can test manually without scheduling
- Good for demos

---

## 🔄 Current Pipeline Flow

**What Works Now:**
```
Play Store URL
    ↓
URL Validation (Module 1)
    ↓
Extract Reviews (Module 2)
    ↓
Clean & Scrub PII (Module 3)
    ↓
Identify Themes (Module 4)
    ↓
❌ Weekly Synthesis (Module 5) ← **STOPS HERE**
```

**What's Missing:**
- Weekly Synthesis (Module 5)
- Storage (Module 6)
- Email (Module 7)
- Scheduling (Module 8)
- Frontend (Module 9)

---

## 💡 Recommendation

**Build Module 5 next** because:
1. ✅ Completes the core analysis pipeline
2. ✅ No new dependencies (uses Groq)
3. ✅ Can test end-to-end immediately
4. ✅ Natural progression from Module 4
5. ✅ Required before email/scheduling

After Module 5, you'll have a complete analysis pipeline that can:
- Extract reviews
- Clean and deduplicate
- Identify themes
- Generate executive summaries

Then you can add storage, email, and scheduling to make it production-ready.

---

## 📝 Quick Start for Module 5

If you want to build Module 5 now, here's what it needs:

1. **Input**: List of `AggregatedTheme` objects from Module 4
2. **Process**: Single LLM call to Groq to synthesize themes
3. **Output**: Weekly Product Pulse JSON:
   ```json
   {
     "title": "...",
     "overview": "...",
     "themes": [{"name": "...", "summary": "..."}],
     "quotes": ["...", "...", "..."],
     "actions": ["...", "...", "..."]
   }
   ```
4. **Constraints**: ≤250 words total, top 3 themes, executive-friendly

Would you like me to build Module 5 now?

