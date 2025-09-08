#!/usr/bin/env python3
"""
Test suite for OAuth Manager
Tests OAuth flow, token storage, and authentication functionality
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import json
import base64
from datetime import datetime, timezone, timedelta
import sys
from pathlib import Path

# Add the auth module to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from auth.oauth_manager import OAuthManager, TokenStorage, OAuthCallbackHandler


class TestTokenStorage(unittest.TestCase):
    """Test TokenStorage functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary token file for testing
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
        
        # Initialize token storage with temp file
        self.token_storage = TokenStorage(self.temp_file.name)
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_encrypt_decrypt_token(self):
        """Test token encryption and decryption"""
        test_token = "test_access_token_12345"
        
        # Encrypt token
        encrypted = self.token_storage._encrypt_token(test_token)
        self.assertIsInstance(encrypted, str)
        self.assertNotEqual(encrypted, test_token)
        
        # Decrypt token
        decrypted = self.token_storage._decrypt_token(encrypted)
        self.assertEqual(decrypted, test_token)
    
    def test_store_and_load_tokens(self):
        """Test storing and loading tokens"""
        access_token = "test_access_token"
        refresh_token = "test_refresh_token"
        expires_in = 3600
        
        # Store tokens
        self.token_storage.store_tokens(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            token_type="Bearer"
        )
        
        # Load tokens
        loaded_tokens = self.token_storage.load_tokens()
        self.assertIsNotNone(loaded_tokens)
        self.assertEqual(loaded_tokens['access_token'], access_token)
        self.assertEqual(loaded_tokens['refresh_token'], refresh_token)
        self.assertEqual(loaded_tokens['token_type'], "Bearer")
        self.assertIsNotNone(loaded_tokens['expires_at'])
        self.assertIsNotNone(loaded_tokens['stored_at'])
    
    def test_store_tokens_without_refresh(self):
        """Test storing tokens without refresh token"""
        access_token = "test_access_token"
        
        # Store tokens without refresh token
        self.token_storage.store_tokens(
            access_token=access_token,
            expires_in=3600
        )
        
        # Load tokens
        loaded_tokens = self.token_storage.load_tokens()
        self.assertIsNotNone(loaded_tokens)
        self.assertEqual(loaded_tokens['access_token'], access_token)
        self.assertIsNone(loaded_tokens['refresh_token'])
    
    def test_token_validation_valid(self):
        """Test token validation with valid token"""
        # Store token with future expiration
        self.token_storage.store_tokens(
            access_token="test_token",
            expires_in=3600  # 1 hour from now
        )
        
        # Check validation
        is_valid = self.token_storage.is_token_valid()
        self.assertTrue(is_valid)
    
    def test_token_validation_expired(self):
        """Test token validation with expired token"""
        # Store token with past expiration
        self.token_storage.store_tokens(
            access_token="test_token",
            expires_in=-3600  # 1 hour ago
        )
        
        # Check validation
        is_valid = self.token_storage.is_token_valid()
        self.assertFalse(is_valid)
    
    def test_token_validation_no_expiration(self):
        """Test token validation without expiration"""
        # Store token without expiration
        self.token_storage.store_tokens(
            access_token="test_token"
        )
        
        # Check validation (should be valid if no expiration)
        is_valid = self.token_storage.is_token_valid()
        self.assertTrue(is_valid)
    
    def test_clear_tokens(self):
        """Test clearing stored tokens"""
        # Store tokens
        self.token_storage.store_tokens(
            access_token="test_token",
            expires_in=3600
        )
        
        # Verify tokens exist
        self.assertIsNotNone(self.token_storage.load_tokens())
        
        # Clear tokens
        self.token_storage.clear_tokens()
        
        # Verify tokens are cleared
        self.assertIsNone(self.token_storage.load_tokens())
    
    def test_load_tokens_file_not_exists(self):
        """Test loading tokens when file doesn't exist"""
        # Clear tokens first
        self.token_storage.clear_tokens()
        
        # Try to load tokens
        loaded_tokens = self.token_storage.load_tokens()
        self.assertIsNone(loaded_tokens)


