# ActivityWatch URL Scheme Integration

This document describes the new URL scheme functionality added to ActivityWatch that allows the application to be opened from web URLs and automatically sync data with a backend API.

## Features Implemented

### 1. Info.plist File

- Added `Info.plist` file to enable opening the app from web URLs
- Supports `activitywatch://` URL scheme
- Compatible with macOS applications

### 2. Token Storage

- Added token storage functionality to the database
- Tokens are stored persistently across application restarts
- Supports both Peewee (SQLite) and Memory storage backends
- Token management API endpoints:
  - `GET /api/0/token` - Get stored token
  - `POST /api/0/token` - Store token
  - `DELETE /api/0/token` - Delete token

### 3. URL Scheme Handling

- New API endpoint: `POST /api/0/url-scheme`
- Extracts tokens from URLs in format: `activitywatch://token?token=YOUR_TOKEN`
- Automatically stores extracted tokens in the database
- Handles URL parsing and validation

### 4. Backend API Integration

- Modified scheduler to call backend API every 10 minutes
- Sends events to `http://localhost:3000/activities`
- Uses stored token for authentication
- Only deletes local events if API call succeeds
- No retry logic for failed API calls (as requested)

## Usage

### Setting Up Token via URL Scheme

1. **From Web Application:**

   ```javascript
   // Redirect user to ActivityWatch with token
   window.location.href = `activitywatch://token?token=${userToken}`;
   ```

2. **From Command Line:**

   ```bash
   # Open ActivityWatch with token
   open "activitywatch://token?token=your-token-here"
   ```

3. **Direct API Call:**
   ```bash
   curl -X POST http://localhost:5600/api/0/url-scheme \
     -H "Content-Type: application/json" \
     -d '{"url": "activitywatch://token?token=your-token-here"}'
   ```

### API Endpoints

#### Token Management

```bash
# Get current token
curl http://localhost:5600/api/0/token

# Store token directly
curl -X POST http://localhost:5600/api/0/token \
  -H "Content-Type: application/json" \
  -d '{"token": "your-token-here"}'

# Delete token
curl -X DELETE http://localhost:5600/api/0/token
```

#### URL Scheme Processing

```bash
# Process URL scheme
curl -X POST http://localhost:5600/api/0/url-scheme \
  -H "Content-Type: application/json" \
  -d '{"url": "activitywatch://token?token=your-token-here"}'
```

## Backend API Format

The scheduler sends events to the backend API in the following format:

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

## Configuration

### Scheduler Settings

The scheduler runs every 10 minutes by default. This can be configured in the server settings:

```bash
# Run with custom interval (in minutes)
aw-server --scheduler-interval 5
```

### Backend API Endpoint

The backend API endpoint is hardcoded to `http://localhost:3000/activities`. To change this, modify the `_send_events_to_api` method in `scheduler.py`.

## Error Handling

- **No Token:** If no token is stored, the scheduler logs a warning and skips the API call
- **API Failure:** If the API call fails, events are not deleted from local storage
- **Network Issues:** Network errors are logged but don't stop the scheduler
- **No Retry:** Failed API calls are not retried (as requested)

## Testing

Use the provided test script to verify functionality:

```bash
python url_scheme_example.py
```

This script tests:

- Server connectivity
- URL scheme token extraction
- Token management endpoints
- Direct token storage

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

### Memory Storage

Tokens are stored in memory as a simple string variable (`_token`).

## Security Considerations

- Tokens are stored in the local database
- URL scheme validation ensures only `activitywatch://` URLs are processed
- Host header validation protects against DNS rebinding attacks
- No token validation is performed (backend should validate tokens)

## Troubleshooting

### Common Issues

1. **"No authentication token found"**

   - Ensure a token has been stored via URL scheme or API
   - Check if the token was stored successfully

2. **"Backend API returned status 401"**

   - Verify the token is valid
   - Check if the backend API is running

3. **"Cannot connect to ActivityWatch server"**

   - Ensure `aw-server` is running
   - Check if the server is listening on the correct port (default: 5600)

4. **URL scheme not working**
   - Verify the `Info.plist` file is in the correct location
   - Check if the application is properly registered with the system

### Logs

Check the ActivityWatch server logs for detailed error messages:

```bash
# View logs
tail -f ~/.local/share/activitywatch/aw-server/logs/aw-server.log
```
