#!/usr/bin/env python3
"""
Samay Sync - Web Dashboard
=========================

A web interface to showcase Samay Sync progress to the team.
Demonstrates all modules working together with real-time updates.

Usage:
    python3 samay-sync/demo/web_dashboard.py
    Or use: ./scripts/start_dashboard.sh
    Then open http://localhost:8080 in your browser
"""

import os
import sys
import json
import time
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our modules
from config.sync_config import get_config
from sync.database_module import DatabaseModule
from sync.state_manager import SyncStateManager
from sync.sync_manager import SyncManager
from auth.oauth_manager import OAuthManager

# Global SyncManager instance
_sync_manager_instance = None

def get_sync_manager():
    """Get or create the global SyncManager instance"""
    global _sync_manager_instance
    if _sync_manager_instance is None:
        config = get_config()
        _sync_manager_instance = SyncManager(config)
        # Don't auto-start sync in dashboard - let user control it
        # _sync_manager_instance.start_auto_sync()  # Removed this line
    return _sync_manager_instance


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP handler for the web dashboard"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        
        if path == '/':
            self.serve_dashboard()
        elif path == '/api/status':
            self.serve_api_status()
        elif path == '/api/modules':
            self.serve_api_modules()
        elif path == '/api/data':
            self.serve_api_data()
        elif path == '/api/login':
            self.serve_api_login()
        elif path == '/api/logout':
            self.serve_api_logout()
        elif path == '/api/database':
            self.serve_api_database()
        elif path == '/api/sync-state':
            self.serve_api_sync_state()
        elif path == '/api/sync-manager':
            self.serve_api_sync_manager()
        elif path == '/api/sync-start':
            self.serve_api_sync_start()
        elif path == '/api/sync-stop':
            self.serve_api_sync_stop()
        elif path == '/favicon.ico':
            self.serve_favicon()
        else:
            self.send_error(404)
    
    def serve_dashboard(self):
        """Serve the main dashboard HTML"""
        html = self.get_dashboard_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_api_status(self):
        """Serve API status endpoint"""
        try:
            status = self.get_system_status()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
        except Exception as e:
            self.send_error(500, str(e))
    
    def serve_api_modules(self):
        """Serve API modules endpoint"""
        try:
            modules = self.get_modules_status()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(modules).encode())
        except Exception as e:
            self.send_error(500, str(e))
    
    def serve_api_data(self):
        """Serve API data endpoint"""
        try:
            data = self.get_live_data()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        except Exception as e:
            self.send_error(500, str(e))
    
    def serve_api_login(self):
        """Serve API login endpoint"""
        try:
            oauth_manager = OAuthManager()
            if oauth_manager.is_authenticated():
                result = {"status": "already_authenticated", "message": "Already logged in"}
            else:
                # Simulate OAuth flow
                code_verifier, code_challenge = oauth_manager._generate_pkce_challenge()
                auth_url = oauth_manager._build_auth_url('demo-state', code_challenge)
                
                # Simulate successful login for demo
                oauth_manager.token_storage.store_tokens('demo_access_token', 'demo_refresh_token', 3600)
                
                result = {
                    "status": "success", 
                    "message": "Login successful!",
                    "auth_url": auth_url,
                    "token_stored": True
                }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        except Exception as e:
            self.send_error(500, str(e))
    
    def serve_api_logout(self):
        """Serve API logout endpoint"""
        try:
            oauth_manager = OAuthManager()
            if oauth_manager.is_authenticated():
                oauth_manager.logout()
                result = {"status": "success", "message": "Logout successful!"}
            else:
                result = {"status": "not_authenticated", "message": "Not logged in"}
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        except Exception as e:
            self.send_error(500, str(e))
    
    def serve_api_database(self):
        """Serve API database endpoint"""
        try:
            db = DatabaseModule()
            with db:
                info = db.get_database_info()
                buckets = db.get_buckets()
                
                bucket_details = []
                for bucket in buckets:
                    bucket_id = bucket['id']
                    events = db.get_events(bucket_id=bucket_id, limit=20)
                    
                    bucket_details.append({
                        "id": bucket_id,
                        "name": bucket.get('name', bucket_id),
                        "total_events": len(events),
                        "events": [
                            {
                                "id": event["id"],
                                "timestamp": event["timestamp"],
                                "duration": event["duration"],
                                "data": event["data"]
                            }
                            for event in events
                        ]
                    })
                
                result = {
                    "database_info": info,
                    "buckets": bucket_details,
                    "timestamp": datetime.now().isoformat()
                }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        except Exception as e:
            self.send_error(500, str(e))
    
    def serve_api_sync_state(self):
        """Serve API sync state endpoint"""
        try:
            sync_manager = SyncStateManager()
            summary = sync_manager.get_sync_summary()
            
            # Get detailed sync states
            sync_states = {}
            for bucket_id in summary.get('bucket_ids', []):
                state = sync_manager.get_sync_state(bucket_id)
                sync_states[bucket_id] = {
                    "last_sync_timestamp": state.last_sync_timestamp,
                    "last_sync_event_id": state.last_sync_event_id,
                    "last_sync_status": state.last_sync_status,
                    "total_events_synced": state.total_events_synced,
                    "last_error": state.last_error
                }
            
            result = {
                "summary": summary,
                "sync_states": sync_states,
                "timestamp": datetime.now().isoformat()
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        except Exception as e:
            self.send_error(500, str(e))
    
    def get_system_status(self):
        """Get overall system status"""
        try:
            config = get_config()
            return {
                "status": "running",
                "timestamp": datetime.now().isoformat(),
                "config_loaded": True,
                "database_path": config.database.db_path,
                "sync_interval": config.sync.sync_interval,
                "oauth_client_id": config.oauth.client_id[:10] + "..." if config.oauth.client_id else "Not configured"
            }
        except Exception as e:
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def get_modules_status(self):
        """Get status of all modules"""
        modules = {}
        
        # Configuration Module
        try:
            config = get_config()
            modules["config"] = {
                "status": "✅ Working",
                "database_path": config.database.db_path,
                "sync_interval": config.sync.sync_interval,
                "oauth_configured": bool(config.oauth.client_id)
            }
        except Exception as e:
            modules["config"] = {"status": f"❌ Error: {str(e)}"}
        
        # Database Module
        try:
            db = DatabaseModule()
            with db:
                info = db.get_database_info()
                modules["database"] = {
                    "status": "✅ Connected",
                    "total_events": info["total_events"],
                    "total_buckets": info["total_buckets"],
                    "connection_status": info["connection_status"]
                }
        except Exception as e:
            modules["database"] = {"status": f"❌ Error: {str(e)}"}
        
        # Sync State Manager
        try:
            sync_manager = SyncStateManager()
            summary = sync_manager.get_sync_summary()
            modules["sync_state"] = {
                "status": "✅ Ready",
                "total_buckets": summary["total_buckets"],
                "total_events_synced": summary["total_events_synced"],
                "overall_status": summary["overall_status"]
            }
        except Exception as e:
            modules["sync_state"] = {"status": f"❌ Error: {str(e)}"}
        
        # OAuth Manager
        try:
            oauth_manager = OAuthManager()
            modules["oauth"] = {
                "status": "✅ Ready",
                "authenticated": oauth_manager.is_authenticated(),
                "pkce_support": True,
                "hybrid_callback": True
            }
        except Exception as e:
            modules["oauth"] = {"status": f"❌ Error: {str(e)}"}
        
        # Sync Manager
        try:
            sync_manager = get_sync_manager()
            stats = sync_manager.get_sync_stats()
            
            # Check if auto-sync is running - use correct attribute name
            auto_sync_running = False
            if hasattr(sync_manager, '_sync_thread') and sync_manager._sync_thread:
                try:
                    auto_sync_running = sync_manager._sync_thread.is_alive()
                except:
                    auto_sync_running = False
            
            modules["sync_manager"] = {
                "status": "✅ Running" if auto_sync_running else "⏸️ Stopped",
                "auto_sync_enabled": auto_sync_running,
                "total_syncs": stats.total_syncs,
                "successful_syncs": stats.successful_syncs,
                "failed_syncs": stats.failed_syncs,
                "total_events_synced": stats.total_events_synced,
                "debug_info": {
                    "has_thread": hasattr(sync_manager, '_sync_thread'),
                    "thread_alive": auto_sync_running,
                    "thread_object": str(sync_manager._sync_thread) if hasattr(sync_manager, '_sync_thread') else "None"
                }
            }
        except Exception as e:
            modules["sync_manager"] = {"status": f"❌ Error: {str(e)}"}
        
        return modules
    
    def get_live_data(self):
        """Get live data from ActivityWatch"""
        try:
            db = DatabaseModule()
            sync_manager = SyncStateManager()
            
            with db:
                info = db.get_database_info()
                buckets = db.get_buckets()
                
                bucket_data = []
                for bucket in buckets:
                    bucket_id = bucket['id']
                    events = db.get_events(bucket_id=bucket_id, limit=10)
                    unsynced = sync_manager.get_events_since_last_sync(bucket_id, events)
                    
                    bucket_data.append({
                        "id": bucket_id,
                        "total_events": len(events),
                        "unsynced_events": len(unsynced),
                        "recent_events": [
                            {
                                "timestamp": event["timestamp"],
                                "data": event["data"],
                                "id": event["id"]
                            }
                            for event in events[:3]
                        ]
                    })
                
                return {
                    "database_info": info,
                    "buckets": bucket_data,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def serve_api_sync_manager(self):
        """Serve Sync Manager status and statistics"""
        try:
            sync_manager = get_sync_manager()
            config = get_config()
            
            # Get sync statistics
            stats = sync_manager.get_sync_stats()
            
            # Check if auto-sync is running
            auto_sync_running = hasattr(sync_manager, '_sync_thread') and sync_manager._sync_thread and sync_manager._sync_thread.is_alive()
            
            result = {
                "sync_manager_status": "running" if auto_sync_running else "stopped",
                "auto_sync_enabled": auto_sync_running,
                "sync_interval": config.sync.sync_interval,
                "statistics": {
                    "total_syncs": stats.total_syncs,
                    "successful_syncs": stats.successful_syncs,
                    "failed_syncs": stats.failed_syncs,
                    "total_events_synced": stats.total_events_synced,
                    "last_sync_time": stats.last_sync_time.isoformat() if stats.last_sync_time else "Never",
                    "average_sync_duration": f"{stats.average_sync_duration:.2f}s"
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Send the response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            error_result = {"error": str(e), "timestamp": datetime.now().isoformat()}
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(error_result).encode())
    
    def serve_api_sync_start(self):
        """Start Sync Manager auto-sync"""
        try:
            sync_manager = get_sync_manager()
            config = get_config()
            
            # Start auto-sync if not already running
            if not hasattr(sync_manager, '_sync_thread') or not sync_manager._sync_thread or not sync_manager._sync_thread.is_alive():
                sync_manager.start_auto_sync()
                result = {
                    "status": "started",
                    "message": "Auto-sync started successfully",
                    "sync_interval": config.sync.sync_interval,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                result = {
                    "status": "already_running",
                    "message": "Auto-sync is already running",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Send the response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            error_result = {"error": str(e), "timestamp": datetime.now().isoformat()}
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(error_result).encode())
    
    def serve_api_sync_stop(self):
        """Stop Sync Manager auto-sync"""
        try:
            sync_manager = get_sync_manager()
            
            # Stop auto-sync if running
            if hasattr(sync_manager, '_sync_thread') and sync_manager._sync_thread and sync_manager._sync_thread.is_alive():
                sync_manager.stop_auto_sync()
                result = {
                    "status": "stopped",
                    "message": "Auto-sync stopped successfully",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                result = {
                    "status": "not_running",
                    "message": "Auto-sync is not running",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Send the response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            error_result = {"error": str(e), "timestamp": datetime.now().isoformat()}
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(error_result).encode())
    
    def serve_favicon(self):
        """Serve a simple favicon to prevent 404 errors"""
        self.send_response(200)
        self.send_header('Content-type', 'image/x-icon')
        self.end_headers()
        # Send a minimal 1x1 pixel favicon
        self.wfile.write(b'\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x01\x00\x20\x00\x68\x04\x00\x00\x16\x00\x00\x00\x28\x00\x00\x00\x10\x00\x00\x00\x20\x00\x00\x00\x01\x00\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
    
    def get_dashboard_html(self):
        """Generate the dashboard HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Samay Sync - Team Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .content {
            padding: 30px;
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .module-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            border-left: 4px solid #4facfe;
            transition: transform 0.2s ease;
        }
        
        .module-card:hover {
            transform: translateY(-2px);
        }
        
        .module-card h3 {
            color: #333;
            margin-bottom: 10px;
            font-size: 1.1em;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .status-indicator {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 500;
            margin-bottom: 8px;
        }
        
        .status-working {
            background: #d4edda;
            color: #155724;
        }
        
        .status-error {
            background: #f8d7da;
            color: #721c24;
        }
        
        .status-running {
            color: #27ae60;
            font-weight: bold;
        }
        
        .status-stopped {
            color: #e74c3c;
            font-weight: bold;
        }
        
        .module-details {
            font-size: 0.9em;
            color: #666;
            line-height: 1.4;
        }
        
        .module-details p {
            margin: 3px 0;
        }
        
        .data-section {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 20px;
            margin-top: 20px;
        }
        
        .data-section h3 {
            color: #333;
            margin-bottom: 15px;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4facfe, #00f2fe);
            transition: width 0.3s ease;
        }
        
        .refresh-btn {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            margin: 10px 0;
            transition: transform 0.2s ease;
        }
        
        .refresh-btn:hover {
            transform: scale(1.05);
        }
        
        .auto-refresh {
            color: #666;
            font-size: 0.9em;
            margin-top: 10px;
        }
        
        .event-item {
            background: white;
            padding: 10px;
            margin: 5px 0;
            border-radius: 8px;
            border-left: 3px solid #4facfe;
        }
        
        .event-timestamp {
            color: #666;
            font-size: 0.9em;
        }
        
        .event-data {
            color: #333;
            font-weight: 500;
        }
        
        .control-panel {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        }
        
        .control-panel h3 {
            color: #333;
            margin-bottom: 20px;
        }
        
        .button-group {
            display: flex;
            gap: 15px;
            justify-content: center;
            flex-wrap: wrap;
        }
        
        .action-btn {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 500;
            transition: all 0.3s ease;
            min-width: 120px;
        }
        
        .action-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(79, 172, 254, 0.4);
        }
        
        .action-btn:active {
            transform: translateY(0);
        }
        
        .action-btn.logout {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
        }
        
        .action-btn.logout:hover {
            box-shadow: 0 5px 15px rgba(255, 107, 107, 0.4);
        }
        
        .action-btn.login {
            background: linear-gradient(135deg, #51cf66 0%, #40c057 100%);
        }
        
        .action-btn.login:hover {
            box-shadow: 0 5px 15px rgba(81, 207, 102, 0.4);
        }
        
        .status-message {
            margin: 15px 0;
            padding: 10px 20px;
            border-radius: 10px;
            font-weight: 500;
            display: none;
        }
        
        .status-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .status-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .data-display {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin: 15px 0;
            border-left: 4px solid #4facfe;
            display: none;
        }
        
        .data-display h4 {
            color: #333;
            margin-bottom: 15px;
        }
        
        .data-item {
            background: #f8f9fa;
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            font-family: monospace;
            font-size: 0.9em;
        }
        
        .auth-status {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            margin-bottom: 15px;
        }
        
        .auth-authenticated {
            background: #d4edda;
            color: #155724;
        }
        
        .auth-not-authenticated {
            background: #f8d7da;
            color: #721c24;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Samay Sync Dashboard</h1>
            <p>Real-time progress and module status for the team</p>
        </div>
        
        <div class="content">
            <!-- Interactive Control Panel -->
            <div class="control-panel">
                <h3>🎮 Interactive Controls</h3>
                <div id="auth-status" class="auth-status auth-not-authenticated">
                    Not Authenticated
                </div>
                <div class="button-group">
                    <button id="login-btn" class="action-btn login" onclick="handleLogin()">
                        🔐 Login
                    </button>
                    <button id="logout-btn" class="action-btn logout" onclick="handleLogout()" style="display: none;">
                        🚪 Logout
                    </button>
                    <button class="action-btn" onclick="showDatabaseData()">
                        🗄️ Show Database Data
                    </button>
                    <button class="action-btn" onclick="showSyncState()">
                        🔄 Show Sync State Manager
                    </button>
                    <button class="action-btn" onclick="startAutoSync()">
                        ▶️ Start Auto Sync
                    </button>
                    <button class="action-btn" onclick="stopAutoSync()">
                        ⏹️ Stop Auto Sync
                    </button>
                </div>
                <div id="status-message" class="status-message"></div>
            </div>
            
            <div class="status-grid" id="modules-grid">
                <!-- Modules will be loaded here -->
            </div>
            
            <!-- Database Data Display -->
            <div id="database-display" class="data-display">
                <h4>🗄️ Database Data</h4>
                <div id="database-content"></div>
            </div>
            
            <!-- Sync State Display -->
            <div id="sync-state-display" class="data-display">
                <h4>🔄 Sync State Manager</h4>
                <div id="sync-state-content"></div>
            </div>
            
            <!-- Sync Manager Display -->
            <div id="sync-manager-display" class="data-display">
                <h4>🚀 Sync Manager</h4>
                <div id="sync-manager-content"></div>
            </div>
        </div>
    </div>

    <script>
        let refreshInterval;
        let isAuthenticated = false;
        
        // Authentication functions
        function handleLogin() {
            fetch('/api/login')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        showStatusMessage('✅ ' + data.message, 'success');
                        updateAuthStatus(true);
                        // Simulate OAuth popup
                        if (data.auth_url) {
                            showStatusMessage('🌐 OAuth URL: ' + data.auth_url.substring(0, 80) + '...', 'success');
                        }
                    } else {
                        showStatusMessage('ℹ️ ' + data.message, 'success');
                    }
                })
                .catch(error => {
                    showStatusMessage('❌ Login failed: ' + error.message, 'error');
                });
        }
        
        function handleLogout() {
            fetch('/api/logout')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        showStatusMessage('✅ ' + data.message, 'success');
                        updateAuthStatus(false);
                    } else {
                        showStatusMessage('ℹ️ ' + data.message, 'success');
                    }
                })
                .catch(error => {
                    showStatusMessage('❌ Logout failed: ' + error.message, 'error');
                });
        }
        
        function updateAuthStatus(authenticated) {
            isAuthenticated = authenticated;
            const authStatus = document.getElementById('auth-status');
            const loginBtn = document.getElementById('login-btn');
            const logoutBtn = document.getElementById('logout-btn');
            
            if (authenticated) {
                authStatus.textContent = '✅ Authenticated';
                authStatus.className = 'auth-status auth-authenticated';
                loginBtn.style.display = 'none';
                logoutBtn.style.display = 'inline-block';
            } else {
                authStatus.textContent = '❌ Not Authenticated';
                authStatus.className = 'auth-status auth-not-authenticated';
                loginBtn.style.display = 'inline-block';
                logoutBtn.style.display = 'none';
            }
        }
        
        function showStatusMessage(message, type) {
            const statusMessage = document.getElementById('status-message');
            statusMessage.textContent = message;
            statusMessage.className = 'status-message status-' + type;
            statusMessage.style.display = 'block';
            
            // Hide after 5 seconds
            setTimeout(() => {
                statusMessage.style.display = 'none';
            }, 5000);
        }
        
        function showDatabaseData() {
            fetch('/api/database')
                .then(response => response.json())
                .then(data => {
                    const display = document.getElementById('database-display');
                    const content = document.getElementById('database-content');
                    
                    let html = '<h5>📊 Database Information:</h5>';
                    html += '<div class="data-item">';
                    html += 'Total Events: ' + data.database_info.total_events + '<br>';
                    html += 'Total Buckets: ' + data.database_info.total_buckets + '<br>';
                    html += 'Connection Status: ' + data.database_info.connection_status + '<br>';
                    html += 'Tables: ' + data.database_info.tables.join(', ') + '<br>';
                    html += '</div>';
                    
                    html += '<h5>📦 Buckets & Events:</h5>';
                    data.buckets.forEach(bucket => {
                        html += '<div class="data-item">';
                        html += '<strong>' + bucket.id + '</strong><br>';
                        html += 'Total Events: ' + bucket.total_events + '<br>';
                        html += 'Recent Events:<br>';
                        
                        bucket.events.slice(0, 5).forEach(event => {
                            html += '&nbsp;&nbsp;• ' + new Date(event.timestamp).toLocaleString() + 
                                   ' - ' + JSON.stringify(event.data) + '<br>';
                        });
                        
                        if (bucket.events.length > 5) {
                            html += '&nbsp;&nbsp;... and ' + (bucket.events.length - 5) + ' more events<br>';
                        }
                        
                        html += '</div>';
                    });
                    
                    content.innerHTML = html;
                    display.style.display = 'block';
                    
                    // Scroll to the display
                    display.scrollIntoView({ behavior: 'smooth' });
                })
                .catch(error => {
                    showStatusMessage('❌ Failed to load database data: ' + error.message, 'error');
                });
        }
        
        function showSyncState() {
            fetch('/api/sync-state')
                .then(response => response.json())
                .then(data => {
                    const display = document.getElementById('sync-state-display');
                    const content = document.getElementById('sync-state-content');
                    
                    let html = '<h5>📊 Sync Summary:</h5>';
                    html += '<div class="data-item">';
                    html += 'Total Buckets: ' + data.summary.total_buckets + '<br>';
                    html += 'Total Events Synced: ' + data.summary.total_events_synced + '<br>';
                    html += 'Overall Status: ' + data.summary.overall_status + '<br>';
                    html += 'Successful Syncs: ' + data.summary.successful_syncs + '<br>';
                    html += 'Failed Syncs: ' + data.summary.failed_syncs + '<br>';
                    html += '</div>';
                    
                    html += '<h5>🔄 Individual Bucket States:</h5>';
                    Object.entries(data.sync_states).forEach(([bucketId, state]) => {
                        html += '<div class="data-item">';
                        html += '<strong>' + bucketId + '</strong><br>';
                        html += 'Last Sync: ' + (state.last_sync_timestamp || 'Never') + '<br>';
                        html += 'Last Event ID: ' + (state.last_sync_event_id || 'None') + '<br>';
                        html += 'Status: ' + state.last_sync_status + '<br>';
                        html += 'Events Synced: ' + state.total_events_synced + '<br>';
                        if (state.last_error) {
                            html += 'Last Error: ' + state.last_error + '<br>';
                        }
                        html += '</div>';
                    });
                    
                    content.innerHTML = html;
                    display.style.display = 'block';
                    
                    // Scroll to the display
                    display.scrollIntoView({ behavior: 'smooth' });
                })
                .catch(error => {
                    showStatusMessage('❌ Failed to load sync state: ' + error.message, 'error');
                });
        }
        
        function showSyncManager() {
            fetch('/api/sync-manager')
                .then(response => response.json())
                .then(data => {
                    const display = document.getElementById('sync-manager-display');
                    const content = document.getElementById('sync-manager-content');
                    
                    let html = '<h5>🚀 Sync Manager Status:</h5>';
                    html += '<div class="data-item">';
                    html += 'Status: <span class="status-' + data.sync_manager_status + '">' + data.sync_manager_status.toUpperCase() + '</span><br>';
                    html += 'Auto Sync: ' + (data.auto_sync_enabled ? '✅ Enabled' : '❌ Disabled') + '<br>';
                    html += 'Sync Interval: ' + data.sync_interval + ' seconds<br>';
                    html += '</div>';
                    
                    html += '<h5>📊 Sync Statistics:</h5>';
                    html += '<div class="data-item">';
                    html += 'Total Syncs: ' + data.statistics.total_syncs + '<br>';
                    html += 'Successful Syncs: ' + data.statistics.successful_syncs + '<br>';
                    html += 'Failed Syncs: ' + data.statistics.failed_syncs + '<br>';
                    html += 'Total Events Synced: ' + data.statistics.total_events_synced + '<br>';
                    html += 'Last Sync Time: ' + (data.statistics.last_sync_time || 'Never') + '<br>';
                    html += 'Average Duration: ' + data.statistics.average_sync_duration + 's<br>';
                    html += '</div>';
                    
                    content.innerHTML = html;
                    display.style.display = 'block';
                    
                    // Scroll to the display
                    display.scrollIntoView({ behavior: 'smooth' });
                })
                .catch(error => {
                    showStatusMessage('❌ Failed to load sync manager: ' + error.message, 'error');
                });
        }
        
        function startAutoSync() {
            fetch('/api/sync-start')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'started') {
                        showStatusMessage('✅ Auto-sync started! Syncing every ' + data.sync_interval + ' seconds', 'success');
                        // Show sync manager stats after starting
                        setTimeout(() => showSyncManagerStats(), 1000);
                    } else if (data.status === 'already_running') {
                        showStatusMessage('ℹ️ ' + data.message, 'info');
                    } else {
                        showStatusMessage('❌ Failed to start auto-sync: ' + data.message, 'error');
                    }
                })
                .catch(error => {
                    showStatusMessage('❌ Failed to start auto-sync: ' + error.message, 'error');
                });
        }
        
        function stopAutoSync() {
            fetch('/api/sync-stop')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'stopped') {
                        showStatusMessage('⏹️ Auto-sync stopped successfully', 'success');
                        // Show sync manager stats after stopping
                        setTimeout(() => showSyncManagerStats(), 1000);
                    } else if (data.status === 'not_running') {
                        showStatusMessage('ℹ️ ' + data.message, 'info');
                    } else {
                        showStatusMessage('❌ Failed to stop auto-sync: ' + data.message, 'error');
                    }
                })
                .catch(error => {
                    showStatusMessage('❌ Failed to stop auto-sync: ' + error.message, 'error');
                });
        }
        
        function showSyncManagerStats() {
            fetch('/api/sync-manager')
                .then(response => response.json())
                .then(data => {
                    const display = document.getElementById('sync-manager-display');
                    const content = document.getElementById('sync-manager-content');
                    
                    let html = '<h5>🚀 Sync Manager Status:</h5>';
                    html += '<div class="data-item">';
                    html += 'Status: <span class="status-' + data.sync_manager_status + '">' + data.sync_manager_status.toUpperCase() + '</span><br>';
                    html += 'Auto Sync: ' + (data.auto_sync_enabled ? '✅ Enabled' : '❌ Disabled') + '<br>';
                    html += 'Sync Interval: ' + data.sync_interval + ' seconds<br>';
                    html += '</div>';
                    
                    html += '<h5>📊 Sync Statistics:</h5>';
                    html += '<div class="data-item">';
                    html += 'Total Syncs: ' + data.statistics.total_syncs + '<br>';
                    html += 'Successful Syncs: ' + data.statistics.successful_syncs + '<br>';
                    html += 'Failed Syncs: ' + data.statistics.failed_syncs + '<br>';
                    html += 'Total Events Synced: ' + data.statistics.total_events_synced + '<br>';
                    html += 'Last Sync Time: ' + (data.statistics.last_sync_time || 'Never') + '<br>';
                    html += 'Average Duration: ' + data.statistics.average_sync_duration + '<br>';
                    html += '</div>';
                    
                    content.innerHTML = html;
                    display.style.display = 'block';
                    
                    // Scroll to the display
                    display.scrollIntoView({ behavior: 'smooth' });
                })
                .catch(error => {
                    showStatusMessage('❌ Failed to load sync manager stats: ' + error.message, 'error');
                });
        }
        
        function refreshModules() {
            console.log('Manual refresh triggered');
            loadModules();
            showStatusMessage('🔄 Status refreshed', 'info');
        }
        
        function loadModules() {
            fetch('/api/modules')
                .then(response => response.json())
                .then(data => {
                    console.log('Modules data received:', data);
                    const grid = document.getElementById('modules-grid');
                    grid.innerHTML = '';
                    
                    Object.entries(data).forEach(([name, module]) => {
                        console.log('Processing module:', name, module);
                        const card = document.createElement('div');
                        card.className = 'module-card';
                        
                        // Determine status class and text based on status content
                        let statusClass, statusText;
                        if (module.status.includes('✅')) {
                            statusClass = 'status-working';
                            statusText = 'Working';
                        } else if (module.status.includes('⏸️')) {
                            statusClass = 'status-stopped';
                            statusText = 'Stopped';
                        } else if (module.status.includes('❌')) {
                            statusClass = 'status-error';
                            statusText = 'Error';
                        } else {
                            statusClass = 'status-working';
                            statusText = module.status; // Use the actual status text
                        }
                        
                        card.innerHTML = `
                            <h3>${getModuleIcon(name)} ${getModuleName(name)}</h3>
                            <div class="status-indicator ${statusClass}">${statusText}</div>
                            <div class="module-details">${getModuleDetails(module)}</div>
                        `;
                        
                        grid.appendChild(card);
                    });
                })
                .catch(error => {
                    console.error('Error loading modules:', error);
                });
        }
        
        
        function getModuleIcon(name) {
            const icons = {
                'config': '📋',
                'database': '🗄️',
                'sync_state': '🔄',
                'sync_manager': '🚀',
                'oauth': '🔐'
            };
            return icons[name] || '📦';
        }
        
        function getModuleName(name) {
            const names = {
                'config': 'Configuration Module',
                'database': 'Database Module',
                'sync_state': 'Sync State Manager',
                'sync_manager': 'Sync Manager',
                'oauth': 'OAuth Manager'
            };
            return names[name] || name;
        }
        
        function getModuleDetails(module) {
            let details = '';
            
            if (module.database_path) {
                details += '<p><strong>Database:</strong> ' + module.database_path.split('/').pop() + '</p>';
            }
            
            if (module.total_events !== undefined) {
                details += '<p><strong>Events:</strong> ' + module.total_events + '</p>';
            }
            
            if (module.total_buckets !== undefined) {
                details += '<p><strong>Buckets:</strong> ' + module.total_buckets + '</p>';
            }
            
            if (module.authenticated !== undefined) {
                details += '<p><strong>Auth:</strong> ' + (module.authenticated ? 'Yes' : 'No') + '</p>';
            }
            
            if (module.overall_status) {
                details += '<p><strong>Status:</strong> ' + module.overall_status + '</p>';
            }
            
            if (module.sync_interval) {
                details += '<p><strong>Interval:</strong> ' + module.sync_interval + 's</p>';
            }
            
            return details;
        }
        
        function refreshData() {
            loadModules();
        }
        
        // Initialize
        loadModules();
        checkAuthStatus();
        
        // Auto-refresh every 5 seconds
        refreshInterval = setInterval(refreshData, 5000);
        
        function checkAuthStatus() {
            fetch('/api/modules')
                .then(response => response.json())
                .then(data => {
                    if (data.oauth && data.oauth.authenticated) {
                        updateAuthStatus(true);
                    } else {
                        updateAuthStatus(false);
                    }
                })
                .catch(error => {
                    console.error('Error checking auth status:', error);
                    updateAuthStatus(false);
                });
        }
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (refreshInterval) {
                clearInterval(refreshInterval);
            }
        });
    </script>
</body>
</html>
        """
    
    def log_message(self, format, *args):
        """Override to reduce log noise"""
        pass


def main():
    """Start the web dashboard server"""
    print("🚀 Starting Samay Sync Web Dashboard...")
    print("=" * 50)
    
    # Set up environment variables for demo
    os.environ.setdefault("SAMAY_OAUTH_CLIENT_ID", "demo_client")
    os.environ.setdefault("SAMAY_OAUTH_CLIENT_SECRET", "demo_secret")
    
    port = 8080
    server_address = ('', port)
    
    try:
        httpd = HTTPServer(server_address, DashboardHandler)
        print(f"✅ Dashboard running at: http://localhost:{port}")
        print(f"📊 Real-time module status and ActivityWatch data")
        print(f"🔄 Auto-refreshing every 5 seconds")
        print(f"⏹️  Press Ctrl+C to stop")
        print()
        
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped")
        httpd.shutdown()
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")


if __name__ == "__main__":
    main()
