#!/usr/bin/env python3
"""
Example script demonstrating how to use the ActivityWatch URL scheme functionality.

This script shows how to:
1. Send a token via URL scheme to the ActivityWatch server
2. Check if the token was stored successfully
3. Test the API endpoints

Usage:
    python url_scheme_example.py
"""

import requests
import json
import time

# ActivityWatch server configuration
SERVER_URL = "http://localhost:5600"
API_BASE = f"{SERVER_URL}/api/0"

def test_url_scheme_token():
    """Test the URL scheme token and URL functionality."""
    
    # Example token and URL (replace with your actual values)
    test_token = "your-auth-token-here"
    test_url = "http://localhost:4000/activities"
    
    # Create URL scheme format with both token and URL
    url_scheme = f"activitywatch://token?token={test_token}&url={test_url}"
    
    print(f"Testing URL scheme: {url_scheme}")
    
    # Send URL scheme request
    try:
        response = requests.post(
            f"{API_BASE}/url-scheme",
            json={"url": url_scheme},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ URL scheme token and URL stored successfully!")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Failed to store token and URL: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False
    
    return True

def test_token_endpoints():
    """Test the token management endpoints."""
    
    print("\n--- Testing Token Endpoints ---")
    
    # Test getting token
    try:
        response = requests.get(f"{API_BASE}/token")
        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ Current token: {token_data.get('token', 'None')}")
        else:
            print(f"❌ Failed to get token: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting token: {e}")
    
    # Test storing token and URL directly
    test_token = "direct-storage-test-token"
    test_url = "http://localhost:4000/activities"
    try:
        response = requests.post(
            f"{API_BASE}/token",
            json={"token": test_token, "url": test_url},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            print(f"✅ Token and URL stored directly: {response.json()}")
        else:
            print(f"❌ Failed to store token and URL directly: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error storing token and URL: {e}")
    
    # Test deleting token
    try:
        response = requests.delete(f"{API_BASE}/token")
        if response.status_code == 200:
            print(f"✅ Token deleted: {response.json()}")
        else:
            print(f"❌ Failed to delete token: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error deleting token: {e}")

def test_server_info():
    """Test if the ActivityWatch server is running."""
    
    print("--- Testing Server Connection ---")
    
    try:
        response = requests.get(f"{API_BASE}/info")
        if response.status_code == 200:
            info = response.json()
            print(f"✅ Server is running!")
            print(f"   Hostname: {info.get('hostname')}")
            print(f"   Version: {info.get('version')}")
            print(f"   Device ID: {info.get('device_id')}")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to ActivityWatch server at {SERVER_URL}")
        print(f"   Make sure the server is running: aw-server")
        print(f"   Error: {e}")
        return False

def main():
    """Main function to run all tests."""
    
    print("ActivityWatch URL Scheme Test")
    print("=" * 40)
    
    # Test server connection first
    if not test_server_info():
        print("\n❌ Cannot proceed without server connection")
        return
    
    # Test URL scheme functionality
    print("\n--- Testing URL Scheme ---")
    test_url_scheme_token()
    
    # Test token endpoints
    test_token_endpoints()
    
    print("\n" + "=" * 40)
    print("Test completed!")
    print("\nTo use this in a real scenario:")
    print("1. Replace 'your-auth-token-here' with your actual token")
    print("2. Replace the URL with your actual backend API endpoint")
    print("3. Use the URL scheme: activitywatch://token?token=YOUR_TOKEN&url=YOUR_API_URL")
    print("4. The scheduler will automatically use this token and URL every 10 minutes")
    print("5. Events will be sent to the configured API endpoint")

if __name__ == "__main__":
    main()
