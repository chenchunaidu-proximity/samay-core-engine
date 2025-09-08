# Samay Sync

**OAuth Authentication & Cloud Synchronization Module for ActivityWatch**

## Overview

Samay Sync extends the ActivityWatch ecosystem with secure OAuth-based authentication and cloud synchronization capabilities. It enables users to authenticate via web browser and automatically sync their activity data to a backend server.

## Features

### 🔐 OAuth Authentication
- **Hybrid Callback Strategy**: Loopback server with deep link fallback
- **Secure Token Storage**: Platform-specific secure storage (macOS Keychain, Windows Credential Manager)
- **Token Refresh**: Automatic token refresh before expiration
- **Cross-Platform**: Works on macOS, Windows, and Linux

### ☁️ Cloud Synchronization
- **Event Queue**: Local queue for outgoing events with offline support
- **Batch Upload**: Configurable interval-based data synchronization (default: 5 minutes)
- **Deduplication**: Prevents duplicate data transmission
- **Error Handling**: Robust retry logic and error recovery

### 🎯 Integration
- **Tray Integration**: Seamless integration with aw-qt tray application
- **Configuration**: Extends existing ActivityWatch configuration system
- **Logging**: Integrated with aw-core logging framework
- **Testing**: Comprehensive test suite with mock endpoints

## Architecture

### Core Components

```
samay-sync/
├── auth/                    # Authentication module
│   ├── oauth_manager.py     # OAuth flow management
│   ├── token_storage.py    # Secure token persistence
│   └── auth_state.py       # Authentication state management
├── sync/                   # Synchronization module
│   ├── event_queue.py      # Event queuing system
│   ├── sync_manager.py     # Sync orchestration
│   └── api_client.py       # Backend API communication
├── ui/                     # User interface integration
│   ├── tray_integration.py # aw-qt tray menu integration
│   └── loading_indicator.py # Loading UI components
├── config/                 # Configuration management
│   ├── auth_config.py      # OAuth configuration
│   └── sync_config.py      # Sync settings
├── utils/                  # Utility functions
│   ├── encryption.py       # Token encryption utilities
│   ├── network_utils.py    # Network helper functions
│   └── platform_utils.py   # Platform-specific utilities
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── mocks/             # Mock implementations
└── docs/                  # Documentation
    ├── api/               # API documentation
    └── guides/            # User guides
```

### Design Principles

- **SOLID Principles**: Single responsibility, open/closed, dependency inversion
- **Loose Coupling**: Modular design with clear interfaces
- **Testability**: Comprehensive test coverage with mock implementations
- **Security**: Secure token storage and transmission
- **Reliability**: Robust error handling and offline support

## OAuth Flow

### 1. Login Process
```
User clicks "Login" → App starts local server → Browser opens OAuth URL → 
User authenticates → Browser redirects to callback → App receives tokens → 
Tokens stored securely → UI updates to show authenticated state
```

### 2. Callback Strategy
- **Primary**: Local HTTP server (`http://127.0.0.1:{port}/callback`)
- **Fallback**: Deep link (`samay://callback`)
- **Security**: State parameter validation and PKCE support

### 3. Token Management
- **Storage**: Platform-specific secure storage
- **Encryption**: Additional base64 encryption layer
- **Refresh**: Automatic refresh before expiration
- **Cleanup**: Secure token removal on logout

## Synchronization

### Event Processing
1. **Collection**: ActivityWatch events collected locally
2. **Queueing**: Events added to local sync queue
3. **Batching**: Events batched for efficient transmission
4. **Upload**: Batched events sent to backend server
5. **Deduplication**: Sent events tracked to prevent duplicates
6. **Error Handling**: Failed uploads retried with exponential backoff

### Data Format
```json
{
  "events": [
    {
      "timestamp": "2024-01-01T12:00:00Z",
      "duration": 3600.0,
      "data": {
        "app": "Chrome",
        "title": "GitHub - ActivityWatch",
        "url": "https://github.com/ActivityWatch"
      }
    }
  ],
  "user_id": "user123",
  "device_id": "device456",
  "sync_timestamp": "2024-01-01T12:05:00Z"
}
```

## Configuration

### OAuth Settings
```toml
[auth]
enabled = true
client_id = "your-client-id"
redirect_uri = "http://127.0.0.1:54783/callback"
scopes = ["profile", "email"]
auth_url = "https://your-provider.com/oauth/authorize"
token_url = "https://your-provider.com/oauth/token"
```

### Sync Settings
```toml
[sync]
enabled = true
base_url = "https://your-backend.com/api"
sync_interval = 300  # 5 minutes
batch_size = 100
max_retries = 3
offline_queue_size = 1000
```

## Installation

### Prerequisites
- Python 3.8+
- ActivityWatch core components
- Platform-specific dependencies

### Development Setup
```bash
# Clone the repository
git clone <repository-url>
cd samay-core-engine/samay-sync

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Start development server
python -m samay_sync.dev_server
```

## Usage

### Integration with aw-qt
The module integrates seamlessly with the existing ActivityWatch tray application:

1. **Login**: Right-click tray icon → "Login"
2. **Status**: Tray menu shows "Logged in as {username}"
3. **Logout**: Right-click tray icon → "Logout"
4. **Sync**: Automatic background synchronization

### API Integration
```python
from samay_sync.auth import AuthManager
from samay_sync.sync import SyncManager

# Initialize components
auth_manager = AuthManager()
sync_manager = SyncManager(auth_manager)

# Start authentication
await auth_manager.start_login_flow()

# Start synchronization
sync_manager.start_sync()
```

## Testing

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **Mock Tests**: OAuth flow testing with mock endpoints
- **Platform Tests**: macOS/Windows specific functionality

### Running Tests
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/

# Run with coverage
pytest --cov=samay_sync
```

## Security Considerations

### Token Security
- **Storage**: Platform-specific secure storage (Keychain/Credential Manager)
- **Encryption**: Additional encryption layer for tokens at rest
- **Transmission**: HTTPS for all API communications
- **Cleanup**: Secure token removal on logout

### OAuth Security
- **PKCE**: Proof Key for Code Exchange for enhanced security
- **State Parameter**: CSRF protection
- **Redirect URI**: Strict validation
- **Token Scope**: Minimal required permissions

## Contributing

### Development Guidelines
- Follow SOLID principles and best practices
- Maintain comprehensive test coverage
- Document all public APIs
- Use type hints throughout
- Follow existing ActivityWatch patterns

### Code Quality
- **Linting**: Ruff/Black for code formatting
- **Type Checking**: MyPy for type validation
- **Security**: Bandit for security issue detection
- **Documentation**: Sphinx for API documentation

## License

This project is part of the ActivityWatch ecosystem and follows the same MPL-2.0 license.

## Support

For issues, questions, or contributions:
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Documentation**: Project documentation
- **Community**: ActivityWatch Discord/Forum

