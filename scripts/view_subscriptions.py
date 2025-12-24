"""
View Database: Subscriptions and Insights Requests

This script displays:
- All subscriptions (who requested what)
- Apps and their subscription counts
- Weekly batches and their status
- Generated insights (weekly pulse notes)

Usage:
    python scripts/view_subscriptions.py           # View by app
    python scripts/view_subscriptions.py --by-email # View by email
"""

import sys
from pathlib import Path

# Add project root to Python path so imports work from any directory
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.database import get_db_session
from app.db.repository import AppRepository
from app.db.models import Subscription, WeeklyBatch, WeeklyPulseNote


def view_subscriptions():
    """Display all subscriptions and who requested what"""
    print("=" * 80)
    print("SUBSCRIPTIONS & INSIGHTS REQUESTS")
    print("=" * 80)
    print()
    
    with get_db_session() as session:
        # Get all apps
        apps = AppRepository.list_all(session)
        
        if not apps:
            print("No apps found in database.")
            return
        
        print(f"Total Apps: {len(apps)}")
        print()
        
        # Display each app with its subscriptions
        for app in apps:
            print("-" * 80)
            print(f"[APP] {app.app_name}")
            print(f"   Play Store ID: {app.playstore_app_id}")
            print(f"   URL: {app.app_url}")
            print(f"   Created: {app.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            
            # Get subscriptions for this app
            subscriptions = session.query(Subscription).filter(
                Subscription.app_id == app.id
            ).order_by(Subscription.created_at.desc()).all()
            
            if subscriptions:
                print(f"   [SUBSCRIPTIONS] ({len(subscriptions)}):")
                for sub in subscriptions:
                    status = "[ACTIVE]" if sub.is_active else "[INACTIVE]"
                    print(f"      - {sub.email} {status}")
                    print(f"        Started: {sub.start_date}")
                    if sub.end_date:
                        print(f"        Ends: {sub.end_date}")
                    print(f"        Created: {sub.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    print()
            else:
                print("   [SUBSCRIPTIONS] No subscriptions")
                print()
            
            # Get weekly batches for this app
            batches = session.query(WeeklyBatch).filter(
                WeeklyBatch.app_id == app.id
            ).order_by(WeeklyBatch.week_start_date.desc()).all()
            
            if batches:
                print(f"   [WEEKLY BATCHES] ({len(batches)}):")
                for batch in batches[:5]:  # Show last 5
                    status_icon = {
                        'pending': '[PENDING]',
                        'processed': '[PROCESSED]',
                        'failed': '[FAILED]'
                    }.get(batch.status, '[UNKNOWN]')
                    
                    print(f"      {status_icon} Week: {batch.week_start_date} to {batch.week_end_date}")
                    print(f"        Status: {batch.status}")
                    print(f"        Updated: {batch.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # Check if pulse note exists
                    pulse = session.query(WeeklyPulseNote).filter(
                        WeeklyPulseNote.weekly_batch_id == batch.id
                    ).first()
                    
                    if pulse:
                        print(f"        [INSIGHT] '{pulse.title}'")
                        print(f"           Word Count: {pulse.word_count}")
                        print(f"           Themes: {len(pulse.themes)}")
                        print(f"           Quotes: {len(pulse.quotes)}")
                        print(f"           Actions: {len(pulse.actions)}")
                        print(f"           Created: {pulse.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    print()
                
                if len(batches) > 5:
                    print(f"      ... and {len(batches) - 5} more batches")
                    print()
            else:
                print("   [WEEKLY BATCHES] No weekly batches")
                print()
        
        # Summary statistics
        print("=" * 80)
        print("SUMMARY STATISTICS")
        print("=" * 80)
        
        total_subscriptions = session.query(Subscription).count()
        active_subscriptions = session.query(Subscription).filter(
            Subscription.is_active == True
        ).count()
        total_batches = session.query(WeeklyBatch).count()
        processed_batches = session.query(WeeklyBatch).filter(
            WeeklyBatch.status == 'processed'
        ).count()
        total_insights = session.query(WeeklyPulseNote).count()
        
        print(f"Total Subscriptions: {total_subscriptions}")
        print(f"Active Subscriptions: {active_subscriptions}")
        print(f"Total Weekly Batches: {total_batches}")
        print(f"Processed Batches: {processed_batches}")
        print(f"Generated Insights: {total_insights}")
        print()


def view_by_email():
    """View subscriptions grouped by email"""
    print("=" * 80)
    print("SUBSCRIPTIONS BY EMAIL")
    print("=" * 80)
    print()
    
    with get_db_session() as session:
        # Get all subscriptions with app info
        subscriptions = session.query(Subscription).order_by(
            Subscription.email, Subscription.created_at.desc()
        ).all()
        
        if not subscriptions:
            print("No subscriptions found.")
            return
        
        # Group by email
        email_groups = {}
        for sub in subscriptions:
            if sub.email not in email_groups:
                email_groups[sub.email] = []
            email_groups[sub.email].append(sub)
        
        for email, subs in email_groups.items():
            print(f"[EMAIL] {email}")
            print(f"   Total Subscriptions: {len(subs)}")
            active_count = sum(1 for s in subs if s.is_active)
            print(f"   Active: {active_count}")
            print()
            
            for sub in subs:
                app = AppRepository.get_by_id(session, sub.app_id)
                status = "[ACTIVE]" if sub.is_active else "[INACTIVE]"
                print(f"   - {app.app_name if app else 'Unknown App'} ({app.playstore_app_id if app else 'N/A'}) {status}")
                print(f"     Started: {sub.start_date}")
                print()
            
            print("-" * 80)
            print()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--by-email":
        view_by_email()
    else:
        view_subscriptions()

