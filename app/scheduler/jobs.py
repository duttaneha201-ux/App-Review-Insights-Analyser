"""
Scheduled job definitions for App Review Insights Analyzer

Jobs:
1. Immediate analysis job (triggered on subscription creation)
2. Weekly recurring job (every Monday 8 AM IST)
"""

import logging
import traceback
from datetime import date, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.pipeline import extract_clean_and_synthesize
from app.db.database import get_db_session
from app.db.models import Subscription
from app.db.repository import (
    AppRepository,
    SubscriptionRepository,
    WeeklyBatchRepository,
    WeeklyPulseNoteRepository,
)
from app.services.email_service import EmailService
from app.scheduler.timezone_utils import (
    get_week_start_date,
    get_week_end_date,
    get_ist_now,
)

logger = logging.getLogger(__name__)


def _log_job_start(job_type: str, **kwargs):
    """Log job start with context"""
    logger.info(
        f"[JOB_START] {job_type}",
        extra={
            'job_type': job_type,
            **kwargs
        }
    )


def _log_job_success(job_type: str, execution_time: float, **kwargs):
    """Log job success with context"""
    logger.info(
        f"[JOB_SUCCESS] {job_type} completed in {execution_time:.2f}s",
        extra={
            'job_type': job_type,
            'execution_time': execution_time,
            'status': 'success',
            **kwargs
        }
    )


def _log_job_failure(job_type: str, error: Exception, execution_time: float, **kwargs):
    """Log job failure with context"""
    error_msg = str(error)
    error_traceback = traceback.format_exc()
    
    logger.error(
        f"[JOB_FAILURE] {job_type} failed: {error_msg}",
        extra={
            'job_type': job_type,
            'error': error_msg,
            'traceback': error_traceback,
            'execution_time': execution_time,
            'status': 'failed',
            **kwargs
        },
        exc_info=True
    )


