# Samay Core Engine Progress Tracking

## Project Architecture Overview

### **Core Engine (Our Team - What we're developing):**
- **User Installation**: App installation process
- **Authentication UI**: Login/sign-in button interface  
- **Web Redirect**: Redirect users to authentication webpage
- **Token Management**: Store authentication tokens locally
- **Logout Functionality**: Option for users to logout
- **Data Transmission**: Send activity data along with token to backend API

### **Backend (Team B - Out of scope):**
- **API Development**: Create REST APIs for authentication and data
- **Data Storage**: Database management and data persistence
- **Security**: Authentication, authorization, and data protection

### **Frontend (Team F - Out of scope):**
- **Login Flow**: Implement authentication UI/UX
- **Data Visualization**: Fetch and display activity data
- **Analytics**: Summarize and present user activity insights

## Core Engine Implementation Status

This document tracks the progress made in the `demo_prep` branch, documenting the Core Engine implementation for the Samay activity tracking system.

## Key Features Implemented

### 1. URL Scheme Integration
- **Purpose**: Enable ActivityWatch to be opened from web URLs and automatically sync data with backend APIs
- **Implementation**: 
  - Added `Info.plist` file for macOS URL scheme support (`samay://`)
  - Implemented token storage in database (both Peewee/SQLite and Memory backends)
  - Created URL scheme handling API endpoint (`POST /api/0/url-scheme`)
  - Added token management endpoints (`GET/POST/DELETE /api/0/token`)

### 2. Backend API Integration
- **Purpose**: Automatically sync local events to external backend API
- **Implementation**:
  - Modified scheduler to call backend API every 10 minutes
  - Sends events to configurable backend endpoint (default: `http://localhost:3000/activities`)
  - Uses stored authentication token for API calls
  - Only deletes local events after successful API transmission
  - No retry logic for failed API calls (as requested)

### 3. Custom Branding ("Samay")
- **Purpose**: Rebrand ActivityWatch for demo purposes
- **Changes**:
  - App name: "ActivityWatch" → "Samay"
  - Bundle identifier: `net.activitywatch.ActivityWatch` → `net.samay.Samay`
  - App bundle: `ActivityWatch.app` → `Samay.app`
  - DMG file: `ActivityWatch.dmg` → `Samay.dmg`
  - All build scripts and configurations updated

### 4. Custom Submodule Repositories
- **Purpose**: Use custom forks for development and testing
- **Changes**:
  - `aw-core`: `ActivityWatch/aw-core.git` → `chenchunaidu-proximity/aw-core.git`
  - `aw-notify`: `ErikBjare/aw-notify.git` → `chenchunaidu-proximity/aw-notify.git`

## Files Added/Modified

### New Files Created
- **`/Info.plist`** - macOS app configuration with URL scheme support
- **`/URL_SCHEME_README.md`** - Comprehensive documentation for URL scheme functionality
- **`/url_scheme_example.py`** - Example script for testing URL scheme integration

### Modified Files
- **`/aw.spec`** - Updated PyInstaller configuration for custom branding
- **`/Makefile`** - Updated build targets for "Samay" branding
- **`/scripts/notarize.sh`** - Updated bundle identifiers and file paths
- **`/scripts/package/activitywatch-setup.iss`** - Updated Windows installer branding
- **`/scripts/package/dmgbuild-settings.py`** - Updated DMG build settings
- **`/scripts/build_changelog.py`** - Fixed macOS download link naming
- **`/.gitmodules`** - Updated submodule URLs to custom repositories

### Submodule Updates
- **`/aw-core/`** - Updated to custom repository (`chenchunaidu-proximity/aw-core.git`)
- **`/aw-notify/`** - Updated to custom repository (`chenchunaidu-proximity/aw-notify.git`)
- **`/aw-qt/`** - Updated to newer commit
- **`/aw-server/`** - Updated to newer commit
- **`/aw-watcher-window/`** - Updated to newer commit

