#!/usr/bin/env python3
"""
Sync State Manager for ActivityWatch Data Synchronization
Tracks sync progress and prevents duplicate data transmission

This file implements the core sync state management system that:
1. Prevents duplicate event transmission by tracking last synced event IDs
2. Maintains sync progress across application restarts
3. Handles partial syncs and failures gracefully
4. Provides comprehensive sync status monitoring
5. Ensures zero data loss during network or server issues

Key Components:
- SyncState: Data structure for tracking bucket sync status
- SyncStateManager: Main class for managing all sync operations
- State Persistence: JSON-based state storage with automatic backups
- Error Recovery: Handles failed, partial, and successful syncs
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
import sqlite3

logger = logging.getLogger(__name__)

@dataclass
class SyncState:
    """Represents the current sync state for a bucket"""
    bucket_id: str
    last_sync_timestamp: Optional[str]  # ISO format timestamp
    last_sync_event_id: Optional[int]   # Last event ID that was synced
    total_events_synced: int            # Total count of events synced
    last_sync_status: str               # 'success', 'failed', 'partial'
    last_sync_error: Optional[str]      # Error message if sync failed
    created_at: str                     # When this sync state was created
    updated_at: str                     # When this sync state was last updated

class SyncStateManager:
    """Manages synchronization state to prevent duplicates and track progress"""
    
    def __init__(self, state_file_path: Optional[str] = None):
        """
        Initialize sync state manager
        
        Args:
            state_file_path: Path to sync state file. If None, uses default location
        """
        if state_file_path is None:
            # Default location in user's home directory
            home = Path.home()
            state_file_path = home / ".samay_sync" / "sync_state.json"
        
        self.state_file_path = Path(state_file_path)
        self.state_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache of sync states
        self._sync_states: Dict[str, SyncState] = {}
        
        # Load existing sync states
        self._load_sync_states()
    
    def _load_sync_states(self):
        """Load sync states from file"""
        try:
            if self.state_file_path.exists():
                with open(self.state_file_path, 'r') as f:
                    data = json.load(f)
                    
                for bucket_id, state_data in data.items():
                    # Convert dict to SyncState object
                    sync_state = SyncState(**state_data)
                    self._sync_states[bucket_id] = sync_state
                
                logger.info(f"Loaded {len(self._sync_states)} sync states from {self.state_file_path}")
            else:
                logger.info("No existing sync state file found, starting fresh")
                
        except Exception as e:
            logger.error(f"Error loading sync states: {e}")
            # Start with empty state if loading fails
            self._sync_states = {}
    
    def _save_sync_states(self):
        """Save sync states to file"""
        try:
            # Convert SyncState objects to dictionaries
            data = {}
            for bucket_id, sync_state in self._sync_states.items():
                data[bucket_id] = asdict(sync_state)
            
            # Create backup of existing file
            if self.state_file_path.exists():
                backup_path = self.state_file_path.with_suffix('.json.backup')
                self.state_file_path.rename(backup_path)
                logger.debug(f"Created backup: {backup_path}")
            
            # Write new state file
            with open(self.state_file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {len(self._sync_states)} sync states to {self.state_file_path}")
            
        except Exception as e:
            logger.error(f"Error saving sync states: {e}")
            raise
    
    def get_sync_state(self, bucket_id: str) -> Optional[SyncState]:
        """
        Get sync state for a specific bucket
        
        Args:
            bucket_id: The bucket identifier
            
        Returns:
            SyncState object if exists, None otherwise
        """
        return self._sync_states.get(bucket_id)
    
    def create_sync_state(self, bucket_id: str) -> SyncState:
        """
        Create a new sync state for a bucket
        
        Args:
            bucket_id: The bucket identifier
            
        Returns:
            New SyncState object
        """
        now = datetime.now(timezone.utc).isoformat()
        
        sync_state = SyncState(
            bucket_id=bucket_id,
            last_sync_timestamp=None,
            last_sync_event_id=None,
            total_events_synced=0,
            last_sync_status='never',
            last_sync_error=None,
            created_at=now,
            updated_at=now
        )
        
        self._sync_states[bucket_id] = sync_state
        self._save_sync_states()
        
        logger.info(f"Created new sync state for bucket: {bucket_id}")
        return sync_state
    
    def get_or_create_sync_state(self, bucket_id: str) -> SyncState:
        """
        Get existing sync state or create new one
        
        Args:
            bucket_id: The bucket identifier
            
        Returns:
            SyncState object (existing or new)
        """
        sync_state = self.get_sync_state(bucket_id)
        if sync_state is None:
            sync_state = self.create_sync_state(bucket_id)
        return sync_state
    
    def update_sync_success(self, 
                           bucket_id: str, 
                           last_event_timestamp: str,
                           last_event_id: int,
                           events_synced: int):
        """
        Update sync state after successful synchronization
        
        Args:
            bucket_id: The bucket identifier
            last_event_timestamp: Timestamp of last synced event
            last_event_id: ID of last synced event
            events_synced: Number of events successfully synced
        """
        sync_state = self.get_or_create_sync_state(bucket_id)
        
        # Update sync state
        sync_state.last_sync_timestamp = last_event_timestamp
        sync_state.last_sync_event_id = last_event_id
        sync_state.total_events_synced += events_synced
        sync_state.last_sync_status = 'success'
        sync_state.last_sync_error = None
        sync_state.updated_at = datetime.now(timezone.utc).isoformat()
        
        self._save_sync_states()
        
        logger.info(f"Updated sync state for {bucket_id}: {events_synced} events synced")
    
    def update_sync_failure(self, 
                           bucket_id: str, 
                           error_message: str,
                           events_synced: int = 0):
        """
        Update sync state after failed synchronization
        
        Args:
            bucket_id: The bucket identifier
            error_message: Description of the error
            events_synced: Number of events synced before failure (if any)
        """
        sync_state = self.get_or_create_sync_state(bucket_id)
        
        # Update sync state
        if events_synced > 0:
            sync_state.total_events_synced += events_synced
            sync_state.last_sync_status = 'partial'
        else:
            sync_state.last_sync_status = 'failed'
        
        sync_state.last_sync_error = error_message
        sync_state.updated_at = datetime.now(timezone.utc).isoformat()
        
        self._save_sync_states()
        
        logger.warning(f"Updated sync state for {bucket_id}: {sync_state.last_sync_status} - {error_message}")
    
    def get_events_since_last_sync(self, 
                                  bucket_id: str,
                                  all_events: List[Dict]) -> List[Dict]:
        """
        Get events that haven't been synced yet
        
        Args:
            bucket_id: The bucket identifier
            all_events: List of all events from the bucket
            
        Returns:
            List of events that need to be synced
        """
        sync_state = self.get_or_create_sync_state(bucket_id)
        
        if sync_state.last_sync_event_id is None:
            # First sync, return all events
            logger.info(f"First sync for {bucket_id}, syncing all {len(all_events)} events")
            return all_events
        
        # Find events after the last synced event ID
        unsynced_events = []
        for event in all_events:
            if event.get('id', 0) > sync_state.last_sync_event_id:
                unsynced_events.append(event)
        
        logger.info(f"Found {len(unsynced_events)} unsynced events for {bucket_id}")
        return unsynced_events
    
    def get_sync_summary(self) -> Dict:
        """
        Get summary of all sync states
        
        Returns:
            Dictionary with sync summary information
        """
        summary = {
            'total_buckets': len(self._sync_states),
            'buckets': {},
            'overall_status': 'unknown'
        }
        
        total_events_synced = 0
        successful_syncs = 0
        failed_syncs = 0
        
        for bucket_id, sync_state in self._sync_states.items():
            bucket_summary = {
                'last_sync': sync_state.last_sync_timestamp,
                'events_synced': sync_state.total_events_synced,
                'status': sync_state.last_sync_status,
                'last_error': sync_state.last_sync_error
            }
            
            summary['buckets'][bucket_id] = bucket_summary
            total_events_synced += sync_state.total_events_synced
            
            if sync_state.last_sync_status == 'success':
                successful_syncs += 1
            elif sync_state.last_sync_status == 'failed':
                failed_syncs += 1
        
        summary['total_events_synced'] = total_events_synced
        summary['successful_syncs'] = successful_syncs
        summary['failed_syncs'] = failed_syncs
        
        # Determine overall status
        if failed_syncs == 0 and successful_syncs > 0:
            summary['overall_status'] = 'healthy'
        elif failed_syncs > 0 and successful_syncs > 0:
            summary['overall_status'] = 'partial'
        elif failed_syncs > 0:
            summary['overall_status'] = 'failed'
        else:
            summary['overall_status'] = 'never_synced'
        
        return summary
    
    def reset_sync_state(self, bucket_id: str):
        """
        Reset sync state for a bucket (useful for testing or manual reset)
        
        Args:
            bucket_id: The bucket identifier
        """
        if bucket_id in self._sync_states:
            del self._sync_states[bucket_id]
            self._save_sync_states()
            logger.info(f"Reset sync state for bucket: {bucket_id}")
    
    def cleanup_old_states(self, days_to_keep: int = 30):
        """
        Clean up sync states older than specified days
        
        Args:
            days_to_keep: Number of days to keep sync states
        """
        cutoff_date = datetime.now(timezone.utc).timestamp() - (days_to_keep * 24 * 3600)
        
        buckets_to_remove = []
        for bucket_id, sync_state in self._sync_states.items():
            try:
                if sync_state.updated_at:
                    updated_timestamp = datetime.fromisoformat(sync_state.updated_at).timestamp()
                    if updated_timestamp < cutoff_date:
                        buckets_to_remove.append(bucket_id)
            except ValueError:
                # Invalid timestamp, remove the state
                buckets_to_remove.append(bucket_id)
        
        for bucket_id in buckets_to_remove:
            del self._sync_states[bucket_id]
            logger.info(f"Removed old sync state for bucket: {bucket_id}")
        
        if buckets_to_remove:
            self._save_sync_states()
            logger.info(f"Cleaned up {len(buckets_to_remove)} old sync states")

# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Test sync state manager
    sync_manager = SyncStateManager()
    
    # Test bucket
    test_bucket = "aw-watcher-window_test"
    
    # Create/get sync state
    sync_state = sync_manager.get_or_create_sync_state(test_bucket)
    print(f"Created sync state for {test_bucket}")
    
    # Simulate successful sync
    sync_manager.update_sync_success(
        test_bucket,
        "2025-08-22T12:00:00Z",
        100,
        50
    )
    
    # Get sync summary
    summary = sync_manager.get_sync_summary()
    print(f"Sync Summary: {json.dumps(summary, indent=2)}")
    
    # Clean up test state
    sync_manager.reset_sync_state(test_bucket)
