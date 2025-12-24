"""
Scheduler configuration

Environment-driven configuration for the scheduler module.
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class SchedulerConfig:
    """Configuration for scheduler"""
    
    # Enable/disable scheduler
    ENABLED: bool = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
    
    # Timezone (IST is source of truth)
    TIMEZONE: str = os.getenv("SCHEDULER_TIMEZONE", "Asia/Kolkata")
    
    # Weekly job schedule (cron format: day_of_week hour minute)
    # Monday = 0, 8 AM IST
    WEEKLY_JOB_DAY: int = int(os.getenv("SCHEDULER_WEEKLY_DAY", "0"))  # Monday
    WEEKLY_JOB_HOUR: int = int(os.getenv("SCHEDULER_WEEKLY_HOUR", "8"))  # 8 AM
    WEEKLY_JOB_MINUTE: int = int(os.getenv("SCHEDULER_WEEKLY_MINUTE", "0"))
    
    # Job store (SQLite for persistence)
    JOB_STORE_URL: str = os.getenv(
        "SCHEDULER_JOB_STORE_URL",
        "sqlite:///./data/scheduler_jobs.db"
    )
    
    # Job execution settings
    MAX_WORKERS: int = int(os.getenv("SCHEDULER_MAX_WORKERS", "4"))
    
    # Retry settings (disabled for MVP)
    AUTO_RETRY_ENABLED: bool = os.getenv("SCHEDULER_AUTO_RETRY", "false").lower() == "true"
    MAX_RETRIES: int = int(os.getenv("SCHEDULER_MAX_RETRIES", "0"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("SCHEDULER_LOG_LEVEL", "INFO")
    
    @classmethod
    def is_enabled(cls) -> bool:
        """Check if scheduler is enabled"""
        return cls.ENABLED
    
    @classmethod
    def get_weekly_cron_time(cls) -> dict:
        """
        Get weekly cron schedule configuration.
        
        Returns:
            dict with 'day_of_week', 'hour', 'minute' for APScheduler
        """
        return {
            'day_of_week': cls.WEEKLY_JOB_DAY,
            'hour': cls.WEEKLY_JOB_HOUR,
            'minute': cls.WEEKLY_JOB_MINUTE,
        }






