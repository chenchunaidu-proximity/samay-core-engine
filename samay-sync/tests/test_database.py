#!/usr/bin/env python3
"""
Test suite for Database Module
Tests database connection, event extraction, and batch processing functionality
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import sqlite3
import json
from datetime import datetime, timezone
import sys
from pathlib import Path

# Add the sync module to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sync.database_module import DatabaseModule


class TestDatabaseModule(unittest.TestCase):
    """Test DatabaseModule functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # Create test database with sample data
        self._create_test_database()
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def _create_test_database(self):
        """Create a test database with sample data"""
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE bucketmodel (
                key INTEGER PRIMARY KEY,
                id TEXT,
                created TEXT,
                name TEXT,
                type TEXT,
                client TEXT,
                hostname TEXT,
                datastr TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE eventmodel (
                id INTEGER PRIMARY KEY,
                bucket_id INTEGER,
                timestamp TEXT,
                duration REAL,
                datastr TEXT,
                FOREIGN KEY (bucket_id) REFERENCES bucketmodel (key)
            )
        """)
        
        # Insert test buckets
        cursor.execute("""
            INSERT INTO bucketmodel (key, id, created, name, type, client, hostname, datastr)
            VALUES (1, 'aw-watcher-window_test', '2024-01-01T00:00:00Z', 'Window Watcher', 'currentwindow', 'aw-watcher-window', 'test-host', '{}')
        """)
        
        cursor.execute("""
            INSERT INTO bucketmodel (key, id, created, name, type, client, hostname, datastr)
            VALUES (2, 'aw-watcher-afk_test', '2024-01-01T00:00:00Z', 'AFK Watcher', 'afkstatus', 'aw-watcher-afk', 'test-host', '{}')
        """)
        
        # Insert test events
        test_events = [
            (1, 1, '2024-01-01T10:00:00Z', 30.5, '{"app": "Safari", "title": "Test Page"}'),
            (2, 1, '2024-01-01T10:01:00Z', 45.0, '{"app": "Chrome", "title": "Another Page"}'),
            (3, 1, '2024-01-01T10:02:00Z', 20.0, '{"app": "VS Code", "title": "test.py"}'),
            (4, 2, '2024-01-01T10:00:00Z', 60.0, '{"status": "not-afk"}'),
            (5, 2, '2024-01-01T10:01:00Z', 30.0, '{"status": "afk"}'),
        ]
        
        cursor.executemany("""
            INSERT INTO eventmodel (id, bucket_id, timestamp, duration, datastr)
            VALUES (?, ?, ?, ?, ?)
        """, test_events)
        
        conn.commit()
        conn.close()
    
    def test_initialization_with_path(self):
        """Test database module initialization with custom path"""
        db = DatabaseModule(self.temp_db.name)
        self.assertEqual(db.db_path, Path(self.temp_db.name))
    
    def test_initialization_without_path(self):
        """Test database module initialization without path (uses config)"""
        with patch('sync.database_module.get_config') as mock_config:
            mock_config.return_value.database.db_path = self.temp_db.name
            db = DatabaseModule()
            self.assertEqual(db.db_path, Path(self.temp_db.name))
    
    def test_database_path_validation(self):
        """Test database path validation"""
        # Test with non-existent file
        with self.assertRaises(FileNotFoundError):
            DatabaseModule("/non/existent/path.db")
        
        # Test with directory instead of file
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                DatabaseModule(temp_dir)
    
    def test_context_manager(self):
        """Test context manager functionality"""
        with DatabaseModule(self.temp_db.name) as db:
            self.assertIsNotNone(db.connection)
            self.assertTrue(hasattr(db.connection, 'execute'))
        
        # Connection should be closed after context
        self.assertIsNone(db.connection)
    
    def test_connect_disconnect(self):
        """Test manual connect/disconnect"""
        db = DatabaseModule(self.temp_db.name)
        
        # Initially not connected
        self.assertIsNone(db.connection)
        
        # Connect
        db.connect()
        self.assertIsNotNone(db.connection)
        
        # Disconnect
        db.disconnect()
        self.assertIsNone(db.connection)
    
    def test_get_database_info(self):
        """Test database info retrieval"""
        with DatabaseModule(self.temp_db.name) as db:
            info = db.get_database_info()
            
            self.assertIn("database_path", info)
            self.assertIn("tables", info)
            self.assertIn("total_events", info)
            self.assertIn("total_buckets", info)
            self.assertIn("connection_status", info)
            
            self.assertEqual(info["total_events"], 5)
            self.assertEqual(info["total_buckets"], 2)
            self.assertIn("eventmodel", info["tables"])
            self.assertIn("bucketmodel", info["tables"])
    
    def test_get_buckets(self):
        """Test bucket retrieval"""
        with DatabaseModule(self.temp_db.name) as db:
            buckets = db.get_buckets()
            
            self.assertEqual(len(buckets), 2)
            
            # Check bucket structure
            bucket = buckets[0]
            self.assertIn("key", bucket)
            self.assertIn("id", bucket)
            self.assertIn("type", bucket)
            self.assertIn("client", bucket)
            self.assertIn("hostname", bucket)
            
            # Check specific buckets
            bucket_ids = [b["id"] for b in buckets]
            self.assertIn("aw-watcher-window_test", bucket_ids)
            self.assertIn("aw-watcher-afk_test", bucket_ids)
    
    def test_get_events_basic(self):
        """Test basic event retrieval"""
        with DatabaseModule(self.temp_db.name) as db:
            events = db.get_events(limit=10)
            
            self.assertEqual(len(events), 5)  # All test events
            
            # Check event structure
            event = events[0]
            self.assertIn("id", event)
            self.assertIn("bucket_id", event)
            self.assertIn("timestamp", event)
            self.assertIn("duration", event)
            self.assertIn("data", event)
            self.assertIn("bucket_name", event)
            self.assertIn("bucket_type", event)
            self.assertIn("client", event)
            self.assertIn("hostname", event)
    
    def test_get_events_with_limit(self):
        """Test event retrieval with limit"""
        with DatabaseModule(self.temp_db.name) as db:
            events = db.get_events(limit=3)
            self.assertEqual(len(events), 3)
    
    def test_get_events_with_offset(self):
        """Test event retrieval with offset"""
        with DatabaseModule(self.temp_db.name) as db:
            events = db.get_events(limit=2, offset=2)
            self.assertEqual(len(events), 2)
            # Events ordered by timestamp DESC: 3, 2, 5, 1, 4
            # offset=2 skips first 2 (3, 2), so we get 5, 1
            self.assertEqual(events[0]["id"], 5)
            self.assertEqual(events[1]["id"], 1)
    
    def test_get_events_with_bucket_filter(self):
        """Test event retrieval with bucket filter"""
        with DatabaseModule(self.temp_db.name) as db:
            # Get events for window watcher bucket only
            events = db.get_events(bucket_id="aw-watcher-window_test")
            self.assertEqual(len(events), 3)  # Only window watcher events
            
            for event in events:
                self.assertEqual(event["bucket_name"], "aw-watcher-window_test")
    
    def test_get_events_with_time_filter(self):
        """Test event retrieval with time filter"""
        with DatabaseModule(self.temp_db.name) as db:
            start_time = datetime(2024, 1, 1, 10, 1, 0, tzinfo=timezone.utc)
            events = db.get_events(start_time=start_time)
            
            # Events from 10:01:00 onwards: 3 (10:02:00), 2 (10:01:00), 5 (10:01:00)
            # Ordered by timestamp DESC: 3, 2, 5
            self.assertEqual(len(events), 3)  # Events 3, 2, 5
    
    def test_get_events_json_parsing(self):
        """Test JSON data parsing in events"""
        with DatabaseModule(self.temp_db.name) as db:
            events = db.get_events(limit=1)
            event = events[0]
            
            # Check that data is parsed as JSON
            self.assertIsInstance(event["data"], dict)
            self.assertIn("app", event["data"])
            self.assertIn("title", event["data"])
    
    def test_get_events_generator(self):
        """Test event generator for batch processing"""
        with DatabaseModule(self.temp_db.name) as db:
            batches = list(db.get_events_generator(batch_size=2))
            
            # Should have 3 batches: [2 events], [2 events], [1 event]
            self.assertEqual(len(batches), 3)
            self.assertEqual(len(batches[0]), 2)
            self.assertEqual(len(batches[1]), 2)
            self.assertEqual(len(batches[2]), 1)
    
    def test_get_event_count(self):
        """Test event count retrieval"""
        with DatabaseModule(self.temp_db.name) as db:
            # Total count
            total_count = db.get_event_count()
            self.assertEqual(total_count, 5)
            
            # Count for specific bucket
            window_count = db.get_event_count("aw-watcher-window_test")
            self.assertEqual(window_count, 3)
            
            afk_count = db.get_event_count("aw-watcher-afk_test")
            self.assertEqual(afk_count, 2)
    
    def test_get_latest_event_timestamp(self):
        """Test latest event timestamp retrieval"""
        with DatabaseModule(self.temp_db.name) as db:
            # Latest overall
            latest = db.get_latest_event_timestamp()
            self.assertIsInstance(latest, datetime)
            self.assertEqual(latest.isoformat(), "2024-01-01T10:02:00+00:00")
            
            # Latest for specific bucket
            window_latest = db.get_latest_event_timestamp("aw-watcher-window_test")
            self.assertEqual(window_latest.isoformat(), "2024-01-01T10:02:00+00:00")
            
            afk_latest = db.get_latest_event_timestamp("aw-watcher-afk_test")
            self.assertEqual(afk_latest.isoformat(), "2024-01-01T10:01:00+00:00")
    
    def test_connection_error_handling(self):
        """Test error handling when not connected"""
        db = DatabaseModule(self.temp_db.name)
        
        # Should raise error when not connected
        with self.assertRaises(RuntimeError):
            db.get_database_info()
        
        with self.assertRaises(RuntimeError):
            db.get_buckets()
        
        with self.assertRaises(RuntimeError):
            db.get_events()
        
        with self.assertRaises(RuntimeError):
            db.get_event_count()
        
        with self.assertRaises(RuntimeError):
            db.get_latest_event_timestamp()


class TestDatabaseModuleIntegration(unittest.TestCase):
    """Integration tests for DatabaseModule"""
    
    def test_full_workflow(self):
        """Test complete database workflow"""
        # Create temporary database
        temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_db.close()
        
        try:
            # Create test database
            conn = sqlite3.connect(temp_db.name)
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute("""
                CREATE TABLE bucketmodel (
                    key INTEGER PRIMARY KEY,
                    id TEXT,
                    created TEXT,
                    name TEXT,
                    type TEXT,
                    client TEXT,
                    hostname TEXT,
                    datastr TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE eventmodel (
                    id INTEGER PRIMARY KEY,
                    bucket_id INTEGER,
                    timestamp TEXT,
                    duration REAL,
                    datastr TEXT,
                    FOREIGN KEY (bucket_id) REFERENCES bucketmodel (key)
                )
            """)
            
            # Insert test data
            cursor.execute("""
                INSERT INTO bucketmodel (key, id, created, name, type, client, hostname, datastr)
                VALUES (1, 'test-bucket', '2024-01-01T00:00:00Z', 'Test Bucket', 'test', 'test-client', 'test-host', '{}')
            """)
            
            cursor.execute("""
                INSERT INTO eventmodel (id, bucket_id, timestamp, duration, datastr)
                VALUES (1, 1, '2024-01-01T10:00:00Z', 30.0, '{"test": "data"}')
            """)
            
            conn.commit()
            conn.close()
            
            # Test full workflow
            with DatabaseModule(temp_db.name) as db:
                # Get info
                info = db.get_database_info()
                self.assertEqual(info["total_events"], 1)
                self.assertEqual(info["total_buckets"], 1)
                
                # Get buckets
                buckets = db.get_buckets()
                self.assertEqual(len(buckets), 1)
                self.assertEqual(buckets[0]["id"], "test-bucket")
                
                # Get events
                events = db.get_events()
                self.assertEqual(len(events), 1)
                self.assertEqual(events[0]["id"], 1)
                self.assertEqual(events[0]["data"]["test"], "data")
                
                # Get count
                count = db.get_event_count()
                self.assertEqual(count, 1)
                
                # Get latest timestamp
                latest = db.get_latest_event_timestamp()
                self.assertEqual(latest.isoformat(), "2024-01-01T10:00:00+00:00")
        
        finally:
            if os.path.exists(temp_db.name):
                os.unlink(temp_db.name)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
