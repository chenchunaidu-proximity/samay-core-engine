"""
Samay Sync Tray Integration

This module provides integration between Samay Sync and the aw-qt tray application.
It handles menu items, status updates, and user interactions for authentication and sync.
"""

import logging
import os
import sys
import webbrowser
from typing import Optional, Dict, Any
from PyQt6.QtCore import QTimer, pyqtSignal, QObject
from PyQt6.QtWidgets import QMenu, QMessageBox, QSystemTrayIcon
from PyQt6.QtGui import QIcon

# Add samay-sync to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.sync_config import Config
from auth.oauth_manager import OAuthManager
from sync.sync_manager import SyncManager

logger = logging.getLogger(__name__)


class SamaySyncTrayIntegration(QObject):
    """
    Handles Samay Sync integration with aw-qt tray application.
    
    This class manages:
    - Authentication status and menu items
    - Sync status updates
    - User interactions (login/logout)
    - Error notifications
    """
    
    # Signals for status updates
    status_changed = pyqtSignal(str)  # Emits new status text
    authentication_changed = pyqtSignal(bool)  # Emits authentication state
    
    def __init__(self, tray_icon: QSystemTrayIcon):
        super().__init__()
        self.tray_icon = tray_icon
        self.config = Config()
        self.oauth_manager: Optional[OAuthManager] = None
        self.sync_manager: Optional[SyncManager] = None
        
        # Status tracking
        self.is_authenticated = False
        self.sync_status = "stopped"  # stopped, syncing, synced, error
        self.last_sync_time: Optional[str] = None
        
        # Menu items (will be set by tray integration)
        self.login_action = None
        self.logout_action = None
        self.status_action = None
        self.settings_action = None
        
        # Initialize components
        self._initialize_components()
        
        # Setup status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(5000)  # Update every 5 seconds
        
        logger.info("Samay Sync tray integration initialized")
    
    def _initialize_components(self):
        """Initialize OAuth and Sync managers."""
        try:
            self.oauth_manager = OAuthManager()
            self.sync_manager = SyncManager()
            
            # Check initial authentication status
            self.is_authenticated = self.oauth_manager.is_authenticated()
            self.authentication_changed.emit(self.is_authenticated)
            
            logger.info(f"Samay Sync components initialized. Authenticated: {self.is_authenticated}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Samay Sync components: {e}")
            self._show_error(f"Failed to initialize Samay Sync: {e}")
    
    def add_menu_items(self, menu: QMenu) -> None:
        """
        Add Samay Sync menu items to the tray menu.
        
        Args:
            menu: The QMenu to add items to
        """
        # Add separator
        menu.addSeparator()
        
        # Add Samay Sync header
        header_action = menu.addAction("🔐 Samay Sync")
        header_action.setEnabled(False)
        
        # Add login/logout actions
        if self.is_authenticated:
            self.logout_action = menu.addAction("🚪 Logout", self._handle_logout)
            self.status_action = menu.addAction("📊 Status: Checking...", self._show_status)
            self.settings_action = menu.addAction("⚙️ Settings", self._show_settings)
        else:
            self.login_action = menu.addAction("🔑 Login", self._handle_login)
            self.status_action = menu.addAction("📊 Status: Not authenticated", self._show_status)
        
        # Add separator
        menu.addSeparator()
        
        logger.info("Samay Sync menu items added to tray")
    
    def _handle_login(self) -> None:
        """Handle user login request."""
        try:
            logger.info("Starting Samay Sync login process")
            
            # Update status
            if self.status_action:
                self.status_action.setText("📊 Status: Authenticating...")
            
            # Start OAuth flow
            if self.oauth_manager:
                success = self.oauth_manager.authenticate()
                
                if success:
                    self.is_authenticated = True
                    self.authentication_changed.emit(True)
                    self._update_menu_items()
                    self._show_success("Successfully logged in to Samay Sync!")
                    
                    # Start sync manager
                    if self.sync_manager:
                        self.sync_manager.start_auto_sync()
                        self.sync_status = "syncing"
                    
                    logger.info("Samay Sync login successful")
                else:
                    self._show_error("Login failed. Please try again.")
                    logger.warning("Samay Sync login failed")
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            self._show_error(f"Login error: {e}")
    
    def _handle_logout(self) -> None:
        """Handle user logout request."""
        try:
            logger.info("Starting Samay Sync logout process")
            
            # Stop sync manager
            if self.sync_manager:
                self.sync_manager.stop_auto_sync()
                self.sync_status = "stopped"
            
            # Clear authentication
            if self.oauth_manager:
                self.oauth_manager.logout()
            
            self.is_authenticated = False
            self.authentication_changed.emit(False)
            self._update_menu_items()
            
            self._show_success("Successfully logged out from Samay Sync!")
            logger.info("Samay Sync logout successful")
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            self._show_error(f"Logout error: {e}")
    
    def _update_menu_items(self) -> None:
        """Update menu items based on authentication status."""
        # This will be called by the tray integration to rebuild the menu
        pass
    
    def _update_status(self) -> None:
        """Update sync status from sync manager."""
        try:
            if not self.sync_manager or not self.is_authenticated:
                return
            
            # Get sync manager status
            stats = self.sync_manager.get_sync_stats()
            
            if stats.is_running:
                self.sync_status = "syncing"
                status_text = f"📊 Status: Syncing... ({stats.events_synced} events)"
            elif stats.last_sync_time:
                self.sync_status = "synced"
                last_sync = stats.last_sync_time
                status_text = f"📊 Status: Synced ({last_sync})"
            else:
                self.sync_status = "stopped"
                status_text = "📊 Status: Ready"
            
            # Update status action if it exists
            if self.status_action:
                self.status_action.setText(status_text)
            
            # Emit status change signal
            self.status_changed.emit(status_text)
            
        except Exception as e:
            logger.error(f"Status update error: {e}")
            if self.status_action:
                self.status_action.setText("📊 Status: Error")
    
    def _show_status(self) -> None:
        """Show detailed sync status."""
        try:
            if not self.sync_manager:
                self._show_error("Sync manager not available")
                return
            
            stats = self.sync_manager.get_sync_stats()
            
            status_msg = f"""
Samay Sync Status:

Authentication: {'✅ Authenticated' if self.is_authenticated else '❌ Not authenticated'}
Sync Status: {self.sync_status.title()}
Events Synced: {stats.events_synced}
Last Sync: {stats.last_sync_time or 'Never'}
Average Duration: {stats.average_sync_duration:.2f}s
Errors: {stats.sync_errors}
            """.strip()
            
            QMessageBox.information(None, "Samay Sync Status", status_msg)
            
        except Exception as e:
            logger.error(f"Status display error: {e}")
            self._show_error(f"Failed to get status: {e}")
    
    def _show_settings(self) -> None:
        """Show Samay Sync settings."""
        try:
            settings_msg = f"""
Samay Sync Settings:

OAuth Client ID: {self.config.oauth.client_id}
OAuth Redirect URI: {self.config.oauth.redirect_uri}
Backend API URL: {self.config.server.base_url}
Sync Interval: {self.config.sync.sync_interval}s
Database Path: {self.config.database.db_path}
            """.strip()
            
            QMessageBox.information(None, "Samay Sync Settings", settings_msg)
            
        except Exception as e:
            logger.error(f"Settings display error: {e}")
            self._show_error(f"Failed to get settings: {e}")
    
    def _show_success(self, message: str) -> None:
        """Show success notification."""
        self.tray_icon.showMessage(
            "Samay Sync",
            message,
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )
    
    def _show_error(self, message: str) -> None:
        """Show error notification."""
        self.tray_icon.showMessage(
            "Samay Sync Error",
            message,
            QSystemTrayIcon.MessageIcon.Critical,
            5000
        )
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            if self.status_timer:
                self.status_timer.stop()
            
            if self.sync_manager:
                self.sync_manager.stop_auto_sync()
            
            logger.info("Samay Sync tray integration cleaned up")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


def create_samay_sync_integration(tray_icon: QSystemTrayIcon) -> SamaySyncTrayIntegration:
    """
    Create and return a Samay Sync tray integration instance.
    
    Args:
        tray_icon: The QSystemTrayIcon to integrate with
        
    Returns:
        SamaySyncTrayIntegration instance
    """
    return SamaySyncTrayIntegration(tray_icon)
