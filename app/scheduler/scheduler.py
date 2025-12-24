"""
Scheduler Manager for App Review Insights Analyzer

Manages APScheduler instance with persistent job store and timezone handling.
"""

import logging
import os
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import pytz

from app.scheduler.config import SchedulerConfig
from app.scheduler.jobs import run_weekly_job
from app.scheduler.timezone_utils import ist_to_utc, get_next_monday_8am_ist

logger = logging.getLogger(__name__)


class SchedulerManager:
    """
    Manages the APScheduler instance for scheduled jobs.
    
    Features:
    - Persistent job store (SQLite)
    - IST timezone handling
    - Weekly recurring job (Monday 8 AM IST)
    - Safe restart handling
    """
    
    def __init__(self):
        self.scheduler: Optional[BackgroundScheduler] = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """
        Initialize the scheduler with configuration.
        
        Returns:
            True if initialized successfully, False otherwise
        """
        if self._initialized:
            logger.warning("Scheduler already initialized")
            return True
        
        if not SchedulerConfig.is_enabled():
            logger.info("Scheduler is disabled via configuration")
            return False
        
        try:
            # Ensure job store directory exists
            job_store_path = SchedulerConfig.JOB_STORE_URL.replace("sqlite:///", "")
            job_store_dir = os.path.dirname(job_store_path)
            if job_store_dir and not os.path.exists(job_store_dir):
                os.makedirs(job_store_dir, exist_ok=True)
            
            # Configure job store
            job_store = SQLAlchemyJobStore(url=SchedulerConfig.JOB_STORE_URL)
            
            # Configure executor
            executor = ThreadPoolExecutor(max_workers=SchedulerConfig.MAX_WORKERS)
            
            # Create scheduler with IST timezone
            # APScheduler uses UTC internally, so we'll convert IST times to UTC
            ist_tz = pytz.timezone('Asia/Kolkata')
            
            self.scheduler = BackgroundScheduler(
                jobstores={'default': job_store},
                executors={'default': executor},
                timezone=ist_tz,  # Set IST as default timezone
                job_defaults={
                    'coalesce': True,  # Combine multiple pending executions
                    'max_instances': 1,  # Only one instance of each job at a time
                    'misfire_grace_time': 300,  # 5 minutes grace period
                }
            )
            
            # Add event listeners
            self.scheduler.add_listener(self._on_job_executed, EVENT_JOB_EXECUTED)
            self.scheduler.add_listener(self._on_job_error, EVENT_JOB_ERROR)
            
            # Schedule weekly job
            self._schedule_weekly_job()
            
            self._initialized = True
            logger.info("Scheduler initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize scheduler: {e}", exc_info=True)
            return False
    
    def _schedule_weekly_job(self):
        """Schedule the weekly recurring job"""
        cron_config = SchedulerConfig.get_weekly_cron_time()
        
        # Schedule job for Monday 8 AM IST
        # APScheduler will handle timezone conversion internally
        self.scheduler.add_job(
            func=run_weekly_job,
            trigger='cron',
            day_of_week=cron_config['day_of_week'],  # 0 = Monday
            hour=cron_config['hour'],  # 8 AM
            minute=cron_config['minute'],  # 0
            id='weekly_review_analysis',
            name='Weekly Review Analysis Job',
            replace_existing=True,  # Replace if exists (safe restart)
        )
        
        logger.info(
            f"Scheduled weekly job: Monday {cron_config['hour']}:{cron_config['minute']:02d} IST"
        )
    
    def start(self) -> bool:
        """
        Start the scheduler.
        
        Returns:
            True if started successfully, False otherwise
        """
        if not self._initialized:
            if not self.initialize():
                return False
        
        if self.scheduler.running:
            logger.warning("Scheduler is already running")
            return True
        
        try:
            self.scheduler.start()
            logger.info("Scheduler started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}", exc_info=True)
            return False
    
    def stop(self, wait: bool = True) -> bool:
        """
        Stop the scheduler.
        
        Args:
            wait: Whether to wait for running jobs to complete
            
        Returns:
            True if stopped successfully, False otherwise
        """
        if not self.scheduler or not self.scheduler.running:
            logger.warning("Scheduler is not running")
            return True
        
        try:
            self.scheduler.shutdown(wait=wait)
            logger.info("Scheduler stopped successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to stop scheduler: {e}", exc_info=True)
            return False
    
    def add_immediate_job(self, subscription_id: int) -> bool:
        """
        Add an immediate job for a new subscription.
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            True if job added successfully, False otherwise
        """
        if not self.scheduler or not self.scheduler.running:
            logger.warning("Scheduler not running, cannot add immediate job")
            return False
        
        try:
            from app.scheduler.jobs import trigger_immediate_analysis
            
            job_id = f"immediate_analysis_{subscription_id}"
            
            # Add job to run immediately
            self.scheduler.add_job(
                func=trigger_immediate_analysis,
                args=[subscription_id],
                trigger='date',  # Run once, immediately
                id=job_id,
                name=f'Immediate Analysis for Subscription {subscription_id}',
                replace_existing=True,
            )
            
            logger.info(f"Added immediate analysis job for subscription {subscription_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add immediate job: {e}", exc_info=True)
            return False
    
    def _on_job_executed(self, event):
        """Handle job execution event"""
        logger.info(
            f"Job executed: {event.job_id}",
            extra={
                'job_id': event.job_id,
                'job_retval': str(event.retval) if event.retval else None,
            }
        )
    
    def _on_job_error(self, event):
        """Handle job error event"""
        logger.error(
            f"Job error: {event.job_id} - {event.exception}",
            extra={
                'job_id': event.job_id,
                'exception': str(event.exception) if event.exception else None,
                'traceback': event.traceback if hasattr(event, 'traceback') else None,
            },
            exc_info=event.exception if event.exception else None
        )
    
    def get_jobs(self) -> list:
        """Get list of scheduled jobs"""
        if not self.scheduler:
            return []
        return self.scheduler.get_jobs()
    
    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self.scheduler is not None and self.scheduler.running


# Global scheduler instance
_scheduler_manager: Optional[SchedulerManager] = None


def get_scheduler_manager() -> SchedulerManager:
    """
    Get the global scheduler manager instance.
    
    Returns:
        SchedulerManager instance
    """
    global _scheduler_manager
    if _scheduler_manager is None:
        _scheduler_manager = SchedulerManager()
    return _scheduler_manager






