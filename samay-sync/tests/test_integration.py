#!/usr/bin/env python3
"""
Test script to demonstrate the dashboard login/logout integration with run.sh/stop.sh
"""

import time
import subprocess
import os

# Try to import requests, skip test if not available
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

def test_dashboard_integration():
    """Test the dashboard login/logout integration"""
    
    if not REQUESTS_AVAILABLE:
        print("⚠️ Skipping integration test - requests library not available")
        print("💡 Install requests: pip install requests")
        return
    
    # Start dashboard in background
    print("🚀 Starting dashboard...")
    dashboard_process = subprocess.Popen([
        "python3", "demo/web_dashboard.py"
    ], env={
        **os.environ,
        "SAMAY_OAUTH_CLIENT_ID": "demo_client",
        "SAMAY_OAUTH_CLIENT_SECRET": "demo_secret"
    })
    
    # Wait for dashboard to start
    time.sleep(3)
    
    try:
        # Test logout (to ensure clean state)
        print("🛑 Testing logout...")
        response = requests.get("http://localhost:8080/api/logout")
        print(f"Logout response: {response.json()}")
        
        # Test login (should trigger run.sh)
        print("🚀 Testing login...")
        response = requests.get("http://localhost:8080/api/login")
        print(f"Login response: {response.json()}")
        
        # Wait a bit to see if ActivityWatch processes start
        print("⏳ Waiting for ActivityWatch services to start...")
        time.sleep(5)
        
        # Check if ActivityWatch processes are running
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        aw_processes = [line for line in result.stdout.split('\n') if 'aw-server' in line or 'aw-watcher' in line]
        
        if aw_processes:
            print("✅ ActivityWatch services are running!")
            for process in aw_processes:
                print(f"  - {process.strip()}")
        else:
            print("⚠️ No ActivityWatch processes found")
        
        # Test logout again (should trigger stop.sh)
        print("🛑 Testing logout again...")
        response = requests.get("http://localhost:8080/api/logout")
        print(f"Logout response: {response.json()}")
        
        # Wait a bit to see if processes stop
        print("⏳ Waiting for ActivityWatch services to stop...")
        time.sleep(3)
        
        # Check if processes stopped
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        aw_processes = [line for line in result.stdout.split('\n') if 'aw-server' in line or 'aw-watcher' in line]
        
        if aw_processes:
            print("⚠️ Some ActivityWatch processes still running:")
            for process in aw_processes:
                print(f"  - {process.strip()}")
        else:
            print("✅ All ActivityWatch services stopped!")
            
    finally:
        # Stop dashboard
        print("🛑 Stopping dashboard...")
        dashboard_process.terminate()
        dashboard_process.wait()
        print("✅ Dashboard stopped")

if __name__ == "__main__":
    test_dashboard_integration()