class TestOAuthManager(unittest.TestCase):
    """Test OAuthManager functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary token file for testing
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
        
        # Mock configuration
        self.mock_config = MagicMock()
        self.mock_config.oauth.client_id = "test_client_id"
        self.mock_config.oauth.client_secret = "test_client_secret"
        self.mock_config.oauth.redirect_uri = "http://127.0.0.1:54783/callback"
        self.mock_config.oauth.auth_url = "https://auth.example.com/oauth/authorize"
        self.mock_config.oauth.token_url = "https://auth.example.com/oauth/token"
        self.mock_config.oauth.token_storage_path = self.temp_file.name
        
        # Initialize OAuth manager with mock config
        self.oauth_manager = OAuthManager(self.mock_config)
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_pkce_generation(self):
        """Test PKCE code verifier and challenge generation"""
        code_verifier, code_challenge = self.oauth_manager._generate_pkce_challenge()
        
        # Check code verifier
        self.assertIsInstance(code_verifier, str)
        self.assertGreaterEqual(len(code_verifier), 43)
        self.assertLessEqual(len(code_verifier), 128)
        
        # Check code challenge
        self.assertIsInstance(code_challenge, str)
        self.assertEqual(len(code_challenge), 43)  # Base64 URL-safe without padding
        
        # Verify challenge is SHA256 hash of verifier
        import hashlib
        expected_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip('=')
        self.assertEqual(code_challenge, expected_challenge)
    
    def test_build_auth_url(self):
        """Test building OAuth authorization URL"""
        state = "test_state_123"
        code_challenge = "test_challenge_456"
        
        auth_url = self.oauth_manager._build_auth_url(state, code_challenge)
        
        # Check URL structure
        self.assertTrue(auth_url.startswith("https://auth.example.com/oauth/authorize"))
        self.assertIn("response_type=code", auth_url)
        self.assertIn("client_id=test_client_id", auth_url)
        self.assertIn("redirect_uri=http%3A%2F%2F127.0.0.1%3A54783%2Fcallback", auth_url)
        self.assertIn("scope=read+write", auth_url)
        self.assertIn(f"state={state}", auth_url)
        self.assertIn(f"code_challenge={code_challenge}", auth_url)
        self.assertIn("code_challenge_method=S256", auth_url)
    
    def test_is_authenticated_not_authenticated(self):
        """Test authentication status when not authenticated"""
        is_auth = self.oauth_manager.is_authenticated()
        self.assertFalse(is_auth)
    
    def test_is_authenticated_authenticated(self):
        """Test authentication status when authenticated"""
        # Store valid tokens
        self.oauth_manager.token_storage.store_tokens(
            access_token="test_token",
            expires_in=3600
        )
        
        is_auth = self.oauth_manager.is_authenticated()
        self.assertTrue(is_auth)
    
    def test_get_access_token_not_authenticated(self):
        """Test getting access token when not authenticated"""
        token = self.oauth_manager.get_access_token()
        self.assertIsNone(token)
    
    def test_get_access_token_authenticated(self):
        """Test getting access token when authenticated"""
        # Store valid tokens
        self.oauth_manager.token_storage.store_tokens(
            access_token="test_token",
            expires_in=3600
        )
        
        token = self.oauth_manager.get_access_token()
        self.assertEqual(token, "test_token")
    
    def test_logout(self):
        """Test logout functionality"""
        # Store tokens first
        self.oauth_manager.token_storage.store_tokens(
            access_token="test_token",
            expires_in=3600
        )
        
        # Verify authenticated
        self.assertTrue(self.oauth_manager.is_authenticated())
        
        # Logout
        self.oauth_manager.logout()
        
        # Verify not authenticated
        self.assertFalse(self.oauth_manager.is_authenticated())
        self.assertIsNone(self.oauth_manager.get_access_token())
    
    def test_exchange_code_for_token(self):
        """Test exchanging authorization code for access token"""
        # Skip if requests not available
        try:
            import requests
        except ImportError:
            self.skipTest("requests module not available")
        
        with patch('requests.post') as mock_post:
            # Mock successful token response
            mock_response = MagicMock()
            mock_response.json.return_value = {
                'access_token': 'test_access_token',
                'refresh_token': 'test_refresh_token',
                'expires_in': 3600,
                'token_type': 'Bearer'
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            # Test token exchange
            result = self.oauth_manager._exchange_code_for_token('test_code', 'test_verifier')
            
            # Verify result
            self.assertEqual(result['access_token'], 'test_access_token')
            self.assertEqual(result['refresh_token'], 'test_refresh_token')
            self.assertEqual(result['expires_in'], 3600)
            self.assertEqual(result['token_type'], 'Bearer')
            
            # Verify request was made correctly
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            self.assertEqual(call_args[0][0], 'https://auth.example.com/oauth/token')
            self.assertEqual(call_args[1]['data']['grant_type'], 'authorization_code')
            self.assertEqual(call_args[1]['data']['client_id'], 'test_client_id')
            self.assertEqual(call_args[1]['data']['code'], 'test_code')
    
    def test_refresh_token_success(self):
        """Test successful token refresh"""
        # Skip if requests not available
        try:
            import requests
        except ImportError:
            self.skipTest("requests module not available")
        
        with patch('requests.post') as mock_post:
            # Store tokens with refresh token
            self.oauth_manager.token_storage.store_tokens(
                access_token="old_token",
                refresh_token="refresh_token",
                expires_in=3600
            )
            
            # Mock successful refresh response
            mock_response = MagicMock()
            mock_response.json.return_value = {
                'access_token': 'new_access_token',
                'refresh_token': 'new_refresh_token',
                'expires_in': 3600,
                'token_type': 'Bearer'
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            # Test token refresh
            success = self.oauth_manager.refresh_token()
            
            # Verify success
            self.assertTrue(success)
            
            # Verify new token is stored
            new_token = self.oauth_manager.get_access_token()
            self.assertEqual(new_token, 'new_access_token')
    
    def test_refresh_token_failure(self):
        """Test token refresh failure"""
        # Skip if requests not available
        try:
            import requests
        except ImportError:
            self.skipTest("requests module not available")
        
        with patch('requests.post') as mock_post:
            # Store tokens with refresh token
            self.oauth_manager.token_storage.store_tokens(
                access_token="old_token",
                refresh_token="refresh_token",
                expires_in=3600
            )
            
            # Mock failed refresh response
            mock_post.side_effect = Exception("Network error")
            
            # Test token refresh
            success = self.oauth_manager.refresh_token()
            
            # Verify failure
            self.assertFalse(success)
    
    def test_refresh_token_no_refresh_token(self):
        """Test token refresh when no refresh token available"""
        # Store tokens without refresh token
        self.oauth_manager.token_storage.store_tokens(
            access_token="test_token",
            expires_in=3600
        )
        
        # Test token refresh
        success = self.oauth_manager.refresh_token()
        
        # Verify failure
        self.assertFalse(success)


class TestOAuthCallbackHandler(unittest.TestCase):
    """Test OAuthCallbackHandler functionality"""
    
    def test_callback_handler_creation(self):
        """Test OAuthCallbackHandler can be created"""
        # OAuthCallbackHandler requires request, client_address, and server parameters
        # This test verifies the class exists and can be imported
        self.assertTrue(hasattr(OAuthCallbackHandler, 'do_GET'))


class TestOAuthManagerIntegration(unittest.TestCase):
    """Integration tests for OAuthManager"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary token file for testing
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
        
        # Mock configuration
        self.mock_config = MagicMock()
        self.mock_config.oauth.client_id = "test_client_id"
        self.mock_config.oauth.client_secret = "test_client_secret"
        self.mock_config.oauth.redirect_uri = "http://127.0.0.1:54783/callback"
        self.mock_config.oauth.auth_url = "https://auth.example.com/oauth/authorize"
        self.mock_config.oauth.token_url = "https://auth.example.com/oauth/token"
        self.mock_config.oauth.token_storage_path = self.temp_file.name
        
        # Initialize OAuth manager with mock config
        self.oauth_manager = OAuthManager(self.mock_config)
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_full_token_lifecycle(self):
        """Test complete token lifecycle"""
        # 1. Initially not authenticated
        self.assertFalse(self.oauth_manager.is_authenticated())
        self.assertIsNone(self.oauth_manager.get_access_token())
        
        # 2. Store tokens manually (simulating successful OAuth flow)
        self.oauth_manager.token_storage.store_tokens(
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            expires_in=3600,
            token_type="Bearer"
        )
        
        # 3. Verify authenticated
        self.assertTrue(self.oauth_manager.is_authenticated())
        token = self.oauth_manager.get_access_token()
        self.assertEqual(token, "test_access_token")
        
        # 4. Test logout
        self.oauth_manager.logout()
        self.assertFalse(self.oauth_manager.is_authenticated())
        self.assertIsNone(self.oauth_manager.get_access_token())
    
    def test_token_storage_persistence(self):
        """Test token storage persistence across manager instances"""
        # Store tokens with first manager
        self.oauth_manager.token_storage.store_tokens(
            access_token="persistent_token",
            expires_in=3600
        )
        
        # Create new manager instance
        new_manager = OAuthManager(self.mock_config)
        
        # Verify tokens are persisted
        self.assertTrue(new_manager.is_authenticated())
        token = new_manager.get_access_token()
        self.assertEqual(token, "persistent_token")


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
