#!/usr/bin/env python3
"""
Test Neon PostgreSQL Database Connection

This script tests the connection to Neon database and verifies
that the connection string is correctly configured.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

# Load environment variables
load_dotenv()

def test_connection():
    """Test database connection"""
    print("=" * 70)
    print("NEON DATABASE CONNECTION TEST")
    print("=" * 70)
    print()
    
    # Get DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("[ERROR] DATABASE_URL not found in environment")
        print()
        print("Please set DATABASE_URL in your .env file:")
        print("  DATABASE_URL=postgresql://username:password@ep-xxxxx.neon.tech/neondb?sslmode=require")
        print()
        return False
    
    # Check if it's a Neon connection string
    if "neon.tech" not in database_url and "neon" not in database_url.lower():
        print("[WARNING] Connection string doesn't appear to be from Neon")
        print(f"   Found: {database_url.split('@')[1] if '@' in database_url else 'unknown'}")
        print()
    
    # Mask password in output
    if "@" in database_url:
        parts = database_url.split("@")
        if ":" in parts[0]:
            user_pass = parts[0].split(":")
            masked_url = f"{user_pass[0]}:****@{parts[1]}"
        else:
            masked_url = database_url
    else:
        masked_url = database_url
    
    print(f"Connection String: {masked_url}")
    print()
    
    # Test connection
    print("Testing connection...")
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Test 1: Check PostgreSQL version
            print("  [OK] Checking PostgreSQL version...")
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"    PostgreSQL: {version.split(',')[0]}")
            
            # Test 2: Check current database
            print("  [OK] Checking current database...")
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.fetchone()[0]
            print(f"    Database: {db_name}")
            
            # Test 3: Check if tables exist
            print("  [OK] Checking for tables...")
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            if tables:
                print(f"    Found {len(tables)} table(s):")
                for table in sorted(tables):
                    print(f"      - {table}")
            else:
                print("    No tables found (run 'alembic upgrade head' to create them)")
            
            # Test 4: Check SSL
            print("  [OK] Checking SSL connection...")
            result = conn.execute(text("SHOW ssl"))
            ssl_status = result.fetchone()[0]
            print(f"    SSL: {ssl_status}")
        
        print()
        print("=" * 70)
        print("[SUCCESS] CONNECTION SUCCESSFUL!")
        print("=" * 70)
        print()
        print("Next steps:")
        if not tables:
            print("  1. Run: alembic upgrade head")
            print("  2. Verify tables were created")
        print("  3. Test your application")
        print()
        return True
        
    except Exception as e:
        print()
        print("=" * 70)
        print("[ERROR] CONNECTION FAILED!")
        print("=" * 70)
        print()
        print(f"Error: {str(e)}")
        print()
        print("Troubleshooting:")
        print("  1. Verify DATABASE_URL in .env file")
        print("  2. Check connection string format")
        print("  3. Ensure database is active (not paused) in Neon dashboard")
        print("  4. Verify SSL is enabled (?sslmode=require)")
        print("  5. Check network connectivity")
        print()
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

