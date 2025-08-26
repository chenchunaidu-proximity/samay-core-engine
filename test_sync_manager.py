#!/usr/bin/env python3
"""
Test script for Sync State Manager
Demonstrates sync state tracking and duplicate prevention

This test file validates the Sync State Manager functionality:
1. Tests sync state creation and management
2. Verifies duplicate prevention logic
3. Tests state persistence across instances
4. Simulates real ActivityWatch data integration
5. Validates error handling and recovery scenarios

Run this to verify the sync state manager is working correctly.
"""

import sys
import json
from pathlib import Path

# Add samay_sync to path
sys.path.append(str(Path(__file__).parent))

from samay_sync.database import ActivityWatchDB
from samay_sync.sync_manager import SyncStateManager

def test_sync_state_management():
    """Test the sync state manager with real ActivityWatch data"""
    print("🔄 Testing Sync State Manager")
    print("=" * 50)
    
    try:
        # Initialize sync state manager
        sync_manager = SyncStateManager()
        print("✅ Sync State Manager initialized")
        
        # Get sync summary (should be empty initially)
        summary = sync_manager.get_sync_summary()
        print(f"\n📊 Initial Sync Summary:")
        print(json.dumps(summary, indent=2))
        
        # Connect to ActivityWatch database
        with ActivityWatchDB() as db:
            print("\n🔍 Connected to ActivityWatch database")
            
            # Get buckets
            buckets = db.get_buckets()
            print(f"Found {len(buckets)} buckets")
            
            for bucket in buckets:
                bucket_id = bucket['id']
                print(f"\n🪣 Processing bucket: {bucket_id}")
                
                # Get all events for this bucket
                all_events = db.get_events(bucket_id=bucket_id)
                print(f"Total events in bucket: {len(all_events)}")
                
                # Get events that haven't been synced yet
                unsynced_events = sync_manager.get_events_since_last_sync(bucket_id, all_events)
                print(f"Events to sync: {len(unsynced_events)}")
                
                if unsynced_events:
                    # Simulate syncing the first few events
                    events_to_sync = unsynced_events[:3]  # Sync first 3 events
                    last_event = events_to_sync[-1]
                    
                    print(f"Syncing {len(events_to_sync)} events...")
                    
                    # Update sync state as if sync was successful
                    sync_manager.update_sync_success(
                        bucket_id=bucket_id,
                        last_event_timestamp=last_event['timestamp'],
                        last_event_id=last_event['id'],
                        events_synced=len(events_to_sync)
                    )
                    
                    print(f"✅ Synced {len(events_to_sync)} events")
                    
                    # Show what events were synced
                    for i, event in enumerate(events_to_sync, 1):
                        print(f"  {i}. ID: {event['id']}, App: {event['data'].get('app', 'Unknown')}")
                    
                    # Now check what's left to sync
                    remaining_events = sync_manager.get_events_since_last_sync(bucket_id, all_events)
                    print(f"Remaining events to sync: {len(remaining_events)}")
                    
                    # Get updated sync summary
                    updated_summary = sync_manager.get_sync_summary()
                    print(f"\n📊 Updated Sync Summary:")
                    print(json.dumps(updated_summary, indent=2))
                    
                    # Show specific bucket status
                    bucket_status = updated_summary['buckets'].get(bucket_id, {})
                    print(f"\n🪣 Bucket '{bucket_id}' Status:")
                    print(f"  Last Sync: {bucket_status.get('last_sync', 'Never')}")
                    print(f"  Events Synced: {bucket_status.get('events_synced', 0)}")
                    print(f"  Status: {bucket_status.get('status', 'Unknown')}")
                    
                else:
                    print("✅ All events already synced for this bucket")
        
        # Final sync summary
        final_summary = sync_manager.get_sync_summary()
        print(f"\n🎯 Final Sync Summary:")
        print(json.dumps(final_summary, indent=2))
        
        # Test error handling
        print(f"\n🧪 Testing Error Handling...")
        sync_manager.update_sync_failure(
            "test_bucket_error",
            "Simulated network error for testing",
            events_synced=0
        )
        
        error_summary = sync_manager.get_sync_summary()
        print(f"After error test:")
        print(json.dumps(error_summary, indent=2))
        
        # Clean up test data
        sync_manager.reset_sync_state("test_bucket_error")
        print("🧹 Cleaned up test data")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Error type: {type(e).__name__}")

def test_sync_state_persistence():
    """Test that sync states are properly saved and loaded"""
    print("\n💾 Testing Sync State Persistence")
    print("=" * 40)
    
    try:
        # Create first sync manager instance
        sync_manager1 = SyncStateManager()
        
        # Create a test sync state
        test_bucket = "persistence_test_bucket"
        sync_state = sync_manager1.get_or_create_sync_state(test_bucket)
        print(f"✅ Created sync state for {test_bucket}")
        
        # Update sync state
        sync_manager1.update_sync_success(
            test_bucket,
            "2025-08-22T12:00:00Z",
            999,
            100
        )
        print(f"✅ Updated sync state")
        
        # Get summary from first instance
        summary1 = sync_manager1.get_sync_summary()
        print(f"📊 Summary from first instance:")
        print(json.dumps(summary1, indent=2))
        
        # Create second sync manager instance (should load existing state)
        sync_manager2 = SyncStateManager()
        
        # Get summary from second instance
        summary2 = sync_manager2.get_sync_summary()
        print(f"📊 Summary from second instance:")
        print(json.dumps(summary2, indent=2))
        
        # Verify they're the same
        if summary1 == summary2:
            print("✅ Sync states persisted correctly between instances")
        else:
            print("❌ Sync states did not persist correctly")
        
        # Clean up
        sync_manager1.reset_sync_state(test_bucket)
        print("🧹 Cleaned up test data")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Test basic functionality
    test_sync_state_management()
    
    # Test persistence
    test_sync_state_persistence()
    
    print("\n🎉 Sync State Manager testing complete!")
