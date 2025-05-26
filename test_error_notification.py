#!/usr/bin/env python3
"""
Test script for error notification system
Tests both Slack notifications and dependency error handling
"""

import sys
import logging
from send_error_notification import send_pyautogui_dependency_error, send_critical_error_notification
from notification_manager import NotificationManager

def test_slack_connection():
    """Test basic Slack webhook connection"""
    print("🔧 Testing Slack webhook connection...")
    
    try:
        notifier = NotificationManager("notification_config.json")
        
        success = notifier.send_notification(
            "This is a test message from the error notification system. If you receive this, the Slack integration is working correctly.",
            "🧪 Test Notification",
            "info"
        )
        
        if success:
            print("✅ Slack notification test PASSED")
            return True
        else:
            print("❌ Slack notification test FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Slack notification test ERROR: {e}")
        return False

def test_pyautogui_error_notification():
    """Test PyAutoGUI specific error notification"""
    print("🔧 Testing PyAutoGUI error notification...")
    
    try:
        success = send_pyautogui_dependency_error()
        
        if success:
            print("✅ PyAutoGUI error notification test PASSED")
            return True
        else:
            print("❌ PyAutoGUI error notification test FAILED")
            return False
            
    except Exception as e:
        print(f"❌ PyAutoGUI error notification test ERROR: {e}")
        return False

def test_critical_error_notification():
    """Test general critical error notification"""
    print("🔧 Testing critical error notification...")
    
    try:
        success = send_critical_error_notification(
            "Test Error Type",
            "This is a test error message for testing purposes",
            "Test log excerpt:\nLine 1: Test log entry\nLine 2: Another test entry"
        )
        
        if success:
            print("✅ Critical error notification test PASSED")
            return True
        else:
            print("❌ Critical error notification test FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Critical error notification test ERROR: {e}")
        return False

def test_dependency_check():
    """Test if dependencies are properly installed"""
    print("🔧 Testing PyAutoGUI dependencies...")
    
    try:
        import pyautogui
        print("✅ PyAutoGUI import successful")
        
        import pyscreeze
        print("✅ pyscreeze import successful")
        
        # Test basic functionality
        screenshot = pyautogui.screenshot()
        print(f"✅ Screenshot test successful: {screenshot.size}")
        
        print("✅ All dependency tests PASSED")
        return True
        
    except ImportError as e:
        print(f"❌ Dependency import test FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ Dependency functionality test FAILED: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 ERROR NOTIFICATION SYSTEM TEST")
    print("=" * 60)
    
    tests = [
        ("Dependency Check", test_dependency_check),
        ("Slack Connection", test_slack_connection),
        ("PyAutoGUI Error Notification", test_pyautogui_error_notification),
        ("Critical Error Notification", test_critical_error_notification)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} EXCEPTION: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:<10} {test_name}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests PASSED! System is ready.")
        sys.exit(0)
    else:
        print("⚠️  Some tests FAILED. Please check the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
