#!/usr/bin/env python3
"""
Create Database Tables

This script creates all database tables directly using SQLAlchemy.
Use this if you prefer not to use Alembic migrations.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from app.db.database import init_db

# Load environment variables
load_dotenv()

def main():
    """Create all database tables"""
    print("=" * 70)
    print("CREATING DATABASE TABLES")
    print("=" * 70)
    print()
    
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("[ERROR] DATABASE_URL not found in environment")
        print()
        print("Please set DATABASE_URL in your .env file:")
        print("  DATABASE_URL=postgresql://username:password@ep-xxxxx.neon.tech/neondb?sslmode=require")
        print()
        sys.exit(1)
    
    print(f"Database: {database_url.split('@')[1] if '@' in database_url else 'unknown'}")
    print()
    print("Creating tables...")
    
    try:
        init_db()
        print()
        print("=" * 70)
        print("[SUCCESS] TABLES CREATED SUCCESSFULLY!")
        print("=" * 70)
        print()
        print("Created tables:")
        print("  - apps")
        print("  - subscriptions")
        print("  - weekly_batches")
        print("  - reviews")
        print("  - theme_summaries")
        print("  - weekly_pulse_notes")
        print()
        
    except Exception as e:
        print()
        print("=" * 70)
        print("[ERROR] FAILED TO CREATE TABLES!")
        print("=" * 70)
        print()
        print(f"Error: {str(e)}")
        print()
        print("Troubleshooting:")
        print("  1. Verify DATABASE_URL is correct")
        print("  2. Test connection: python scripts/test_neon_connection.py")
        print("  3. Check database permissions")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()

