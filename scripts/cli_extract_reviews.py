"""
CLI script for extracting and cleaning Play Store reviews.

Usage:
    python scripts/cli_extract_reviews.py <play_store_url> [options]

Example:
    python scripts/cli_extract_reviews.py "https://play.google.com/store/apps/details?id=com.whatsapp" --weeks 12
"""

import sys
from pathlib import Path

# Add project root to Python path so imports work from any directory
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import argparse
import json
from datetime import date
from app.pipeline import extract_and_clean_reviews, extract_clean_and_synthesize
from app.services.weekly_synthesis import WeeklySynthesisEngine


def format_review(review, index: int) -> str:
    """Format a review for display"""
    stars = "⭐" * review.rating
    date_str = review.date.strftime("%Y-%m-%d")
    title_str = f" - {review.title}" if review.title else ""
    return f"\n{index}. {stars} ({review.rating}/5) - {date_str}{title_str}\n   {review.text[:200]}{'...' if len(review.text) > 200 else ''}"


def main():
    parser = argparse.ArgumentParser(
        description="Extract and clean Play Store reviews",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract reviews for WhatsApp (12 weeks, default)
  python cli_extract_reviews.py "https://play.google.com/store/apps/details?id=com.whatsapp"
  
  # Extract reviews for 4 weeks
  python cli_extract_reviews.py "https://play.google.com/store/apps/details?id=com.whatsapp" --weeks 4
  
  # Save to JSON file
  python cli_extract_reviews.py "https://play.google.com/store/apps/details?id=com.whatsapp" --output reviews.json
  
  # Disable cleaning (for testing)
  python cli_extract_reviews.py "https://play.google.com/store/apps/details?id=com.whatsapp" --no-cleaning
        """
    )
    
    parser.add_argument(
        'url',
        help='Play Store URL (e.g., https://play.google.com/store/apps/details?id=com.whatsapp)'
    )
    
    parser.add_argument(
        '--weeks',
        type=int,
        default=12,
        choices=range(1, 13),
        metavar='N',
        help='Number of weeks to look back (1-12, default: 12)'
    )
    
    parser.add_argument(
        '--samples',
        type=int,
        default=15,
        metavar='N',
        help='Number of reviews to sample per rating (default: 15)'
    )
    
    parser.add_argument(
        '--exclude-days',
        type=int,
        default=7,
        metavar='N',
        help='Exclude reviews from last N days (default: 7)'
    )
    
    parser.add_argument(
        '--output',
        '-o',
        type=str,
        help='Output JSON file path (optional)'
    )
    
    parser.add_argument(
        '--no-cleaning',
        action='store_true',
        help='Disable text cleaning and PII scrubbing (for testing)'
    )
    
    parser.add_argument(
        '--duplicate-threshold',
        type=int,
        default=90,
        choices=range(0, 101),
        metavar='0-100',
        help='Fuzzy duplicate threshold (default: 90)'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        default=True,
        help='Run browser in headless mode (default: True)'
    )
    
    parser.add_argument(
        '--no-headless',
        dest='headless',
        action='store_false',
        help='Show browser window (for debugging)'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON only (no human-readable output)'
    )
    
    parser.add_argument(
        '--synthesize',
        action='store_true',
        default=True,
        help='Generate weekly pulse synthesis (default: True)'
    )
    
    parser.add_argument(
        '--no-synthesize',
        dest='synthesize',
        action='store_false',
        help='Skip weekly pulse synthesis (faster, for testing)'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("Play Store Reviews Extractor & Cleaner")
    print("=" * 70)
    print(f"\nURL: {args.url}")
    print(f"Weeks: {args.weeks}")
    print(f"Samples per rating: {args.samples}")
    print(f"Exclude last {args.exclude_days} days")
    print(f"Cleaning: {'Disabled' if args.no_cleaning else 'Enabled'}")
    print(f"Duplicate threshold: {args.duplicate_threshold}")
    print(f"Synthesis: {'Enabled' if args.synthesize else 'Disabled'}")
    print("\nExtracting reviews... (this may take a few minutes)\n")
    
    # Extract, clean, and synthesize
    if args.synthesize:
        result = extract_clean_and_synthesize(
            play_store_url=args.url,
            weeks=args.weeks,
            samples_per_rating=args.samples,
            exclude_last_days=args.exclude_days,
            enable_cleaning=not args.no_cleaning,
            duplicate_threshold=args.duplicate_threshold,
            headless=args.headless
        )
    else:
        result = extract_and_clean_reviews(
            play_store_url=args.url,
            weeks=args.weeks,
            samples_per_rating=args.samples,
            exclude_last_days=args.exclude_days,
            enable_cleaning=not args.no_cleaning,
            duplicate_threshold=args.duplicate_threshold,
            headless=args.headless
        )
        # Add empty synthesis fields for compatibility
        result['themes'] = []
        result['weekly_pulse'] = None
    
    # Handle errors
    if result['errors']:
        print("\n" + "=" * 70)
        print("ERRORS:")
        print("=" * 70)
        for error in result['errors']:
            print(f"  ❌ {error}")
        print()
        sys.exit(1)
    
    if not result['app_exists']:
        print(f"\n❌ App not found: {result.get('app_id', 'Unknown')}")
        sys.exit(1)
    
    reviews = result['reviews']
    stats = result['stats']
    start_date, end_date = result['date_range']
    
    # Output results
    if args.json:
        # JSON output only
        output_data = {
            'app_id': result['app_id'],
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'stats': stats,
            'reviews': [r.to_dict() for r in reviews]
        }
        print(json.dumps(output_data, indent=2, ensure_ascii=False))
    else:
        # Human-readable output
        print("=" * 70)
        print("EXTRACTION RESULTS")
        print("=" * 70)
        print(f"\nApp ID: {result['app_id']}")
        print(f"Date Range: {start_date} to {end_date}")
        print(f"Total Reviews: {len(reviews)}")
        
        print("\nReviews by Rating:")
        for rating in range(5, 0, -1):
            count = stats.get('by_rating', {}).get(rating, 0) or stats.get('final_count', 0) // 5
            stars = "⭐" * rating
            print(f"  {stars} ({rating} stars): {count} reviews")
        
        # Show themes if available
        if result.get('themes'):
            print("\n" + "=" * 70)
            print(f"IDENTIFIED THEMES ({len(result['themes'])} themes)")
            print("=" * 70)
            for i, theme in enumerate(result['themes'][:5], 1):
                print(f"\n{i}. {theme.theme}")
                print(f"   Frequency: {theme.frequency} week(s)")
                if theme.key_points:
                    print(f"   Key Points: {', '.join(theme.key_points[:2])}")
        
        # Show weekly pulse if available
        if result.get('weekly_pulse'):
            pulse = result['weekly_pulse']
            print("\n" + "=" * 70)
            print("WEEKLY PRODUCT PULSE")
            print("=" * 70)
            print(f"\nTitle: {pulse.title}")
            print(f"\nOverview:\n{pulse.overview}")
            
            if pulse.themes:
                print(f"\nTop Themes ({len(pulse.themes)}):")
                for theme in pulse.themes:
                    print(f"  • {theme.get('name', 'Unknown')}: {theme.get('summary', '')}")
            
            if pulse.quotes:
                print(f"\nRepresentative Quotes ({len(pulse.quotes)}):")
                for i, quote in enumerate(pulse.quotes, 1):
                    print(f"  {i}. \"{quote}\"")
            
            if pulse.actions:
                print(f"\nRecommended Actions ({len(pulse.actions)}):")
                for i, action in enumerate(pulse.actions, 1):
                    print(f"  {i}. {action}")
            
            print(f"\nWord Count: {pulse.word_count()} / {WeeklySynthesisEngine.MAX_WORDS}")
        
        if reviews and not result.get('weekly_pulse'):
            print("\n" + "=" * 70)
            print("SAMPLE REVIEWS (first 5)")
            print("=" * 70)
            for i, review in enumerate(reviews[:5], 1):
                print(format_review(review, i))
        
        print("\n" + "=" * 70)
        print("✅ Analysis completed successfully!")
        print("=" * 70)
    
    # Save to file if requested
    if args.output:
        output_data = {
            'app_id': result['app_id'],
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'stats': stats,
            'reviews': [r.to_dict() for r in reviews]
        }
        
        # Add themes and pulse if available
        if result.get('themes'):
            output_data['themes'] = [t.to_dict() for t in result['themes']]
        
        if result.get('weekly_pulse'):
            output_data['weekly_pulse'] = result['weekly_pulse'].to_dict()
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {args.output}")


if __name__ == '__main__':
    main()