### Key Code Changes in Server Files
- **`/aw-server/aw_server/api.py`** - Added token management and URL scheme handling endpoints
- **`/aw-server/aw_server/rest.py`** - Added REST API endpoints for `/token` and `/url-scheme`
- **`/aw-server/aw_server/scheduler.py`** - Modified to send events to backend API every 10 minutes
- **`/aw-server/aw_server/server.py`** - Updated to include new API endpoints and token storage

### Key Code Changes in aw-qt Files (Custom "Samay" Branding)
- **`/aw-qt/aw_qt/main.py`** - Help text: "A trayicon and service manager for Samay"
- **`/aw-qt/aw_qt/trayicon.py`** - Tooltip and menu text: "Samay" branding
- **`/aw-qt/aw_qt.spec`** - Bundle name: "Samay.app"
- **`/aw-qt/resources/aw-qt.desktop`** - Desktop entry name and icon: "Samay"
- **`/aw-qt/media/`** - Updated submodule to newer commit

**Status**: ✅ **IMPLEMENTED** - The `demo_prep` branch has "Samay" branding fully implemented in aw-qt. The `test` branch reverts these changes back to "ActivityWatch".

## API Endpoints Added

### Token Management
```bash
# Get current token
GET /api/0/token

# Store token directly
POST /api/0/token
Content-Type: application/json
{"token": "your-token-here"}

# Delete token
DELETE /api/0/token
```

### URL Scheme Processing
```bash
# Process URL scheme
POST /api/0/url-scheme
Content-Type: application/json
{"url": "samay://token?token=your-token-here"}
```

## Usage Examples

### Setting Up Token via URL Scheme
```javascript
// From web application
window.location.href = `samay://token?token=${userToken}`;
```

```bash
# From command line
open "samay://token?token=your-token-here"
```

### Backend API Format
The scheduler sends events to the backend API in this format:
```json
{
  "events": [
    {
      "id": 123,
      "timestamp": "2024-01-01T10:00:00+00:00",
      "duration": 3600.0,
      "data": {
        "app": "Chrome",
        "title": "Example Page"
      },
      "bucket_id": "aw-watcher-window"
    }
  ],
  "timestamp": "2024-01-01T11:00:00+00:00"
}
```

**Headers:**
- `Authorization: Bearer YOUR_TOKEN`
- `Content-Type: application/json`

## Database Schema

### Token Table (Peewee Storage)
```sql
CREATE TABLE tokenmodel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token VARCHAR UNIQUE NOT NULL,
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Configuration

### Scheduler Settings
- Runs every 10 minutes by default
- Configurable via `--scheduler-interval` parameter
- Backend API endpoint: `http://localhost:3000/activities` (hardcoded)

## Security Considerations
- Tokens stored in local database
- URL scheme validation ensures only `samay://` URLs are processed
- Host header validation protects against DNS rebinding attacks
- No token validation performed (backend should validate tokens)

## Testing
Use the provided test script to verify functionality:
```bash
python url_scheme_example.py
```

## Core Engine Implementation Status
- ✅ **Authentication Flow**: URL scheme integration implemented
- ✅ **Token Management**: Token storage and management working
- ✅ **Data Transmission**: Backend API synchronization implemented
- ✅ **User Experience**: Custom "Samay" branding applied
- ✅ **Documentation**: Implementation documentation created
- ✅ **Testing**: Test script provided for validation

## Next Steps
- [ ] Test URL scheme functionality in production environment
- [ ] Verify backend API integration works with real backend
- [ ] Consider adding retry logic for failed API calls
- [ ] Add configuration options for backend API endpoint
- [ ] Implement token validation if needed

## Notes
- The `test` branch represents the official ActivityWatch project without these customizations
- This `demo_prep` branch contains all the custom features for the demo
- All changes are backward compatible with the original ActivityWatch functionality
