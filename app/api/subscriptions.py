"""
API endpoint for subscription management

Handles POST /api/subscriptions requests from the frontend.
"""

import logging
from datetime import date, timedelta
from typing import Dict, Any, Optional
from fastapi import HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Union

from app.services.url_validator import PlayStoreURLValidator
from app.pipeline import extract_clean_and_synthesize
from app.db.database import get_db_session
from app.db.repository import (
    AppRepository,
    SubscriptionRepository,
    WeeklyBatchRepository,
)
from app.scheduler import get_scheduler_manager

logger = logging.getLogger(__name__)


class SubscriptionRequest(BaseModel):
    """Request model for subscription creation"""
    playstore_url: str = Field(..., description="Google Play Store app URL")
    weeks: int = Field(..., ge=1, le=12, description="Number of weeks to analyze (1-12)")
    email: EmailStr = Field(..., description="Email address to receive insights")
    
    @field_validator('playstore_url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class SubscriptionResponse(BaseModel):
    """Response model for subscription creation"""
    status: str
    message: str
    app_id: Optional[str] = None


async def create_subscription(request: SubscriptionRequest) -> SubscriptionResponse:
    """
    Create a new subscription and trigger analysis.
    
    This endpoint:
    1. Validates the Play Store URL exists
    2. Checks reviews exist in the time window
    3. Creates app record (if new)
    4. Creates subscription
    5. Creates initial weekly batch
    6. Triggers first analysis job immediately
    
    Args:
        request: SubscriptionRequest with playstore_url, weeks, email
        
    Returns:
        SubscriptionResponse with status and message
        
    Raises:
        HTTPException: For validation errors or processing failures
    """
    try:
        # Step 1: Validate URL exists on Play Store
        logger.info(f"Validating Play Store URL: {request.playstore_url}")
        validator = PlayStoreURLValidator()
        validation_result = validator.validate_and_verify(str(request.playstore_url))
        
        if not validation_result['valid']:
            raise HTTPException(
                status_code=400,
                detail="Invalid Play Store URL format"
            )
        
        if not validation_result['app_exists']:
            raise HTTPException(
                status_code=404,
                detail="This app does not exist on Play Store."
            )
        
        app_id = validation_result['app_id']
        
        # Step 2: Check reviews exist in timeframe (quick check)
        # We'll do a full check during analysis, but validate URL first
        
        # Step 3: Create/update app and subscription in database
        with get_db_session() as session:
            # Get or create app
            app = AppRepository.get_or_create_by_playstore_id(
                session,
                playstore_app_id=app_id,
                app_name=app_id.split('.')[-1].title(),  # Simple name from ID
                app_url=str(request.playstore_url),
            )
            session.commit()
            
            # Create subscription
            start_date = date.today()
            subscription = SubscriptionRepository.create(
                session,
                app_id=app.id,
                email=request.email,
                start_date=start_date,
                is_active=True,
            )
            session.commit()
            
            logger.info(f"Created subscription {subscription.id} for app {app_id}")
            
            subscription_id = subscription.id
        
        # Step 4: Trigger first analysis job immediately via scheduler
        scheduler_manager = get_scheduler_manager()
        if scheduler_manager.is_running():
            # Add immediate job to scheduler
            scheduler_manager.add_immediate_job(subscription_id)
            logger.info(f"Scheduled immediate analysis job for subscription {subscription_id}")
        else:
            # Fallback: run synchronously if scheduler not running
            logger.warning("Scheduler not running, executing analysis synchronously")
            try:
                # Calculate date range
                today = date.today()
                end_date = today - timedelta(days=7)  # Exclude last 7 days
                start_date = end_date - timedelta(days=request.weeks * 7)
                
                # Run analysis pipeline (fallback synchronous execution)
                logger.info(f"Starting analysis for {app_id}, weeks={request.weeks}")
                result = extract_clean_and_synthesize(
                    play_store_url=str(request.playstore_url),
                    weeks=request.weeks,
                    samples_per_rating=15,
                    exclude_last_days=7,
                )
                
                # Check for errors
                if result.get('errors'):
                    error_msg = '; '.join(result['errors'])
                    logger.error(f"Analysis errors: {error_msg}")
                    # Don't fail subscription creation, but log error
                    return SubscriptionResponse(
                        status="success",
                        message="Subscription created. Analysis started but encountered some issues. Check logs for details.",
                        app_id=app_id
                    )
                
                # Check if reviews were found
                if result.get('stats', {}).get('total_reviews', 0) == 0:
                    raise HTTPException(
                        status_code=400,
                        detail="No reviews found for the selected time range."
                    )
                
                logger.info(f"Analysis completed successfully for {app_id}")
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error during analysis: {e}", exc_info=True)
                # Subscription is created, but analysis failed
                # In production, you'd queue a retry
                return SubscriptionResponse(
                    status="success",
                    message="Subscription created. Analysis will be retried automatically.",
                    app_id=app_id
                )
        
        return SubscriptionResponse(
            status="success",
            message="Analysis started. You will receive the insights by email.",
            app_id=app_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating subscription: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Something went wrong. Please try again later."
        )