def _process_weekly_batch(
    subscription_id: int,
    app_id: int,
    week_start: date,
    week_end: date,
    app_url: str,
    email: str,
    weeks: int = 12
) -> Dict[str, Any]:
    """
    Process a weekly batch: extract, analyze, synthesize, and send email.
    
    Args:
        subscription_id: Subscription ID
        app_id: App ID
        week_start: Week start date (Monday)
        week_end: Week end date (Sunday)
        app_url: Play Store URL
        email: Recipient email
        weeks: Number of weeks to analyze
        
    Returns:
        dict with 'success', 'error', 'stats'
    """
    import time
    start_time = time.time()
    
    try:
        # Check if batch already exists and is processed
        with get_db_session() as session:
            existing_batch = WeeklyBatchRepository.get_by_app_and_week(
                session,
                app_id=app_id,
                week_start_date=week_start,
            )
            
            if existing_batch and existing_batch.status == 'processed':
                # Check if pulse note exists
                pulse_note = WeeklyPulseNoteRepository.get_by_week(
                    session,
                    existing_batch.id
                )
                
                if pulse_note:
                    logger.info(
                        f"Batch {existing_batch.id} already processed, skipping",
                        extra={
                            'subscription_id': subscription_id,
                            'app_id': app_id,
                            'week_start': str(week_start),
                            'week_end': str(week_end),
                        }
                    )
                    return {
                        'success': True,
                        'skipped': True,
                        'message': 'Batch already processed',
                        'batch_id': existing_batch.id,
                    }
        
        # Run analysis pipeline
        logger.info(
            f"Running analysis pipeline for app_id={app_id}, week={week_start} to {week_end}",
            extra={
                'subscription_id': subscription_id,
                'app_id': app_id,
                'week_start': str(week_start),
                'week_end': str(week_end),
            }
        )
        
        # Calculate date range for extraction
        # We want reviews from week_start to week_end
        days_diff = (week_end - week_start).days + 1
        
        result = extract_clean_and_synthesize(
            play_store_url=app_url,
            weeks=max(1, days_diff // 7),  # At least 1 week
            samples_per_rating=15,
            exclude_last_days=0,  # Don't exclude, we're processing specific week
        )
        
        execution_time = time.time() - start_time
        
        # Check for errors
        if result.get('errors'):
            error_msg = '; '.join(result['errors'])
            raise Exception(f"Pipeline errors: {error_msg}")
        
        # Check if reviews were found
        if result.get('stats', {}).get('total_reviews', 0) == 0:
            logger.warning(
                f"No reviews found for week {week_start} to {week_end}",
                extra={
                    'subscription_id': subscription_id,
                    'app_id': app_id,
                    'week_start': str(week_start),
                    'week_end': str(week_end),
                }
            )
            return {
                'success': True,
                'skipped': True,
                'message': 'No reviews found',
                'stats': result.get('stats', {}),
            }
        
        # Get the weekly pulse
        weekly_pulse = result.get('weekly_pulse')
        if not weekly_pulse:
            logger.warning(
                f"No weekly pulse generated for week {week_start}",
                extra={
                    'subscription_id': subscription_id,
                    'app_id': app_id,
                    'week_start': str(week_start),
                }
            )
            return {
                'success': True,
                'skipped': True,
                'message': 'No pulse generated',
                'stats': result.get('stats', {}),
            }
        
        # Send email
        try:
            email_service = EmailService()
            email_service.send_weekly_pulse(
                recipient_email=email,
                pulse=weekly_pulse,
                app_name=result.get('app_id', 'App'),
                audience='product_manager'
            )
            logger.info(f"Email sent successfully to {email}")
        except Exception as e:
            logger.error(f"Failed to send email to {email}: {e}", exc_info=True)
            # Don't fail the whole job if email fails
            # In production, you might want to queue a retry
        
        return {
            'success': True,
            'stats': result.get('stats', {}),
            'execution_time': execution_time,
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        _log_job_failure(
            'process_weekly_batch',
            e,
            execution_time,
            subscription_id=subscription_id,
            app_id=app_id,
            week_start=str(week_start),
            week_end=str(week_end),
        )
        raise


def trigger_immediate_analysis(subscription_id: int) -> Dict[str, Any]:
    """
    Immediate analysis job triggered when a subscription is created.
    
    This job:
    1. Gets subscription details
    2. Determines the week to process (current week or last complete week)
    3. Processes the batch
    4. Sends email
    
    Args:
        subscription_id: Subscription ID
        
    Returns:
        dict with 'success', 'error', 'stats'
    """
    _log_job_start('immediate_analysis', subscription_id=subscription_id)
    
    try:
        with get_db_session() as session:
            # Get subscription
            subscription = session.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                raise ValueError(f"Subscription {subscription_id} not found")
            
            if not subscription.is_active:
                logger.info(f"Subscription {subscription_id} is not active, skipping")
                return {
                    'success': True,
                    'skipped': True,
                    'message': 'Subscription not active',
                }
            
            # Get app
            app = AppRepository.get_by_id(session, subscription.app_id)
            if not app:
                raise ValueError(f"App {subscription.app_id} not found")
            
            # Determine week to process
            # Process the last complete week (not current week)
            today_ist = get_ist_now().date()
            last_week_end = today_ist - timedelta(days=today_ist.weekday() + 1)  # Last Sunday
            last_week_start = last_week_end - timedelta(days=6)  # Last Monday
            
            # Process the batch
            result = _process_weekly_batch(
                subscription_id=subscription.id,
                app_id=app.id,
                week_start=last_week_start,
                week_end=last_week_end,
                app_url=app.app_url,
                email=subscription.email,
                weeks=12,  # Default, subscription doesn't store this yet
            )
            
            _log_job_success(
                'immediate_analysis',
                result.get('execution_time', 0),
                subscription_id=subscription_id,
                app_id=app.id,
            )
            
            return result
            
    except Exception as e:
        _log_job_failure('immediate_analysis', e, 0, subscription_id=subscription_id)
        return {
            'success': False,
            'error': str(e),
        }


def run_weekly_job() -> Dict[str, Any]:
    """
    Weekly recurring job that runs every Monday at 8 AM IST.
    
    This job:
    1. Gets all active subscriptions
    2. For each subscription, processes the last complete week
    3. Skips if already processed (idempotency)
    4. Sends emails
    
    Returns:
        dict with 'success', 'processed_count', 'errors'
    """
    import time
    start_time = time.time()
    
    _log_job_start('weekly_recurring')
    
    processed_count = 0
    errors = []
    
    try:
        with get_db_session() as session:
            # Get all active subscriptions
            subscriptions = SubscriptionRepository.get_active_subscriptions(session)
            
            logger.info(f"Found {len(subscriptions)} active subscriptions")
            
            # Determine week to process (last complete week)
            today_ist = get_ist_now().date()
            last_week_end = today_ist - timedelta(days=today_ist.weekday() + 1)  # Last Sunday
            last_week_start = last_week_end - timedelta(days=6)  # Last Monday
            
            logger.info(
                f"Processing week {last_week_start} to {last_week_end}",
                extra={
                    'week_start': str(last_week_start),
                    'week_end': str(last_week_end),
                }
            )
            
            # Process each subscription
            for subscription in subscriptions:
                try:
                    app = AppRepository.get_by_id(session, subscription.app_id)
                    if not app:
                        logger.warning(f"App {subscription.app_id} not found for subscription {subscription.id}")
                        continue
                    
                    result = _process_weekly_batch(
                        subscription_id=subscription.id,
                        app_id=app.id,
                        week_start=last_week_start,
                        week_end=last_week_end,
                        app_url=app.app_url,
                        email=subscription.email,
                        weeks=12,  # Default
                    )
                    
                    if result.get('success') and not result.get('skipped'):
                        processed_count += 1
                    elif result.get('error'):
                        errors.append({
                            'subscription_id': subscription.id,
                            'error': result['error'],
                        })
                        
                except Exception as e:
                    error_msg = str(e)
                    errors.append({
                        'subscription_id': subscription.id,
                        'error': error_msg,
                    })
                    logger.error(
                        f"Error processing subscription {subscription.id}: {error_msg}",
                        exc_info=True
                    )
        
        execution_time = time.time() - start_time
        
        _log_job_success(
            'weekly_recurring',
            execution_time,
            processed_count=processed_count,
            error_count=len(errors),
        )
        
        return {
            'success': True,
            'processed_count': processed_count,
            'error_count': len(errors),
            'errors': errors,
            'execution_time': execution_time,
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        _log_job_failure('weekly_recurring', e, execution_time)
        return {
            'success': False,
            'error': str(e),
            'processed_count': processed_count,
            'error_count': len(errors),
            'errors': errors,
        }

