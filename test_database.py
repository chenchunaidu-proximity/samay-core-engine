#!/usr/bin/env python3
"""
Test script for ActivityWatch database connection
"""

import sys
import json
from pathlib import Path

# Add samay_sync to path
sys.path.append(str(Path(__file__).parent))

from samay_sync.database import ActivityWatchDB

def test_database_connection():
    """Test the database connection and basic operations"""
    print("🔍 Testing ActivityWatch Database Connection")
    print("=" * 50)
    
    try:
        # Test database connection
        with ActivityWatchDB() as db:
            print("✅ Database connection successful!")
            
            # Get database info
            print("\n📊 Database Information:")
            info = db.get_database_info()
            print(json.dumps(info, indent=2, default=str))
            
            # Get buckets
            print("\n🪣 Available Buckets:")
            buckets = db.get_buckets()
            for bucket in buckets:
                print(f"  • {bucket['id']}")
                print(f"    - Events: {bucket.get('event_count', 'Unknown')}")
                print(f"    - First: {bucket.get('first_event', 'Unknown')}")
                print(f"    - Last: {bucket.get('last_event', 'Unknown')}")
                print()
            
            # Get sample events
            if buckets:
                print("📅 Sample Events (latest 3):")
                sample_events = db.get_events(limit=3)
                for i, event in enumerate(sample_events, 1):
                    print(f"  {i}. Timestamp: {event.get('timestamp', 'N/A')}")
                    print(f"     Duration: {event.get('duration', 'N/A')}s")
                    print(f"     Bucket: {event.get('bucket_id', 'N/A')}")
                    print(f"     Data: {event.get('data', {})}")
                    print()
            
            # Test event count
            total_events = db.get_event_count()
            print(f"📈 Total Events in Database: {total_events}")
            
    except FileNotFoundError as e:
        print(f"❌ Database file not found: {e}")
        print("\n💡 Make sure ActivityWatch is running and has collected some data.")
        print("   Try running: ./scripts/run.sh")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Error type: {type(e).__name__}")

if __name__ == "__main__":
    test_database_connection()
