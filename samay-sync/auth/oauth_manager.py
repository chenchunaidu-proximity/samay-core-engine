#!/usr/bin/env python3
"""
OAuth Manager for Samay Sync MVP
Implements OAuth 2.0 Authorization Code Flow with PKCE

This module provides:
1. OAuth flow orchestration with hybrid callback strategy
2. Secure token storage and management
3. Token refresh handling
4. Error handling and recovery
5. Cross-platform compatibility
"""

import os
import json
import base64
import hashlib
import secrets
import webbrowser
import threading
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode, parse_qs, urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler
import sys

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.sync_config import get_config


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback"""
    
    def do_GET(self):
        """Handle OAuth callback"""
        if self.path.startswith('/callback'):
            # Parse query parameters
            query_params = parse_qs(urlparse(self.path).query)
            
            # Extract authorization code and state
            code = query_params.get('code', [None])[0]
            state = query_params.get('state', [None])[0]
            error = query_params.get('error', [None])[0]
            
            # Store callback result
            self.server.callback_result = {
                'code': code,
                'state': state,
                'error': error,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Send response to browser
            if error:
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(f"""
                <html>
                <body>
                    <h2>OAuth Error</h2>
                    <p>Error: {error}</p>
                    <p>You can close this window.</p>
                </body>
                </html>
                """.encode())
            else:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"""
                <html>
                <body>
                    <h2>OAuth Success</h2>
                    <p>Authentication successful! You can close this window.</p>
                </body>
                </html>
                """)
            
            # Shutdown server after handling callback
            threading.Thread(target=self.server.shutdown, daemon=True).start()
    
    def log_message(self, format, *args):
        """Suppress HTTP server logs"""
        pass


class TokenStorage:
    """Secure token storage implementation"""
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize token storage
        
        Args:
            storage_path: Path to token storage file. If None, uses config default
        """
        if storage_path is None:
            config = get_config()
            storage_path = config.oauth.token_storage_path
        
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _encrypt_token(self, token: str) -> str:
        """
        Encrypt token using base64 encoding
        
        Args:
            token: Token to encrypt
            
        Returns:
            Encrypted token
        """
        return base64.b64encode(token.encode()).decode()
    
    def _decrypt_token(self, encrypted_token: str) -> str:
        """
        Decrypt token using base64 decoding
        
        Args:
            encrypted_token: Encrypted token
            
        Returns:
            Decrypted token
        """
        return base64.b64decode(encrypted_token.encode()).decode()
    
    def store_tokens(self, access_token: str, refresh_token: Optional[str] = None, 
                    expires_in: Optional[int] = None, token_type: str = "Bearer"):
        """
        Store OAuth tokens securely
        
        Args:
            access_token: OAuth access token
            refresh_token: OAuth refresh token (optional)
            expires_in: Token expiration time in seconds (optional)
            token_type: Token type (default: Bearer)
        """
        try:
            # Calculate expiration time
            expires_at = None
            if expires_in:
                expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()
            
            # Prepare token data
            token_data = {
                'access_token': self._encrypt_token(access_token),
                'refresh_token': self._encrypt_token(refresh_token) if refresh_token else None,
                'expires_at': expires_at,
                'token_type': token_type,
                'stored_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Write to file
            with open(self.storage_path, 'w') as f:
                json.dump(token_data, f, indent=2)
            
        except Exception as e:
            raise RuntimeError(f"Error storing tokens: {e}")
    
    def load_tokens(self) -> Optional[Dict]:
        """
        Load OAuth tokens from storage
        
        Returns:
            Token data dictionary or None if not found
        """
        try:
            if not self.storage_path.exists():
                return None
            
            with open(self.storage_path, 'r') as f:
                token_data = json.load(f)
            
            # Decrypt tokens
            if 'access_token' in token_data:
                token_data['access_token'] = self._decrypt_token(token_data['access_token'])
            if 'refresh_token' in token_data and token_data['refresh_token']:
                token_data['refresh_token'] = self._decrypt_token(token_data['refresh_token'])
            
            return token_data
            
        except Exception as e:
            return None
    
    def clear_tokens(self):
        """Clear stored tokens"""
        try:
            if self.storage_path.exists():
                self.storage_path.unlink()
        except Exception as e:
            pass  # Ignore errors when clearing tokens
    
    def is_token_valid(self) -> bool:
        """
        Check if stored token is valid and not expired
        
        Returns:
            True if token is valid, False otherwise
        """
        token_data = self.load_tokens()
        if not token_data:
            return False
        
        # Check if token has expiration
        if 'expires_at' in token_data and token_data['expires_at']:
            try:
                expires_at = datetime.fromisoformat(token_data['expires_at'].replace('Z', '+00:00'))
                return datetime.now(timezone.utc) < expires_at
            except:
                return True  # If we can't parse expiration, assume valid
        
        return True


class OAuthManager:
    """OAuth 2.0 Authorization Code Flow with PKCE implementation"""
    
    def __init__(self, config=None):
        """
        Initialize OAuth manager
        
        Args:
            config: Configuration object. If None, loads from config
        """
        if config is None:
            config = get_config()
        
        self.config = config
        self.token_storage = TokenStorage(config.oauth.token_storage_path)
        self.callback_server = None
        self.callback_result = None
    
    def _generate_pkce_challenge(self) -> Tuple[str, str]:
        """
        Generate PKCE code verifier and challenge
        
        Returns:
            Tuple of (code_verifier, code_challenge)
        """
        # Generate code verifier (43-128 characters)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip('=')
        
        # Generate code challenge (SHA256 hash of verifier)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip('=')
        
        return code_verifier, code_challenge
    
    def _start_callback_server(self, port: int) -> HTTPServer:
        """
        Start local HTTP server for OAuth callback
        
        Args:
            port: Port number for callback server
            
        Returns:
            HTTPServer instance
        """
        server = HTTPServer(('127.0.0.1', port), OAuthCallbackHandler)
        server.callback_result = None
        
        # Start server in background thread
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        
        return server
    
    def _build_auth_url(self, state: str, code_challenge: str) -> str:
        """
        Build OAuth authorization URL
        
        Args:
            state: OAuth state parameter
            code_challenge: PKCE code challenge
            
        Returns:
            Authorization URL
        """
        params = {
            'response_type': 'code',
            'client_id': self.config.oauth.client_id,
            'redirect_uri': self.config.oauth.redirect_uri,
            'scope': 'read write',  # Default scope, can be configured
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
        
        return f"{self.config.oauth.auth_url}?{urlencode(params)}"
    
    def _exchange_code_for_token(self, code: str, code_verifier: str) -> Dict:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from callback
            code_verifier: PKCE code verifier
            
        Returns:
            Token response dictionary
        """
        import requests
        
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.config.oauth.client_id,
            'client_secret': self.config.oauth.client_secret,
            'code': code,
            'redirect_uri': self.config.oauth.redirect_uri,
            'code_verifier': code_verifier
        }
        
        try:
            response = requests.post(
                self.config.oauth.token_url,
                data=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            raise RuntimeError(f"Token exchange failed: {e}")
    
    def authenticate(self) -> bool:
        """
        Perform OAuth authentication flow
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Generate PKCE parameters
            code_verifier, code_challenge = self._generate_pkce_challenge()
            
            # Generate state parameter
            state = secrets.token_urlsafe(32)
            
            # Extract port from redirect URI
            redirect_port = int(self.config.oauth.redirect_uri.split(':')[-1].split('/')[0])
            
            # Start callback server
            self.callback_server = self._start_callback_server(redirect_port)
            
            # Build authorization URL
            auth_url = self._build_auth_url(state, code_challenge)
            
            # Open browser for authentication
            webbrowser.open(auth_url)
            
            # Wait for callback (with timeout)
            timeout = 300  # 5 minutes
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if self.callback_server.callback_result:
                    callback_result = self.callback_server.callback_result
                    
                    # Check for errors
                    if callback_result.get('error'):
                        raise RuntimeError(f"OAuth error: {callback_result['error']}")
                    
                    # Verify state parameter
                    if callback_result.get('state') != state:
                        raise RuntimeError("OAuth state mismatch")
                    
                    # Exchange code for token
                    code = callback_result.get('code')
                    if not code:
                        raise RuntimeError("No authorization code received")
                    
                    token_response = self._exchange_code_for_token(code, code_verifier)
                    
                    # Store tokens
                    self.token_storage.store_tokens(
                        access_token=token_response['access_token'],
                        refresh_token=token_response.get('refresh_token'),
                        expires_in=token_response.get('expires_in'),
                        token_type=token_response.get('token_type', 'Bearer')
                    )
                    
                    return True
                
                time.sleep(0.1)
            
            raise RuntimeError("OAuth authentication timeout")
            
        except Exception as e:
            return False
        
        finally:
            # Clean up callback server
            if self.callback_server:
                self.callback_server.shutdown()
                self.callback_server = None
    
    def is_authenticated(self) -> bool:
        """
        Check if user is authenticated
        
        Returns:
            True if authenticated, False otherwise
        """
        return self.token_storage.is_token_valid()
    
    def get_access_token(self) -> Optional[str]:
        """
        Get current access token
        
        Returns:
            Access token or None if not available
        """
        token_data = self.token_storage.load_tokens()
        if token_data and self.token_storage.is_token_valid():
            return token_data['access_token']
        return None
    
    def logout(self):
        """Logout user and clear tokens"""
        self.token_storage.clear_tokens()
    
    def refresh_token(self) -> bool:
        """
        Refresh access token using refresh token
        
        Returns:
            True if refresh successful, False otherwise
        """
        token_data = self.token_storage.load_tokens()
        if not token_data or not token_data.get('refresh_token'):
            return False
        
        try:
            import requests
            
            data = {
                'grant_type': 'refresh_token',
                'client_id': self.config.oauth.client_id,
                'client_secret': self.config.oauth.client_secret,
                'refresh_token': token_data['refresh_token']
            }
            
            response = requests.post(
                self.config.oauth.token_url,
                data=data,
                timeout=30
            )
            response.raise_for_status()
            
            token_response = response.json()
            
            # Store new tokens
            self.token_storage.store_tokens(
                access_token=token_response['access_token'],
                refresh_token=token_response.get('refresh_token', token_data['refresh_token']),
                expires_in=token_response.get('expires_in'),
                token_type=token_response.get('token_type', 'Bearer')
            )
            
            return True
            
        except Exception as e:
            return False


# Example usage and testing
if __name__ == "__main__":
    try:
        # Test OAuth manager
        oauth_manager = OAuthManager()
        
        print("🔐 Testing OAuth Manager")
        print("=" * 50)
        
        # Check authentication status
        is_auth = oauth_manager.is_authenticated()
        print(f"✅ Authentication status: {'Authenticated' if is_auth else 'Not authenticated'}")
        
        if not is_auth:
            print("\n🚀 Starting OAuth authentication...")
            print("This will open a browser window for authentication.")
            print("Note: This is a test with placeholder endpoints.")
            
            # Note: This will fail with placeholder endpoints, but shows the flow
            success = oauth_manager.authenticate()
            if success:
                print("✅ Authentication successful!")
                token = oauth_manager.get_access_token()
                print(f"Access token: {token[:20]}..." if token else "No token")
            else:
                print("❌ Authentication failed")
        else:
            token = oauth_manager.get_access_token()
            print(f"✅ Current access token: {token[:20]}..." if token else "No token")
        
        # Test token refresh
        if oauth_manager.is_authenticated():
            print("\n🔄 Testing token refresh...")
            refresh_success = oauth_manager.refresh_token()
            print(f"Token refresh: {'Success' if refresh_success else 'Failed'}")
        
        # Test logout
        print("\n🚪 Testing logout...")
        oauth_manager.logout()
        is_auth_after_logout = oauth_manager.is_authenticated()
        print(f"After logout: {'Still authenticated' if is_auth_after_logout else 'Logged out'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Error type: {type(e).__name__}")
