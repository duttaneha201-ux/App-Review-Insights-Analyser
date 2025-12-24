# Scheduler Module

Module 9: Scheduler for App Review Insights Analyzer

## Overview

The scheduler module reliably triggers weekly review extraction, analysis, synthesis, and email delivery every Monday at 8:00 AM IST, with correct timezone handling, observability, and failure recovery.

## Features

- **Persistent Job Store**: Uses SQLite-compatible job store for reliability across restarts
- **Timezone Handling**: Correctly handles IST (Asia/Kolkata) as source of truth, converts to UTC internally
- **Immediate Jobs**: Triggers analysis immediately when a subscription is created
- **Weekly Recurring Jobs**: Runs every Monday at 8 AM IST for all active subscriptions
- **Idempotency**: Prevents duplicate processing of the same weekly batch
- **Structured Logging**: Comprehensive logging for job execution, success, and failures
- **Failure Handling**: Captures errors and marks jobs as failed without automatic retries (configurable)

## Architecture

### Components

1. **`timezone_utils.py`**: Timezone conversion utilities (IST ↔ UTC)
2. **`config.py`**: Environment-driven configuration
3. **`scheduler.py`**: APScheduler manager with persistent job store
4. **`jobs.py`**: Job definitions (immediate and weekly)

### Job Types

#### A. Immediate Analysis Job
- Triggered when a new subscription is created
- Runs end-to-end pipeline:
  - Fetch reviews
  - Clean & deduplicate
  - Store weekly batch
  - Generate themes
  - Generate weekly pulse
  - Send email

#### B. Weekly Recurring Job
- Runs every Monday at 8:00 AM IST
- For each active subscription:
  - Identifies the correct weekly window (last complete week)
  - Skips if already processed (idempotency)
  - Triggers the same pipeline as above

## Configuration

Environment variables (in `.env`):

```bash
# Enable/disable scheduler
SCHEDULER_ENABLED=true

# Timezone (IST is source of truth)
SCHEDULER_TIMEZONE=Asia/Kolkata

# Weekly job schedule (Monday = 0)
SCHEDULER_WEEKLY_DAY=0        # Monday
SCHEDULER_WEEKLY_HOUR=8      # 8 AM
SCHEDULER_WEEKLY_MINUTE=0

# Job store (SQLite)
SCHEDULER_JOB_STORE_URL=sqlite:///./data/scheduler_jobs.db

# Execution settings
SCHEDULER_MAX_WORKERS=4

# Retry settings (disabled for MVP)
SCHEDULER_AUTO_RETRY=false
SCHEDULER_MAX_RETRIES=0

# Logging
SCHEDULER_LOG_LEVEL=INFO
```

## Usage

### Starting the Scheduler

The scheduler is automatically started when you run the API server:

```bash
python run_api_server.py
```

The scheduler initializes and starts in the background, scheduling:
1. Weekly recurring job (Monday 8 AM IST)
2. Immediate jobs as subscriptions are created

### Manual Scheduler Control

```python
from app.scheduler import get_scheduler_manager

# Get scheduler manager
scheduler = get_scheduler_manager()

# Initialize (if not already done)
scheduler.initialize()

# Start scheduler
scheduler.start()

# Add immediate job for a subscription
scheduler.add_immediate_job(subscription_id=1)

# Stop scheduler
scheduler.stop(wait=True)
```

### Programmatic Job Triggering

```python
from app.scheduler.jobs import trigger_immediate_analysis, run_weekly_job

# Trigger immediate analysis for a subscription
result = trigger_immediate_analysis(subscription_id=1)

# Run weekly job manually (for testing)
result = run_weekly_job()
```

## Idempotency

The scheduler ensures jobs do not reprocess the same weekly batch twice:

1. **Batch Check**: Before processing, checks if a batch exists for the week
2. **Status Check**: Verifies batch status is not already 'processed'
3. **Pulse Check**: Confirms weekly pulse note exists
4. **Skip Logic**: If all checks pass, skips processing and returns success

## Logging

