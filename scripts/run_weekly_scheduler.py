#!/usr/bin/env python3
"""
GitHub Actions Scheduler Entrypoint

This script runs the weekly review analysis job.
It is designed to be called by GitHub Actions scheduled workflows.

Features:
- Idempotent execution (skips already-processed batches)
- Structured logging
- Clear error reporting
- Safe to re-run
"""

import sys
import os
import logging
import traceback
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def validate_environment():
    """Validate that required environment variables are set."""
    required_vars = [
        'GROQ_API_KEY',
        'SMTP_HOST',
        'SMTP_USERNAME',
        'SMTP_PASSWORD',
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        error_msg = f"Missing required environment variables: {', '.join(missing)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("Environment validation passed")


def main():
    """Main entrypoint for weekly scheduler."""
    start_time = datetime.now()
    
    try:
        logger.info("=" * 80)
        logger.info("WEEKLY REVIEW ANALYSIS JOB STARTED")
        logger.info(f"Started at: {start_time.isoformat()}")
        logger.info("=" * 80)
        
        # Validate environment
        validate_environment()
        
        # Import here to ensure path is set
        from app.scheduler.jobs import run_weekly_job
        from app.scheduler.timezone_utils import get_ist_now
        
        # Log timezone info
        ist_now = get_ist_now()
        logger.info(f"Current IST time: {ist_now.isoformat()}")
        
        # Run the weekly job
        logger.info("Executing weekly job...")
        result = run_weekly_job()
        
        # Calculate execution time
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Log results
        logger.info("=" * 80)
        logger.info("WEEKLY REVIEW ANALYSIS JOB COMPLETED")
        logger.info(f"Completed at: {end_time.isoformat()}")
        logger.info(f"Execution time: {execution_time:.2f} seconds")
        logger.info(f"Success: {result.get('success', False)}")
        logger.info(f"Processed count: {result.get('processed_count', 0)}")
        logger.info(f"Error count: {result.get('error_count', 0)}")
        
        if result.get('errors'):
            logger.warning(f"Errors encountered: {len(result['errors'])}")
            for error in result['errors']:
                logger.warning(f"  - Subscription {error.get('subscription_id')}: {error.get('error')}")
        
        logger.info("=" * 80)
        
        # Exit with error code if job failed
        if not result.get('success', False):
            logger.error("Weekly job failed")
            if result.get('error'):
                logger.error(f"Error: {result['error']}")
            sys.exit(1)
        
        # Exit with error code if there were processing errors
        if result.get('error_count', 0) > 0:
            logger.warning(f"Job completed with {result['error_count']} errors")
            # Don't fail the whole job if some subscriptions failed
            # This allows partial success
        
        logger.info("Weekly job completed successfully")
        sys.exit(0)
        
    except ValueError as e:
        # Environment validation errors
        logger.error(f"Configuration error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
        
    except Exception as e:
        # Unexpected errors
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        logger.error("=" * 80)
        logger.error("WEEKLY REVIEW ANALYSIS JOB FAILED")
        logger.error(f"Failed at: {end_time.isoformat()}")
        logger.error(f"Execution time: {execution_time:.2f} seconds")
        logger.error(f"Error: {str(e)}")
        logger.error("=" * 80)
        logger.error("Full traceback:")
        logger.error(traceback.format_exc())
        logger.error("=" * 80)
        
        sys.exit(1)


if __name__ == '__main__':
    main()

