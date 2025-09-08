# 🌐 Samay Sync Web Dashboard

A beautiful, interactive web interface to showcase Samay Sync progress to your team.

## 🚀 Quick Start

```bash
# Start the dashboard
python3 demo/web_dashboard.py

# Or use the launch script
./scripts/dashboard.sh

# Open in browser
open http://localhost:8080
```

## 📊 Features

### **Real-Time Module Status**
- ✅ **Configuration Module**: Settings and validation status
- ✅ **Database Module**: ActivityWatch connection and data stats
- ✅ **Sync State Manager**: Sync progress and duplicate prevention
- ✅ **OAuth Manager**: Authentication status and PKCE support
- ✅ **Sync Manager**: Complete sync orchestration with auto-sync

### **Interactive Controls**
- 🔐 **Login/Logout**: OAuth authentication with ActivityWatch service management
- 🗄️ **Database Data**: View live ActivityWatch events
- 🔄 **Sync State**: Monitor sync progress and states
- ▶️ **Start Auto Sync**: Start automatic synchronization
- ⏹️ **Stop Auto Sync**: Stop synchronization process

### **Live ActivityWatch Data**
- 📦 **Real Buckets**: Live bucket information
- 📊 **Event Counts**: Total and unsynced events
- 🕒 **Recent Activity**: Latest user activities (Cursor, Android Studio, etc.)
- 🔄 **Auto-Refresh**: Updates every 5 seconds

### **Service Management Integration**
- 🚀 **Auto Start**: Login triggers `run.sh` to start ActivityWatch services
- 🛑 **Auto Stop**: Logout triggers `stop.sh` to stop ActivityWatch services
- ⚡ **Background Execution**: Non-blocking script execution
- 🔄 **Service Health**: Real-time service status monitoring

### **Team-Friendly Interface**
- 🎨 **Beautiful Design**: Modern, responsive UI
- 📱 **Mobile Ready**: Works on all devices
- 🔄 **Auto-Updates**: No manual refresh needed
- 📈 **Progress Visualization**: Clear status indicators

## 🎯 Perfect for Team Demos

**Show Your Team:**
- ✅ **Working Modules**: All 5 core modules operational
- ✅ **Real Data**: Live ActivityWatch integration
- ✅ **Zero Duplicates**: Clean sync state management
- ✅ **Auto Sync**: Complete synchronization orchestration
- ✅ **Service Management**: Automated ActivityWatch lifecycle
- ✅ **Production Ready**: App-ready architecture

**Share Progress:**
- 📊 **Module Status**: Green checkmarks for working modules
- 📈 **Data Flow**: Real events being processed
- 🔐 **Auth Ready**: OAuth 2.0 with PKCE implemented
- 🚀 **Sync Manager**: Complete auto-sync with start/stop controls
- ⚡ **Real-Time**: Live status updates every 5 seconds
- 🔧 **Service Control**: Automated service start/stop

## 🛠️ Technical Details

**Built With:**
- Python 3 HTTP server
- Real-time API endpoints
- Modern HTML5/CSS3/JavaScript
- Responsive design
- Optimized shell script integration

**API Endpoints:**
- `/` - Main dashboard
- `/api/status` - System status
- `/api/modules` - Module status
- `/api/data` - Live ActivityWatch data
- `/api/login` - OAuth login + ActivityWatch start
- `/api/logout` - OAuth logout + ActivityWatch stop
- `/api/database` - Database data display
- `/api/sync-state` - Sync state manager
- `/api/sync-manager` - Sync manager stats
- `/api/sync-start` - Start auto-sync
- `/api/sync-stop` - Stop auto-sync

## 🔧 Service Management

### **Optimized Scripts Integration**

The dashboard automatically manages ActivityWatch services through optimized shell scripts:

**`run.sh` (Optimized):**
- ✅ **Smart Detection**: Checks if services are already running
- ✅ **Graceful Build**: Comprehensive error handling and logging
- ✅ **Server Readiness**: Waits for ActivityWatch server to be ready
- ✅ **Health Checks**: Verifies service startup before proceeding
- ✅ **User Feedback**: Clear progress indicators and helpful tips

**`stop.sh` (Optimized):**
- ✅ **Graceful Shutdown**: SIGTERM first, then SIGKILL if needed
- ✅ **Port Cleanup**: Ensures port 5600 is free
- ✅ **Environment Cleanup**: Removes virtual environment
- ✅ **Status Reporting**: Comprehensive cleanup summary

### **Service Lifecycle**

```
Login Button → OAuth Auth → run.sh → ActivityWatch Services Start
Logout Button → OAuth Logout → stop.sh → ActivityWatch Services Stop
```

**Features:**
- 🔄 **Non-blocking**: Scripts run in background threads
- 📊 **Real-time**: Service status updates immediately
- 🛡️ **Error Handling**: Graceful failure recovery
- 📝 **Logging**: Detailed execution logs

## 🎬 Demo Script

1. **Start Dashboard**: `python3 demo/web_dashboard.py`
2. **Open Browser**: `http://localhost:8080`
3. **Show Team**: 
   - All 5 modules working ✅
   - Real ActivityWatch data 📊
   - Live event processing 🔄
   - Interactive controls 🎮
   - Auto-sync start/stop ▶️⏹️
   - Service management 🚀🛑
   - Complete MVP ready 🎉

### **Demo Flow:**
1. **Show Module Status**: All green checkmarks
2. **Click Login**: Watch ActivityWatch services start automatically
3. **Show Live Data**: Real events from ActivityWatch
4. **Start Auto Sync**: Demonstrate sync orchestration
5. **Click Logout**: Watch services stop gracefully
6. **Show Service Management**: Automated lifecycle

## 🔧 Customization

**Environment Variables:**
```bash
export SAMAY_OAUTH_CLIENT_ID="your_client_id"
export SAMAY_OAUTH_CLIENT_SECRET="your_client_secret"
```

**Port Configuration:**
```python
# Change port in web_dashboard.py
port = 8080  # Change to your preferred port
```

**Script Paths:**
```python
# Scripts are automatically located at:
# samay-sync/scripts/run.sh
# samay-sync/scripts/stop.sh
```

## 📱 Mobile Demo

Perfect for showing on:
- 💻 **Laptop**: Full dashboard experience
- 📱 **Phone**: Responsive mobile view
- 📺 **Projector**: Team presentation mode
- 🖥️ **Tablet**: Touch-friendly interface

## 🚀 Production Features

**Ready for Production:**
- ✅ **Error Handling**: Comprehensive error recovery
- ✅ **Logging**: Detailed execution logs
- ✅ **Health Checks**: Service status monitoring
- ✅ **Graceful Shutdown**: Clean service termination
- ✅ **Cross-Platform**: Works on macOS, Linux, Windows
- ✅ **Non-blocking**: Responsive UI during operations

## 📊 Performance

**Optimizations:**
- ⚡ **Fast Startup**: Optimized build process
- 🔄 **Efficient Sync**: Smart duplicate prevention
- 📡 **Real-time Updates**: 5-second refresh cycle
- 🛡️ **Robust Error Handling**: Graceful failure recovery
- 🧹 **Clean Shutdown**: Proper resource cleanup

---

**🎉 Ready to impress your team with Samay Sync's complete production-ready system!**