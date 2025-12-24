"""
End-to-end pipeline for extracting, cleaning, and processing reviews.

This module provides a complete workflow:
1. Extract reviews from Play Store
2. Clean text (HTML, emojis, links)
3. Scrub PII (emails, phones, usernames, etc.)
4. Deduplicate (fuzzy matching)
5. Filter and sample
"""

import logging
import os
from datetime import date, timedelta
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

from app.models.review import Review
from app.services.url_validator import PlayStoreURLValidator
from app.services.review_extractor import ReviewExtractor
from app.services.cleaning_service import CleaningService
from app.services.theme_chunker import ThemeChunker
from app.services.weekly_synthesis import WeeklySynthesisEngine, WeeklyPulse
from app.db.database import get_db_session
from app.db.repository import (
    AppRepository,
    WeeklyBatchRepository,
    ReviewRepository,
    ThemeSummaryRepository,
    WeeklyPulseNoteRepository,
)

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


def extract_and_clean_reviews(
    play_store_url: str,
    weeks: int = 12,
    samples_per_rating: int = 15,
    exclude_last_days: int = 7,
    enable_cleaning: bool = True,
    duplicate_threshold: int = 90,
    headless: bool = True
) -> Dict[str, Any]:
    """
    Complete pipeline: Extract, clean, and process reviews from Play Store.
    
    Args:
        play_store_url: Full Play Store URL (e.g., "https://play.google.com/store/apps/details?id=com.whatsapp")
        weeks: Number of weeks to look back (1-12, default: 12)
        samples_per_rating: Number of reviews to sample per rating (default: 15)
        exclude_last_days: Exclude reviews from last N days (default: 7)
        enable_cleaning: Enable text cleaning and PII scrubbing (default: True)
        duplicate_threshold: Fuzzy duplicate threshold 0-100 (default: 90)
        headless: Run browser in headless mode (default: True)
        
    Returns:
        Dictionary with:
        - 'reviews': List of cleaned Review objects
        - 'app_id': Extracted app ID
        - 'app_exists': Whether app exists
        - 'date_range': Tuple of (start_date, end_date)
        - 'stats': Dictionary with extraction statistics
        - 'errors': List of error messages (if any)
    """
    errors = []
    stats = {
        'total_extracted': 0,
        'after_cleaning': 0,
        'after_deduplication': 0,
        'after_date_filter': 0,
        'after_length_filter': 0,
        'final_count': 0,
        'pii_scrubbed': 0,
        'by_rating': {}
    }
    
    # Step 1: Validate URL and extract app ID
    logger.info(f"Validating Play Store URL: {play_store_url}")
    validator = PlayStoreURLValidator()
    validation_result = validator.validate_and_verify(play_store_url)
    
    if not validation_result['valid']:
        errors.append(f"Invalid URL: {validation_result.get('error', 'Unknown error')}")
        return {
            'reviews': [],
            'app_id': None,
            'app_exists': False,
            'date_range': None,
            'stats': stats,
            'errors': errors
        }
    
    app_id = validation_result['app_id']
    
    if not validation_result['app_exists']:
        errors.append(f"App not found: {validation_result.get('error', 'App does not exist')}")
        return {
            'reviews': [],
            'app_id': app_id,
            'app_exists': False,
            'date_range': None,
            'stats': stats,
            'errors': errors
        }
    
    # Step 2: Calculate date range
    today = date.today()
    end_date = today - timedelta(days=exclude_last_days)
    start_date = end_date - timedelta(days=weeks * 7)
    
    logger.info(f"Extracting reviews for {app_id} from {start_date} to {end_date}")
    
    # Step 3: Extract reviews
    try:
        extractor = ReviewExtractor(
            headless=headless,
            enable_cleaning=enable_cleaning,
            duplicate_threshold=duplicate_threshold
        )
        
        reviews = extractor.extract_reviews(
            app_id=app_id,
            start_date=start_date,
            end_date=end_date,
            samples_per_rating=samples_per_rating
        )
        
        stats['final_count'] = len(reviews)
        
        # Count by rating
        for rating in range(1, 6):
            count = sum(1 for r in reviews if r.rating == rating)
            stats['by_rating'][rating] = count
        
        logger.info(f"Successfully extracted and processed {len(reviews)} reviews")
        
        return {
            'reviews': reviews,
            'app_id': app_id,
            'app_exists': True,
            'date_range': (start_date, end_date),
            'stats': stats,
            'errors': errors
        }
        
    except Exception as e:
        logger.error(f"Error extracting reviews: {e}", exc_info=True)
        errors.append(f"Extraction failed: {str(e)}")
        return {
            'reviews': [],
            'app_id': app_id,
            'app_exists': True,
            'date_range': (start_date, end_date),
            'stats': stats,
            'errors': errors
        }


