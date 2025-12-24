# Storage Layer (Module 8)

Database storage layer for App Review Insights Analyzer using SQLite + SQLAlchemy ORM.

## Overview

This module provides persistent storage for:
- App metadata
- Email subscriptions
- Weekly processing batches
- Reviews (with deduplication)
- Theme summaries
- Weekly pulse notes

## Database Schema

### Tables

1. **apps**: App metadata
   - `id` (PK)
   - `playstore_app_id` (unique)
   - `app_name`
   - `app_url`
   - `created_at`

2. **subscriptions**: Email subscriptions
   - `id` (PK)
   - `app_id` (FK → apps.id)
   - `email`
   - `start_date`
   - `end_date` (nullable)
   - `is_active`
   - `created_at`

3. **weekly_batches**: Weekly processing batches
   - `id` (PK)
   - `app_id` (FK → apps.id)
   - `week_start_date`
   - `week_end_date`
   - `status` (pending | processed | failed)
   - `created_at`
   - `updated_at`
   - Unique constraint: `(app_id, week_start_date)`

4. **reviews**: Individual reviews
   - `id` (PK)
   - `app_id` (FK → apps.id)
   - `weekly_batch_id` (FK → weekly_batches.id, nullable)
   - `rating` (1-5)
   - `title`
   - `text`
   - `review_date`
   - `review_hash` (unique, for deduplication)
   - `created_at`

5. **theme_summaries**: Theme analysis results
   - `id` (PK)
   - `weekly_batch_id` (FK → weekly_batches.id)
   - `theme_name`
   - `key_points` (JSON array)
   - `candidate_quotes` (JSON array)
   - `created_at`

6. **weekly_pulse_notes**: Final weekly pulse artifacts
   - `id` (PK)
   - `weekly_batch_id` (FK → weekly_batches.id, unique)
   - `title`
   - `overview`
   - `themes` (JSON array of `{name, summary}`)
   - `quotes` (JSON array)
   - `actions` (JSON array)
   - `word_count`
   - `created_at`

## Setup

### 1. Install Dependencies

```bash
pip install sqlalchemy alembic
```

### 2. Run Migrations

```bash
# Create initial schema
alembic upgrade head

# Check current revision
alembic current

# Create new migration (if schema changes)
alembic revision --autogenerate -m "Description"

# Rollback (if needed)
alembic downgrade -1
```

### 3. Initialize Database

```python
from app.db.database import init_db

init_db()  # Creates all tables (use after migrations)
```

## Usage

### Repository Pattern

All database access goes through repository classes:

```python
from app.db.database import get_db_session
from app.db.repository import (
    AppRepository,
    WeeklyBatchRepository,
    ReviewRepository,
    ThemeSummaryRepository,
    WeeklyPulseNoteRepository,
)

# Get or create app
with get_db_session() as session:
    app = AppRepository.get_or_create_by_playstore_id(
        session,
        playstore_app_id="com.whatsapp",
        app_name="WhatsApp",
        app_url="https://play.google.com/store/apps/details?id=com.whatsapp",
    )
    session.commit()

# Create weekly batch (idempotent)
with get_db_session() as session:
    batch = WeeklyBatchRepository.get_or_create(
        session,
        app_id=app.id,
        week_start_date=date(2024, 1, 1),
        week_end_date=date(2024, 1, 7),
    )
    session.commit()

# Bulk insert reviews with deduplication
with get_db_session() as session:
    reviews = [Review(rating=5, title="Great", text="Great app!", date=date.today())]
    inserted_count = ReviewRepository.bulk_insert_with_deduplication(
        session,
        app_id=app.id,
        weekly_batch_id=batch.id,
        reviews=reviews,
    )
    session.commit()

# Insert theme summaries
with get_db_session() as session:
    themes = [
        {
            "theme_name": "Performance",
            "key_points": ["Slow", "Crashes"],
            "candidate_quotes": ["Very slow"],
        }
    ]
    ThemeSummaryRepository.bulk_insert(
        session,
        weekly_batch_id=batch.id,
        themes=themes,
    )
    session.commit()

# Create or update weekly pulse note (idempotent)
with get_db_session() as session:
    pulse = WeeklyPulseNoteRepository.create_or_update(
        session,
        weekly_batch_id=batch.id,
        title="Weekly Product Pulse",
        overview="Overview text",
        themes=[{"name": "Theme", "summary": "Summary"}],
        quotes=["Quote 1"],
        actions=["Action 1"],
        word_count=150,
    )
    session.commit()
```

### Backup & Export

```python
from app.db.backup import (
    export_reviews_to_json,
    export_reviews_to_csv,
    export_pulse_notes_to_json,
    export_pulse_notes_to_csv,
    backup_database,
)
from pathlib import Path

with get_db_session() as session:
    # Export reviews
    export_reviews_to_json(session, Path("exports/reviews.json"), app_id=1)
    export_reviews_to_csv(session, Path("exports/reviews.csv"), app_id=1)
    
    # Export pulse notes
    export_pulse_notes_to_json(session, Path("exports/pulses.json"), app_id=1)
    export_pulse_notes_to_csv(session, Path("exports/pulses.csv"), app_id=1)
    
    # Backup database
    backup_path = backup_database(Path("backups"))
    print(f"Backup created: {backup_path}")
```

## Configuration

### Database URL

Set via environment variable or default:

```python
# Default: sqlite:///data/reviews.db
# Override: DATABASE_URL=sqlite:///path/to/custom.db
```

### SQL Logging

Enable SQL query logging:

```bash
export SQL_ECHO=true
```

## Testing

Run tests:

```bash
pytest tests/test_db_models.py
pytest tests/test_db_repository.py
pytest tests/test_db_backup.py
```

Tests use in-memory SQLite database (no file I/O).

## Key Features

### Idempotency

- `get_or_create` methods ensure safe re-runs
- Weekly batches are unique per app/week
- Reviews are deduplicated by hash
- Pulse notes are unique per batch

### Deduplication

Reviews are deduplicated using SHA256 hash of:
- Rating
- Text content
- Review date

### Foreign Key Integrity

All relationships use proper foreign keys with CASCADE delete:
- Deleting an app deletes all related data
- Deleting a batch deletes reviews, themes, and pulse notes

### JSON Fields

Theme summaries and pulse notes use JSON columns for flexible storage:
- `key_points`: List of strings
- `candidate_quotes`: List of strings
- `themes`: List of `{name, summary}` objects
- `quotes`: List of strings
- `actions`: List of strings

## Migration to PostgreSQL

The schema is designed to be PostgreSQL-ready:

1. Change database URL:
   ```python
   DATABASE_URL=postgresql://user:pass@localhost/dbname
   ```

2. Update Alembic configuration if needed

3. Run migrations:
   ```bash
   alembic upgrade head
   ```

No code changes required - SQLAlchemy handles the differences.

## File Structure

```
app/db/
├── __init__.py          # Module exports
├── database.py          # Connection & session management
├── models.py            # SQLAlchemy ORM models
├── repository.py        # Data access layer
├── backup.py            # Export & backup utilities
└── README.md            # This file

alembic/
├── env.py               # Alembic configuration
├── versions/            # Migration scripts
└── script.py.mako       # Migration template

tests/
├── test_db_models.py    # Model tests
├── test_db_repository.py # Repository tests
└── test_db_backup.py    # Backup/export tests
```

## Notes

- Database file location: `data/reviews.db` (default)
- Backup location: `backups/` (default)
- All timestamps use UTC
- Indexes are created automatically for common queries
- Check constraints are enforced at application level (SQLite limitation)








