#!/usr/bin/env python3
"""
Test suite for Sync State Manager
Tests sync state tracking, duplicate prevention, and state persistence
"""

import os
import tempfile
import unittest
from unittest.mock import patch
import json
from datetime import datetime, timezone
import sys
from pathlib import Path

# Add the sync module to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sync.state_manager import SyncStateManager, SyncState


class TestSyncState(unittest.TestCase):
    """Test SyncState dataclass functionality"""
    
    def test_sync_state_creation(self):
        """Test SyncState creation with default values"""
        now = datetime.now(timezone.utc).isoformat()
        
        sync_state = SyncState(
            bucket_id="test-bucket",
            last_sync_timestamp=None,
            last_sync_event_id=None,
            total_events_synced=0,
            last_sync_status="never",
            last_sync_error=None,
            created_at=now,
            updated_at=now
        )
        
        self.assertEqual(sync_state.bucket_id, "test-bucket")
        self.assertIsNone(sync_state.last_sync_timestamp)
        self.assertIsNone(sync_state.last_sync_event_id)
        self.assertEqual(sync_state.total_events_synced, 0)
        self.assertEqual(sync_state.last_sync_status, "never")
        self.assertIsNone(sync_state.last_sync_error)
        self.assertEqual(sync_state.created_at, now)
        self.assertEqual(sync_state.updated_at, now)