def extract_clean_and_synthesize(
    play_store_url: str,
    weeks: int = 12,
    samples_per_rating: int = 15,
    exclude_last_days: int = 7,
    enable_cleaning: bool = True,
    duplicate_threshold: int = 90,
    headless: bool = True,
    groq_api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Complete pipeline: Extract → Clean → Theme → Synthesize
    
    This is the main function that runs the complete analysis pipeline:
    1. Extract reviews from Play Store
    2. Clean and scrub PII
    3. Identify themes
    4. Generate Weekly Product Pulse
    
    Args:
        play_store_url: Full Play Store URL
        weeks: Number of weeks to look back (1-12, default: 12)
        samples_per_rating: Number of reviews per rating (default: 15)
        exclude_last_days: Exclude reviews from last N days (default: 7)
        enable_cleaning: Enable text cleaning and PII scrubbing (default: True)
        duplicate_threshold: Fuzzy duplicate threshold 0-100 (default: 90)
        headless: Run browser in headless mode (default: True)
        groq_api_key: Optional Groq API key (uses env var if not provided)
        
    Returns:
        Dictionary with:
        - 'reviews': List of cleaned Review objects
        - 'themes': List of AggregatedTheme objects
        - 'weekly_pulse': WeeklyPulse object
        - 'app_id': Extracted app ID
        - 'app_exists': Whether app exists
        - 'date_range': Tuple of (start_date, end_date)
        - 'stats': Dictionary with statistics
        - 'errors': List of error messages (if any)
    """
    errors = []
    stats = {
        'total_reviews': 0,
        'themes_identified': 0,
        'pulse_generated': False,
        'pulse_word_count': 0
    }
    
    # Step 1: Extract and clean reviews
    extraction_result = extract_and_clean_reviews(
        play_store_url=play_store_url,
        weeks=weeks,
        samples_per_rating=samples_per_rating,
        exclude_last_days=exclude_last_days,
        enable_cleaning=enable_cleaning,
        duplicate_threshold=duplicate_threshold,
        headless=headless
    )
    
    if extraction_result['errors']:
        return {
            'reviews': [],
            'themes': [],
            'weekly_pulse': None,
            'app_id': extraction_result.get('app_id'),
            'app_exists': extraction_result.get('app_exists', False),
            'date_range': extraction_result.get('date_range'),
            'stats': stats,
            'errors': extraction_result['errors']
        }
    
    reviews = extraction_result['reviews']
    stats['total_reviews'] = len(reviews)
    
    if not reviews:
        errors.append("No reviews extracted")
        return {
            'reviews': [],
            'themes': [],
            'weekly_pulse': None,
            'app_id': extraction_result['app_id'],
            'app_exists': True,
            'date_range': extraction_result['date_range'],
            'stats': stats,
            'errors': errors
        }
    
    # Step 2: Identify themes
    try:
        start_date, end_date = extraction_result['date_range']
        chunker = ThemeChunker(api_key=groq_api_key)
        themes = chunker.process_reviews(reviews, start_date, end_date)
        stats['themes_identified'] = len(themes)
        
    except Exception as e:
        logger.error(f"Error identifying themes: {e}", exc_info=True)
        errors.append(f"Theme identification failed: {str(e)}")
        themes = []
    
    # Step 3: Synthesize weekly pulse
    weekly_pulse = None
    if themes:
        try:
            # Get app name from validation result (extracted from Play Store)
            app_name = extraction_result.get('app_name')
            if not app_name and extraction_result['app_id']:
                # Fallback: try to get from database
                with get_db_session() as session:
                    app = AppRepository.get_by_playstore_id(session, extraction_result['app_id'])
                    if app:
                        app_name = app.app_name
                    else:
                        # Last resort: use formatted app_id
                        app_name = extraction_result['app_id'].split('.')[-1].title()
            
            synthesizer = WeeklySynthesisEngine(api_key=groq_api_key)
            weekly_pulse = synthesizer.synthesize_weekly_pulse(themes, app_name)
            stats['pulse_generated'] = True
            stats['pulse_word_count'] = weekly_pulse.word_count()
            
        except Exception as e:
            logger.error(f"Error synthesizing weekly pulse: {e}", exc_info=True)
            errors.append(f"Weekly synthesis failed: {str(e)}")
    
    # Step 4: Save to database
    try:
        start_date, end_date = extraction_result['date_range']
        app_id_str = extraction_result['app_id']
        
        with get_db_session() as session:
            # Get app name from validation result (extracted from Play Store)
            extracted_app_name = extraction_result.get('app_name')
            
            # Get or create app
            app = AppRepository.get_or_create_by_playstore_id(
                session,
                playstore_app_id=app_id_str,
                app_name=extracted_app_name or app_name or app_id_str,
                app_url=play_store_url,
            )
            session.commit()
            
            # Update app_name variable with the actual stored name
            app_name = app.app_name
            
            # Get or create weekly batch
            batch = WeeklyBatchRepository.get_or_create(
                session,
                app_id=app.id,
                week_start_date=start_date,
                week_end_date=end_date,
            )
            session.commit()
            
            # Save reviews
            if reviews:
                inserted_count = ReviewRepository.bulk_insert_with_deduplication(
                    session,
                    app_id=app.id,
                    weekly_batch_id=batch.id,
                    reviews=reviews,
                )
                session.commit()
                logger.info(f"Saved {inserted_count} reviews to database")
            
            # Save theme summaries
            if themes:
                theme_data = [
                    {
                        "theme_name": theme.theme,
                        "key_points": theme.key_points,
                        "candidate_quotes": theme.candidate_quotes,
                    }
                    for theme in themes
                ]
                ThemeSummaryRepository.bulk_insert(
                    session,
                    weekly_batch_id=batch.id,
                    themes=theme_data,
                )
                session.commit()
                logger.info(f"Saved {len(themes)} theme summaries to database")
            
            # Save weekly pulse note
            if weekly_pulse:
                WeeklyPulseNoteRepository.create_or_update(
                    session,
                    weekly_batch_id=batch.id,
                    title=weekly_pulse.title,
                    overview=weekly_pulse.overview,
                    themes=weekly_pulse.themes,
                    quotes=weekly_pulse.quotes,
                    actions=weekly_pulse.actions,
                    word_count=weekly_pulse.word_count(),
                )
                session.commit()
                logger.info("Saved weekly pulse note to database")
            
            # Update batch status
            WeeklyBatchRepository.update_status(session, batch.id, "processed")
            session.commit()
            
    except Exception as e:
        logger.error(f"Error saving to database: {e}", exc_info=True)
        errors.append(f"Database save failed: {str(e)}")
        # Don't fail the whole pipeline if DB save fails
    
    # Get final app name from database
    final_app_name = None
    if extraction_result['app_id']:
        try:
            with get_db_session() as session:
                app = AppRepository.get_by_playstore_id(session, extraction_result['app_id'])
                if app:
                    final_app_name = app.app_name
        except Exception:
            pass  # Don't fail if we can't get app name
    
    return {
        'reviews': reviews,
        'themes': themes,
        'weekly_pulse': weekly_pulse,
        'app_id': extraction_result['app_id'],
        'app_name': final_app_name or extraction_result.get('app_name'),
        'app_exists': True,
        'date_range': extraction_result['date_range'],
        'stats': stats,
        'errors': errors
    }


def process_reviews_for_analysis(reviews: List[Review]) -> List[Review]:
    """
    Additional processing step for reviews before analysis.
    Ensures all reviews are cleaned and PII-free.
    
    Args:
        reviews: List of Review objects
        
    Returns:
        List of fully cleaned Review objects
    """
    cleaning_service = CleaningService()
    processed = []
    
    for review in reviews:
        # Double-check cleaning (in case reviews came from elsewhere)
        cleaned_text, had_pii = cleaning_service.clean_and_scrub(review.text)
        
        if len(cleaned_text.strip()) < 15:
            continue
        
        processed_review = Review(
            rating=review.rating,
            title=review.title,
            text=cleaned_text,
            date=review.date,
            review_id=review.review_id,
            author=None  # Never store author
        )
        processed.append(processed_review)
    
    return processed

