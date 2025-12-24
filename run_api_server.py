"""
Run the FastAPI server for the UI module with scheduler

Usage:
    python run_api_server.py
"""

import uvicorn
import logging
from app.scheduler import get_scheduler_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Initialize and start scheduler
    scheduler_manager = get_scheduler_manager()
    if scheduler_manager.initialize():
        if scheduler_manager.start():
            logger.info("Scheduler started successfully")
        else:
            logger.error("Failed to start scheduler")
    else:
        logger.warning("Scheduler initialization skipped (disabled or failed)")
    
    try:
        # Start FastAPI server
        uvicorn.run(
            "app.api.server:app",
            host="0.0.0.0",
            port=8000,
            reload=False,  # Disable reload to avoid scheduler issues
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        # Stop scheduler on shutdown
        scheduler_manager.stop(wait=True)
        logger.info("Scheduler stopped")



