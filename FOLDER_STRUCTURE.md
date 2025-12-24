# Folder Structure Documentation

This document describes the organization and purpose of each directory and key file in the repository.

## 📁 Root Directory

### Core Application Files

- **`run_api_server.py`**: Main entry point for the FastAPI server. Initializes scheduler and starts Uvicorn.
- **`start_frontend_simple.py`**: Simple HTTP server for serving the standalone HTML frontend.
- **`start_servers.bat`** / **`start_servers.sh`**: Convenience scripts to start both backend and frontend servers.

### Configuration Files

- **`requirements.txt`**: Python package dependencies
- **`pytest.ini`**: Pytest configuration
- **`alembic.ini`**: Alembic database migration configuration
- **`.gitignore`**: Git ignore patterns (excludes `__pycache__`, `.env`, databases, etc.)

### Documentation Files

- **`README.md`**: Main project documentation and quick start guide
- **`DEPENDENCIES_AND_CREDENTIALS.md`**: Setup guide for API keys and credentials
- **`GROQ_SETUP.md`**: Detailed Groq API setup instructions
- **`SMTP_SETUP.md`**: Email service configuration guide
- **`PROJECT_ROADMAP.md`**: Development roadmap and module status
- **`QUICK_START_UI.md`**: Frontend setup and usage guide
- **`FOLDER_STRUCTURE.md`**: This file

### Module Summaries (Historical)

- `MODULE_2_SUMMARY.md` through `MODULE_7_SUMMARY.md`: Historical module completion summaries
- `UI_MODULE_SUMMARY.md`, `STORAGE_LAYER_INTEGRATION.md`: Integration summaries

---

## 📁 `app/` - Main Application Code

### `app/api/` - FastAPI REST API

- **`server.py`**: FastAPI application instance, CORS configuration, route definitions
- **`subscriptions.py`**: Subscription creation endpoint, request/response models

### `app/db/` - Database Layer

- **`database.py`**: SQLAlchemy engine, session management, connection utilities
- **`models.py`**: SQLAlchemy ORM models (App, Subscription, Review, WeeklyBatch, WeeklyPulseNote)
- **`repository.py`**: Repository pattern implementations for data access
- **`backup.py`**: Database backup and export utilities (JSON/CSV)
- **`README.md`**: Database schema documentation

### `app/models/` - Domain Models

- **`review.py`**: Review domain model (Pydantic)
- **`__init__.py`**: Model exports

### `app/scheduler/` - Task Scheduling

- **`scheduler.py`**: APScheduler manager, job store configuration
- **`jobs.py`**: Job definitions (immediate analysis, weekly recurring)
- **`config.py`**: Scheduler configuration (timezone, cron schedule, etc.)
- **`timezone_utils.py`**: IST/UTC conversion utilities
- **`README.md`**: Scheduler documentation

### `app/services/` - Business Logic Services

- **`url_validator.py`**: Play Store URL validation and verification
- **`review_extractor.py`**: Playwright-based review scraping
- **`cleaning_service.py`**: Text cleaning, PII detection/scrubbing, deduplication
- **`theme_chunker.py`**: LLM-based theme identification and chunking
- **`weekly_synthesis.py`**: Weekly pulse generation using LLM
- **`llm_orchestrator.py`**: Centralized LLM API client with retry logic
- **`email_service.py`**: SMTP email sending service

### `app/pipeline.py` - Pipeline Orchestration

- End-to-end pipeline: extract → clean → synthesize → email
- Main function: `extract_clean_and_synthesize()`

---

## 📁 `alembic/` - Database Migrations

- **`env.py`**: Alembic environment configuration
- **`script.py.mako`**: Migration template
- **`versions/`**: Migration scripts
  - `f96d038bdb20_initial_schema.py`: Initial database schema

---

## 📁 `tests/` - Test Suite

### Unit Tests

- **`test_url_validator.py`**: URL validation service tests
- **`test_review_extractor.py`**: Review extraction tests
- **`test_cleaning_service.py`**: Cleaning and PII scrubbing tests
- **`test_theme_chunker.py`**: Theme chunking tests
- **`test_weekly_synthesis.py`**: Weekly synthesis tests
- **`test_email_service.py`**: Email service tests
- **`test_llm_orchestrator.py`**: LLM orchestrator tests

### Database Tests

- **`test_db_models.py`**: Database model tests
- **`test_db_repository.py`**: Repository pattern tests
- **`test_db_backup.py`**: Backup utility tests

### Integration Tests

- **`test_pipeline.py`**: End-to-end pipeline tests
- **`test_complete_pipeline.py`**: Complete flow integration test
- **`test_scheduler.py`**: Scheduler and job tests

---

## 📁 `scripts/` - Utility Scripts

- **`cli_extract_reviews.py`**: Command-line tool for extracting reviews
- **`view_subscriptions.py`**: Database viewer for subscriptions and batches

---

## 📁 `examples/` - Example Code

- **`use_storage_layer.py`**: Example of using the database repository layer

---

## 📁 `frontend/` - Frontend UI

### Next.js Application (Optional)

- **`app/`**: Next.js app directory
  - `page.tsx`: Main page component
  - `layout.tsx`: Root layout
  - `globals.css`: Global styles
- **`components/`**: React components
  - `SubscriptionForm.tsx`: Subscription form component
- **`package.json`**: Node.js dependencies
- **`next.config.js`**: Next.js configuration
- **`tsconfig.json`**: TypeScript configuration
- **`README.md`**: Frontend documentation

### Standalone HTML (Fallback)

- **`index.html`**: Standalone HTML frontend (works without Node.js)

---

## 📁 `data/` - Data Storage (Gitignored)

- **`reviews.db`**: Main SQLite database
- **`scheduler_jobs.db`**: APScheduler job store database

---

## 🗑️ Excluded from Repository

The following are excluded via `.gitignore`:

- **`__pycache__/`**: Python bytecode cache
- **`.env`**: Environment variables (API keys, credentials)
- **`*.db`**: Database files
- **`htmlcov/`**: Test coverage reports
- **`node_modules/`**: Node.js dependencies
- **`venv/`**, **`env/`**: Python virtual environments
- **`*.log`**: Log files

---

## 📊 File Count Summary

- **Core Application**: ~20 Python files in `app/`
- **Tests**: ~13 test files
- **Migrations**: 1 initial migration
- **Documentation**: ~15 markdown files
- **Scripts**: 2 utility scripts
- **Frontend**: Next.js app + standalone HTML

---

## 🔄 Typical Development Workflow

1. **Make changes** in `app/` modules
2. **Write tests** in `tests/`
3. **Run tests**: `pytest`
4. **Create migration** (if DB changes): `alembic revision --autogenerate -m "description"`
5. **Apply migration**: `alembic upgrade head`
6. **Test locally**: `python run_api_server.py`
7. **Commit and push**

---

## 📝 Notes

- All Python code follows PEP 8 style guidelines
- Type hints are used throughout
- Repository pattern is used for database access
- Services are designed to be testable and mockable
- Configuration is environment-driven (no hardcoded values)




