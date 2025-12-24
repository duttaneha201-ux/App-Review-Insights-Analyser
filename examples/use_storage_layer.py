"""
Example: Using the Storage Layer

This script demonstrates how to:
1. Query apps from database
2. Retrieve reviews by app/week
3. Get theme summaries
4. Retrieve weekly pulse notes
5. Export data
"""

from datetime import date, timedelta
from app.db.database import get_db_session
from app.db.repository import (
    AppRepository,
    WeeklyBatchRepository,
    ReviewRepository,
    ThemeSummaryRepository,
    WeeklyPulseNoteRepository,
)
from app.db.backup import (
    export_reviews_to_json,
    export_pulse_notes_to_json,
    backup_database,
)
from pathlib import Path


def list_all_apps():
    """List all apps in the database"""
    print("\n=== All Apps ===")
    with get_db_session() as session:
        apps = AppRepository.list_all(session)
        if not apps:
            print("No apps found in database.")
            return
        
        for app in apps:
            print(f"  - {app.app_name} ({app.playstore_app_id})")
            print(f"    Created: {app.created_at}")
            print(f"    URL: {app.app_url}")


def get_reviews_for_app(app_id: str, limit: int = 10):
    """Get reviews for a specific app"""
    print(f"\n=== Reviews for {app_id} ===")
    with get_db_session() as session:
        app = AppRepository.get_by_playstore_id(session, app_id)
        if not app:
            print(f"App {app_id} not found in database.")
            return
        
        reviews = ReviewRepository.get_by_app(session, app.id, limit=limit)
        print(f"Found {len(reviews)} reviews (showing up to {limit}):")
        
        for review in reviews[:limit]:
            print(f"\n  Rating: {review.rating}⭐")
            print(f"  Date: {review.review_date}")
            print(f"  Title: {review.title or 'N/A'}")
            print(f"  Text: {review.text[:100]}..." if len(review.text) > 100 else f"  Text: {review.text}")


def get_weekly_batches_for_app(app_id: str):
    """Get weekly batches for a specific app"""
    print(f"\n=== Weekly Batches for {app_id} ===")
    with get_db_session() as session:
        app = AppRepository.get_by_playstore_id(session, app_id)
        if not app:
            print(f"App {app_id} not found in database.")
            return
        
        # Get batches through app relationship
        batches = app.weekly_batches
        if not batches:
            print("No weekly batches found.")
            return
        
        print(f"Found {len(batches)} weekly batches:")
        for batch in sorted(batches, key=lambda b: b.week_start_date, reverse=True):
            print(f"\n  Week: {batch.week_start_date} to {batch.week_end_date}")
            print(f"  Status: {batch.status}")
            print(f"  Created: {batch.created_at}")
            
            # Count reviews
            review_count = len(batch.reviews)
            print(f"  Reviews: {review_count}")
            
            # Count themes
            theme_count = len(batch.theme_summaries)
            print(f"  Themes: {theme_count}")
            
            # Check for pulse note
            if batch.weekly_pulse_note:
                print(f"  Pulse: {batch.weekly_pulse_note.title} ({batch.weekly_pulse_note.word_count} words)")


def get_themes_for_week(app_id: str, week_start: date):
    """Get theme summaries for a specific week"""
    print(f"\n=== Themes for Week {week_start} ===")
    with get_db_session() as session:
        app = AppRepository.get_by_playstore_id(session, app_id)
        if not app:
            print(f"App {app_id} not found.")
            return
        
        batch = WeeklyBatchRepository.get_by_app_and_week(session, app.id, week_start)
        if not batch:
            print(f"No batch found for week {week_start}.")
            return
        
        themes = ThemeSummaryRepository.get_by_week(session, batch.id)
        if not themes:
            print("No themes found for this week.")
            return
        
        print(f"Found {len(themes)} themes:")
        for theme in themes:
            print(f"\n  Theme: {theme.theme_name}")
            print(f"  Key Points: {len(theme.key_points)}")
            for point in theme.key_points[:3]:  # Show first 3
                print(f"    - {point}")
            print(f"  Quotes: {len(theme.candidate_quotes)}")


def get_pulse_note_for_week(app_id: str, week_start: date):
    """Get weekly pulse note for a specific week"""
    print(f"\n=== Weekly Pulse for Week {week_start} ===")
    with get_db_session() as session:
        app = AppRepository.get_by_playstore_id(session, app_id)
        if not app:
            print(f"App {app_id} not found.")
            return
        
        batch = WeeklyBatchRepository.get_by_app_and_week(session, app.id, week_start)
        if not batch:
            print(f"No batch found for week {week_start}.")
            return
        
        pulse = WeeklyPulseNoteRepository.get_by_week(session, batch.id)
        if not pulse:
            print("No pulse note found for this week.")
            return
        
        print(f"\nTitle: {pulse.title}")
        print(f"\nOverview:\n{pulse.overview}")
        print(f"\nThemes ({len(pulse.themes)}):")
        for theme in pulse.themes:
            print(f"  - {theme.get('name', 'N/A')}: {theme.get('summary', 'N/A')}")
        print(f"\nQuotes ({len(pulse.quotes)}):")
        for quote in pulse.quotes:
            print(f"  - \"{quote}\"")
        print(f"\nActions ({len(pulse.actions)}):")
        for action in pulse.actions:
            print(f"  - {action}")
        print(f"\nWord Count: {pulse.word_count}")


def export_data_example(app_id: str):
    """Example of exporting data"""
    print(f"\n=== Exporting Data for {app_id} ===")
    
    with get_db_session() as session:
        app = AppRepository.get_by_playstore_id(session, app_id)
        if not app:
            print(f"App {app_id} not found.")
            return
        
        # Create exports directory
        export_dir = Path("exports")
        export_dir.mkdir(exist_ok=True)
        
        # Export reviews to JSON
        reviews_file = export_dir / f"reviews_{app_id}.json"
        count = export_reviews_to_json(session, reviews_file, app_id=app.id)
        print(f"Exported {count} reviews to {reviews_file}")
        
        # Export pulse notes to JSON
        pulses_file = export_dir / f"pulses_{app_id}.json"
        count = export_pulse_notes_to_json(session, pulses_file, app_id=app.id)
        print(f"Exported {count} pulse notes to {pulses_file}")


def backup_example():
    """Example of backing up database"""
    print("\n=== Creating Database Backup ===")
    backup_path = backup_database()
    print(f"Backup created: {backup_path}")


if __name__ == "__main__":
    print("=" * 70)
    print("Storage Layer Usage Examples")
    print("=" * 70)
    
    # Example app ID (change to match your data)
    example_app_id = "com.whatsapp"
    
    # List all apps
    list_all_apps()
    
    # Get reviews for an app
    get_reviews_for_app(example_app_id, limit=5)
    
    # Get weekly batches
    get_weekly_batches_for_app(example_app_id)
    
    # Get themes for a recent week (if data exists)
    # Uncomment and adjust date as needed:
    # recent_week = date.today() - timedelta(days=14)
    # get_themes_for_week(example_app_id, recent_week)
    
    # Get pulse note for a week
    # Uncomment and adjust date as needed:
    # get_pulse_note_for_week(example_app_id, recent_week)
    
    # Export data
    # export_data_example(example_app_id)
    
    # Backup database
    # backup_example()
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)








