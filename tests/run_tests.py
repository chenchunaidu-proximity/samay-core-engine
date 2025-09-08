#!/usr/bin/env python3
"""
Test runner for Samay Core Engine authentication UI tests
"""

import sys
import os
import subprocess

def run_test(test_file):
    """Run a single test file."""
    print(f"\n{'='*60}")
    print(f"Running {test_file}")
    print('='*60)
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error running {test_file}: {e}")
        return False

def main():
    """Run all authentication UI tests."""
    print("🧪 Samay Core Engine - Authentication UI Test Suite")
    print("=" * 60)
    
    # Get the tests directory
    tests_dir = os.path.dirname(__file__)
    
    # List of test files to run
    test_files = [
        "test_auth_ui.py",
        "test_auth_comprehensive.py"
    ]
    
    passed = 0
    total = len(test_files)
    
    for test_file in test_files:
        test_path = os.path.join(tests_dir, test_file)
        if os.path.exists(test_path):
            if run_test(test_path):
                passed += 1
        else:
            print(f"❌ Test file not found: {test_path}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Suite Results: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All test suites passed!")
        print("\n✅ Authentication UI implementation is ready for commit!")
        print("\nSummary of implemented features:")
        print("  • Complete authentication UI in system tray")
        print("  • Login/logout functionality with proper error handling")
        print("  • Dynamic authentication status display")
        print("  • Periodic status updates")
        print("  • Clean integration with existing UI")
        
        print("\nNext steps:")
        print("  1. Commit the authentication UI changes")
        print("  2. Test with real aw-server instance")
        print("  3. Test complete authentication flow")
        
        return True
    else:
        print("❌ Some test suites failed. Please review and fix.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