class TestSyncStateManager(unittest.TestCase):
    """Test SyncStateManager functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary state file for testing
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
        
        # Initialize sync state manager with temp file
        self.sync_manager = SyncStateManager(self.temp_file.name)
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
        if os.path.exists(self.temp_file.name + '.backup'):
            os.unlink(self.temp_file.name + '.backup')
    
    def test_initialization(self):
        """Test sync state manager initialization"""
        self.assertIsInstance(self.sync_manager, SyncStateManager)
        self.assertEqual(self.sync_manager.state_file_path, Path(self.temp_file.name))
        self.assertIsInstance(self.sync_manager._sync_states, dict)
    
    def test_create_sync_state(self):
        """Test creating a new sync state"""
        bucket_id = "test-bucket"
        sync_state = self.sync_manager.create_sync_state(bucket_id)
        
        self.assertIsInstance(sync_state, SyncState)
        self.assertEqual(sync_state.bucket_id, bucket_id)
        self.assertEqual(sync_state.last_sync_status, "never")
        self.assertEqual(sync_state.total_events_synced, 0)
        self.assertIsNone(sync_state.last_sync_event_id)
        
        # Check that it's stored in memory
        stored_state = self.sync_manager.get_sync_state(bucket_id)
        self.assertEqual(stored_state.bucket_id, bucket_id)
    
    def test_get_or_create_sync_state(self):
        """Test get or create sync state functionality"""
        bucket_id = "test-bucket"
        
        # First call should create new state
        sync_state1 = self.sync_manager.get_or_create_sync_state(bucket_id)
        self.assertEqual(sync_state1.bucket_id, bucket_id)
        
        # Second call should return existing state
        sync_state2 = self.sync_manager.get_or_create_sync_state(bucket_id)
        self.assertEqual(sync_state1.bucket_id, sync_state2.bucket_id)
        self.assertEqual(sync_state1.created_at, sync_state2.created_at)
    
    def test_update_sync_success(self):
        """Test updating sync state after successful sync"""
        bucket_id = "test-bucket"
        
        # Create initial state
        sync_state = self.sync_manager.get_or_create_sync_state(bucket_id)
        initial_events = sync_state.total_events_synced
        
        # Update with successful sync
        self.sync_manager.update_sync_success(
            bucket_id,
            "2025-08-22T12:00:00Z",
            100,
            50
        )
        
        # Check updated state
        updated_state = self.sync_manager.get_sync_state(bucket_id)
        self.assertEqual(updated_state.last_sync_status, "success")
        self.assertEqual(updated_state.total_events_synced, initial_events + 50)
        self.assertEqual(updated_state.last_sync_event_id, 100)
        self.assertEqual(updated_state.last_sync_timestamp, "2025-08-22T12:00:00Z")
        self.assertIsNone(updated_state.last_sync_error)
    
    def test_update_sync_failure(self):
        """Test updating sync state after failed sync"""
        bucket_id = "test-bucket"
        
        # Create initial state
        sync_state = self.sync_manager.get_or_create_sync_state(bucket_id)
        initial_events = sync_state.total_events_synced
        
        # Update with failed sync
        error_message = "Network timeout"
        self.sync_manager.update_sync_failure(bucket_id, error_message)
        
        # Check updated state
        updated_state = self.sync_manager.get_sync_state(bucket_id)
        self.assertEqual(updated_state.last_sync_status, "failed")
        self.assertEqual(updated_state.total_events_synced, initial_events)
        self.assertEqual(updated_state.last_sync_error, error_message)
    
    def test_update_sync_partial_failure(self):
        """Test updating sync state after partial sync failure"""
        bucket_id = "test-bucket"
        
        # Create initial state
        sync_state = self.sync_manager.get_or_create_sync_state(bucket_id)
        initial_events = sync_state.total_events_synced
        
        # Update with partial failure (some events synced before failure)
        error_message = "Server error after 25 events"
        events_synced = 25
        self.sync_manager.update_sync_failure(bucket_id, error_message, events_synced)
        
        # Check updated state
        updated_state = self.sync_manager.get_sync_state(bucket_id)
        self.assertEqual(updated_state.last_sync_status, "partial")
        self.assertEqual(updated_state.total_events_synced, initial_events + events_synced)
        self.assertEqual(updated_state.last_sync_error, error_message)
    
    def test_get_events_since_last_sync_first_sync(self):
        """Test getting events since last sync for first sync"""
        bucket_id = "test-bucket"
        test_events = [
            {"id": 1, "data": {"app": "Test1"}},
            {"id": 2, "data": {"app": "Test2"}},
            {"id": 3, "data": {"app": "Test3"}},
        ]
        
        # For first sync, should return all events
        unsynced = self.sync_manager.get_events_since_last_sync(bucket_id, test_events)
        self.assertEqual(len(unsynced), len(test_events))
        self.assertEqual(unsynced, test_events)
    
    def test_get_events_since_last_sync_subsequent_sync(self):
        """Test getting events since last sync for subsequent syncs"""
        bucket_id = "test-bucket"
        test_events = [
            {"id": 1, "data": {"app": "Test1"}},
            {"id": 2, "data": {"app": "Test2"}},
            {"id": 3, "data": {"app": "Test3"}},
            {"id": 4, "data": {"app": "Test4"}},
            {"id": 5, "data": {"app": "Test5"}},
        ]
        
        # Simulate syncing first 3 events
        self.sync_manager.update_sync_success(
            bucket_id,
            "2025-08-22T12:00:00Z",
            3,  # Last synced event ID
            3   # Events synced
        )
        
        # Should return only events after ID 3
        unsynced = self.sync_manager.get_events_since_last_sync(bucket_id, test_events)
        self.assertEqual(len(unsynced), 2)  # Events 4 and 5
        self.assertEqual(unsynced[0]["id"], 4)
        self.assertEqual(unsynced[1]["id"], 5)
    
    def test_get_sync_summary(self):
        """Test getting sync summary"""
        # Create multiple sync states
        bucket1 = "bucket1"
        bucket2 = "bucket2"
        
        # Create states with different statuses
        self.sync_manager.update_sync_success(bucket1, "2025-08-22T12:00:00Z", 100, 50)
        self.sync_manager.update_sync_failure(bucket2, "Network error")
        
        # Get summary
        summary = self.sync_manager.get_sync_summary()
        
        # Check summary structure
        self.assertIn("total_buckets", summary)
        self.assertIn("buckets", summary)
        self.assertIn("overall_status", summary)
        self.assertIn("total_events_synced", summary)
        self.assertIn("successful_syncs", summary)
        self.assertIn("failed_syncs", summary)
        
        # Check values
        self.assertEqual(summary["total_buckets"], 2)
        self.assertEqual(summary["total_events_synced"], 50)
        self.assertEqual(summary["successful_syncs"], 1)
        self.assertEqual(summary["failed_syncs"], 1)
        self.assertEqual(summary["overall_status"], "partial")
        
        # Check bucket details
        self.assertIn(bucket1, summary["buckets"])
        self.assertIn(bucket2, summary["buckets"])
        self.assertEqual(summary["buckets"][bucket1]["status"], "success")
        self.assertEqual(summary["buckets"][bucket2]["status"], "failed")
    
    def test_reset_sync_state(self):
        """Test resetting sync state"""
        bucket_id = "test-bucket"
        
        # Create and update state
        self.sync_manager.update_sync_success(bucket_id, "2025-08-22T12:00:00Z", 100, 50)
        
        # Verify state exists
        self.assertIsNotNone(self.sync_manager.get_sync_state(bucket_id))
        
        # Reset state
        self.sync_manager.reset_sync_state(bucket_id)
        
        # Verify state is gone
        self.assertIsNone(self.sync_manager.get_sync_state(bucket_id))
    
    def test_state_persistence(self):
        """Test state persistence across manager instances"""
        bucket_id = "test-bucket"
        
        # Create state with first manager
        self.sync_manager.update_sync_success(bucket_id, "2025-08-22T12:00:00Z", 100, 50)
        
        # Create new manager instance (should load from file)
        new_manager = SyncStateManager(self.temp_file.name)
        
        # Check that state was persisted
        persisted_state = new_manager.get_sync_state(bucket_id)
        self.assertIsNotNone(persisted_state)
        self.assertEqual(persisted_state.bucket_id, bucket_id)
        self.assertEqual(persisted_state.last_sync_status, "success")
        self.assertEqual(persisted_state.total_events_synced, 50)
        self.assertEqual(persisted_state.last_sync_event_id, 100)


class TestSyncStateManagerIntegration(unittest.TestCase):
    """Integration tests for SyncStateManager"""
    
    def test_full_sync_workflow(self):
        """Test complete sync workflow"""
        # Create temporary state file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        temp_file.close()
        
        try:
            sync_manager = SyncStateManager(temp_file.name)
            
            # Test bucket
            bucket_id = "test-bucket"
            test_events = [
                {"id": 1, "timestamp": "2025-08-22T10:00:00Z", "data": {"app": "Test1"}},
                {"id": 2, "timestamp": "2025-08-22T10:01:00Z", "data": {"app": "Test2"}},
                {"id": 3, "timestamp": "2025-08-22T10:02:00Z", "data": {"app": "Test3"}},
                {"id": 4, "timestamp": "2025-08-22T10:03:00Z", "data": {"app": "Test4"}},
                {"id": 5, "timestamp": "2025-08-22T10:04:00Z", "data": {"app": "Test5"}},
            ]
            
            # Step 1: First sync (all events)
            unsynced = sync_manager.get_events_since_last_sync(bucket_id, test_events)
            self.assertEqual(len(unsynced), 5)
            
            # Sync first 3 events
            events_to_sync = unsynced[:3]
            last_event = events_to_sync[-1]
            sync_manager.update_sync_success(
                bucket_id,
                last_event["timestamp"],
                last_event["id"],
                len(events_to_sync)
            )
            
            # Step 2: Second sync (remaining events)
            unsynced = sync_manager.get_events_since_last_sync(bucket_id, test_events)
            self.assertEqual(len(unsynced), 2)  # Events 4 and 5
            
            # Sync remaining events
            events_to_sync = unsynced
            last_event = events_to_sync[-1]
            sync_manager.update_sync_success(
                bucket_id,
                last_event["timestamp"],
                last_event["id"],
                len(events_to_sync)
            )
            
            # Step 3: Third sync (no new events)
            unsynced = sync_manager.get_events_since_last_sync(bucket_id, test_events)
            self.assertEqual(len(unsynced), 0)  # No new events
            
            # Verify final state
            sync_state = sync_manager.get_sync_state(bucket_id)
            self.assertEqual(sync_state.total_events_synced, 5)
            self.assertEqual(sync_state.last_sync_event_id, 5)
            self.assertEqual(sync_state.last_sync_status, "success")
            
            # Verify summary
            summary = sync_manager.get_sync_summary()
            self.assertEqual(summary["total_events_synced"], 5)
            self.assertEqual(summary["overall_status"], "healthy")
        
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            if os.path.exists(temp_file.name + '.backup'):
                os.unlink(temp_file.name + '.backup')
    
    def test_error_recovery_workflow(self):
        """Test error recovery workflow"""
        # Create temporary state file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        temp_file.close()
        
        try:
            sync_manager = SyncStateManager(temp_file.name)
            bucket_id = "test-bucket"
            
            # Simulate successful sync
            sync_manager.update_sync_success(bucket_id, "2025-08-22T12:00:00Z", 100, 50)
            
            # Simulate failure
            sync_manager.update_sync_failure(bucket_id, "Network timeout")
            
            # Check state
            sync_state = sync_manager.get_sync_state(bucket_id)
            self.assertEqual(sync_state.last_sync_status, "failed")
            self.assertEqual(sync_state.total_events_synced, 50)  # Should not change
            
            # Simulate recovery with successful sync
            sync_manager.update_sync_success(bucket_id, "2025-08-22T12:05:00Z", 150, 25)
            
            # Check final state
            final_state = sync_manager.get_sync_state(bucket_id)
            self.assertEqual(final_state.last_sync_status, "success")
            self.assertEqual(final_state.total_events_synced, 75)  # 50 + 25
            self.assertEqual(final_state.last_sync_event_id, 150)
            self.assertIsNone(final_state.last_sync_error)
        
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            if os.path.exists(temp_file.name + '.backup'):
                os.unlink(temp_file.name + '.backup')


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
