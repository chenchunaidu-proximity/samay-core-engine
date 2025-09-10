#!/usr/bin/env python3
"""
Minimal URL scheme test script for debugging samay:// handling
"""
import sys
import AppKit
from AppKit import NSAppleEventManager
from PyObjCTools import AppHelper

# Use numeric constants (same as in main.py fix)
keyDirectObject = 0x2D2D2D2D  # '----'
kInternetEventClass = 0x4755524C  # 'GURL'
kAEGetURL = 0x4755524C  # 'GURL'

class URLHandler(AppKit.NSObject):
    def handleGetURLEvent_withReplyEvent_(self, event, replyEvent):
        url_desc = event.paramDescriptorForKeyword_(keyDirectObject)
        if url_desc:
            print("✅ Received URL:", url_desc.stringValue())
        else:
            print("❌ No URL in AppleEvent")

# Create handler and keep strong reference
handler = URLHandler.alloc().init()

# Register for URL scheme events
NSAppleEventManager.sharedAppleEventManager().setEventHandler_andSelector_forEventClass_andEventID_(
    handler,
    "handleGetURLEvent:withReplyEvent:",
    kInternetEventClass,
    kAEGetURL
)

print("🔗 Listening for samay:// events...")
print("📝 Test with: open 'samay://token=123&url=http://localhost:3000/activities'")
print("⏹️  Press Ctrl+C to stop")

try:
    AppHelper.runConsoleEventLoop()
except KeyboardInterrupt:
    print("\n🛑 Stopped")