Structured logs include:

- **Job Start**: `[JOB_START]` with job type and context
- **Job Success**: `[JOB_SUCCESS]` with execution time and stats
- **Job Failure**: `[JOB_FAILURE]` with error message and traceback

Log fields:
- `job_type`: Type of job (immediate_analysis, weekly_recurring)
- `subscription_id`: Subscription ID (if applicable)
- `app_id`: App ID
- `week_start` / `week_end`: Week date range
- `execution_time`: Job execution time in seconds
- `status`: success/failed
- `error`: Error message (if failed)
- `traceback`: Full traceback (if failed)

## Timezone Handling

**Critical**: IST (Asia/Kolkata) is the source of truth for business logic.

- All scheduling logic converts IST times to UTC internally
- APScheduler uses IST timezone as default
- Cron jobs are scheduled in IST timezone
- Monday 8:00 AM IST is respected regardless of server timezone

### Timezone Utilities

```python
from app.scheduler.timezone_utils import (
    get_ist_now,
    get_utc_now,
    ist_to_utc,
    utc_to_ist,
    get_next_monday_8am_ist,
    get_week_start_date,
    get_week_end_date,
)

# Get current time in IST
now_ist = get_ist_now()

# Convert IST to UTC
utc_time = ist_to_utc(ist_time)

# Get next Monday 8 AM IST
next_monday = get_next_monday_8am_ist()

# Get week start/end dates
week_start = get_week_start_date()  # Monday
week_end = get_week_end_date()       # Sunday
```

## Failure Handling

On failure:

1. **Error Capture**: Stack trace and error context are captured
2. **Job Marking**: Job is marked as failed (via logging)
3. **Notification**: Failure is logged (email notification stub for future)
4. **No Auto-Retry**: Jobs do not retry automatically (configurable via `SCHEDULER_AUTO_RETRY`)

## Testing

Run unit tests:

```bash
pytest tests/test_scheduler.py -v
```

Tests cover:
- Timezone conversion (IST ↔ UTC)
- Immediate job triggering
- Weekly job scheduling
- Idempotency checks
- Failure handling
- Scheduler manager initialization

## Database

The scheduler uses two databases:

1. **Main Database** (`data/reviews.db`): Stores apps, subscriptions, batches, reviews, themes, pulse notes
2. **Job Store** (`data/scheduler_jobs.db`): Stores APScheduler job metadata (managed by APScheduler)

## Safe Restart Behavior

The scheduler is designed to be safe to restart:

- **Job Persistence**: Jobs are stored in SQLite, survive restarts
- **Replace Existing**: Jobs with same ID are replaced (no duplicates)
- **Coalesce**: Multiple pending executions are combined
- **Max Instances**: Only one instance of each job runs at a time
- **Misfire Grace**: 5-minute grace period for missed jobs

## Monitoring

### Check Scheduler Status

```python
from app.scheduler import get_scheduler_manager

scheduler = get_scheduler_manager()

# Check if running
if scheduler.is_running():
    # Get scheduled jobs
    jobs = scheduler.get_jobs()
    for job in jobs:
        print(f"Job: {job.id}, Next Run: {job.next_run_time}")
```

### View Job Logs

Check application logs for structured job execution logs:

```bash
# Filter for job logs
grep "JOB_" logs/app.log
```

## Troubleshooting

### Scheduler Not Starting

1. Check `SCHEDULER_ENABLED=true` in `.env`
2. Verify job store directory exists (`data/`)
3. Check logs for initialization errors

### Jobs Not Running

1. Verify scheduler is running: `scheduler.is_running()`
2. Check job store database: `data/scheduler_jobs.db`
3. Verify timezone configuration
4. Check logs for job execution errors

### Duplicate Processing

1. Verify idempotency checks are working
2. Check batch status in database
3. Ensure `replace_existing=True` in job scheduling

## Future Enhancements

- Email notifications on job failures
- Automatic retry with exponential backoff
- Job execution history table
- Web UI for job monitoring
- Metrics and alerting integration






