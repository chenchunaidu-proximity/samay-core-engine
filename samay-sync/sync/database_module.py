#!/usr/bin/env python3
"""
Database Module for Samay Sync MVP
Direct SQLite access to ActivityWatch database for event extraction

This module provides:
1. Direct SQLite connection to ActivityWatch database
2. Event extraction with filtering and batch processing
3. Memory-efficient processing for large datasets
4. Context manager for safe database connections
"""

import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Generator
import sys
import os

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.sync_config import get_config


class DatabaseModule:
    """Manages direct SQLite connection to ActivityWatch database"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database. If None, uses config default
        """
        if db_path is None:
            config = get_config()
            db_path = config.database.db_path
        
        self.db_path = Path(db_path)
        self.connection = None
        self._validate_db_path()
    
    def _validate_db_path(self):
        """Validate that the database file exists and is accessible"""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found at: {self.db_path}")
        
        if not self.db_path.is_file():
            raise ValueError(f"Path is not a file: {self.db_path}")
    
    def connect(self):
        """Establish connection to SQLite database"""
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row  # Enable dict-like access
        except sqlite3.Error as e:
            raise ConnectionError(f"Failed to connect to database: {e}")
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
    
    def get_database_info(self) -> Dict:
        """Get basic information about the database"""
        if not self.connection:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        try:
            cursor = self.connection.cursor()
            
            # Get table information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Get event count
            event_count = 0
            if 'eventmodel' in tables:
                cursor.execute("SELECT COUNT(*) FROM eventmodel")
                event_count = cursor.fetchone()[0]
            
            # Get bucket count
            bucket_count = 0
            if 'bucketmodel' in tables:
                cursor.execute("SELECT COUNT(*) FROM bucketmodel")
                bucket_count = cursor.fetchone()[0]
            
            return {
                "database_path": str(self.db_path),
                "tables": tables,
                "total_events": event_count,
                "total_buckets": bucket_count,
                "connection_status": "connected"
            }
            
        except sqlite3.Error as e:
            raise RuntimeError(f"Error getting database info: {e}")
    
    def get_buckets(self) -> List[Dict]:
        """Get all available data buckets"""
        if not self.connection:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT key, id, created, name, type, client, hostname, datastr
                FROM bucketmodel
                ORDER BY key
            """)
            
            buckets = []
            for row in cursor.fetchall():
                bucket = dict(row)
                buckets.append(bucket)
            
            return buckets
            
        except sqlite3.Error as e:
            raise RuntimeError(f"Error getting buckets: {e}")
    
    def get_events(self, 
                   bucket_id: Optional[str] = None,
                   limit: int = 1000,
                   offset: int = 0,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None) -> List[Dict]:
        """
        Get events from database with optional filtering
        
        Args:
            bucket_id: Filter by specific bucket ID (bucket name, not key)
            limit: Maximum number of events to return
            offset: Number of events to skip
            start_time: Filter events after this time
            end_time: Filter events before this time
        
        Returns:
            List of event dictionaries
        """
        if not self.connection:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        try:
            cursor = self.connection.cursor()
            
            # Build query with JOIN to get bucket information
            query = """
                SELECT e.id, e.bucket_id, e.timestamp, e.duration, e.datastr,
                       b.id as bucket_name, b.type as bucket_type, b.client, b.hostname
                FROM eventmodel e
                JOIN bucketmodel b ON e.bucket_id = b.key
            """
            params = []
            conditions = []
            
            if bucket_id:
                conditions.append("b.id = ?")
                params.append(bucket_id)
            
            if start_time:
                conditions.append("e.timestamp >= ?")
                params.append(start_time.isoformat())
            
            if end_time:
                conditions.append("e.timestamp <= ?")
                params.append(end_time.isoformat())
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY e.timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            
            events = []
            for row in cursor.fetchall():
                event = dict(row)
                # Parse JSON data if present
                if 'datastr' in event and event['datastr']:
                    try:
                        event['data'] = json.loads(event['datastr'])
                    except json.JSONDecodeError:
                        # Keep as string if not valid JSON
                        event['data'] = event['datastr']
                else:
                    event['data'] = {}
                
                # Remove the raw datastr field
                event.pop('datastr', None)
                
                events.append(event)
            
            return events
            
        except sqlite3.Error as e:
            raise RuntimeError(f"Error getting events: {e}")
    
    def get_events_generator(self, 
                            bucket_id: Optional[str] = None,
                            batch_size: int = 1000,
                            start_time: Optional[datetime] = None,
                            end_time: Optional[datetime] = None) -> Generator[List[Dict], None, None]:
        """
        Generator for processing events in batches (memory efficient for large datasets)
        
        Args:
            bucket_id: Filter by specific bucket ID
            batch_size: Number of events per batch
            start_time: Filter events after this time
            end_time: Filter events before this time
        
        Yields:
            Batches of events as lists
        """
        offset = 0
        while True:
            events = self.get_events(
                bucket_id=bucket_id,
                limit=batch_size,
                offset=offset,
                start_time=start_time,
                end_time=end_time
            )
            
            if not events:
                break
            
            yield events
            offset += batch_size
    
    def get_event_count(self, bucket_id: Optional[str] = None) -> int:
        """Get total count of events"""
        if not self.connection:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        try:
            cursor = self.connection.cursor()
            
            if bucket_id:
                # Count events for specific bucket
                query = """
                    SELECT COUNT(*) 
                    FROM eventmodel e
                    JOIN bucketmodel b ON e.bucket_id = b.key
                    WHERE b.id = ?
                """
                cursor.execute(query, [bucket_id])
            else:
                # Count all events
                cursor.execute("SELECT COUNT(*) FROM eventmodel")
            
            count = cursor.fetchone()[0]
            return count
            
        except sqlite3.Error as e:
            raise RuntimeError(f"Error getting event count: {e}")
    
    def get_latest_event_timestamp(self, bucket_id: Optional[str] = None) -> Optional[datetime]:
        """Get the timestamp of the most recent event"""
        if not self.connection:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        try:
            cursor = self.connection.cursor()
            
            if bucket_id:
                # Get latest event for specific bucket
                query = """
                    SELECT e.timestamp
                    FROM eventmodel e
                    JOIN bucketmodel b ON e.bucket_id = b.key
                    WHERE b.id = ?
                    ORDER BY e.timestamp DESC
                    LIMIT 1
                """
                cursor.execute(query, [bucket_id])
            else:
                # Get latest event overall
                cursor.execute("SELECT timestamp FROM eventmodel ORDER BY timestamp DESC LIMIT 1")
            
            result = cursor.fetchone()
            if result:
                timestamp_str = result[0]
                try:
                    # Parse the timestamp string
                    return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except ValueError:
                    return None
            
            return None
            
        except sqlite3.Error as e:
            raise RuntimeError(f"Error getting latest event timestamp: {e}")


# Example usage and testing
if __name__ == "__main__":
    try:
        with DatabaseModule() as db:
            # Get database info
            info = db.get_database_info()
            print("Database Info:")
            print(f"  Path: {info['database_path']}")
            print(f"  Tables: {info['tables']}")
            print(f"  Total Events: {info['total_events']}")
            print(f"  Total Buckets: {info['total_buckets']}")
            
            # Get buckets
            buckets = db.get_buckets()
            print(f"\nFound {len(buckets)} buckets:")
            for bucket in buckets:
                print(f"  - {bucket['id']}")
                print(f"    Type: {bucket['type']}")
                print(f"    Client: {bucket['client']}")
                print(f"    Hostname: {bucket['hostname']}")
                print()
            
            # Get sample events
            if buckets:
                sample_events = db.get_events(limit=3)
                print(f"Sample events:")
                for event in sample_events:
                    print(f"  - {event.get('timestamp', 'N/A')}: {event.get('data', {})}")
                    
    except FileNotFoundError as e:
        print(f"❌ Database file not found: {e}")
        print("\n💡 Make sure ActivityWatch is running and has collected some data.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Error type: {type(e).__name__}")
