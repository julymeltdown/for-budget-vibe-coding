#!/usr/bin/env python3
"""
Emergency Error Notification Script
Sends Slack webhook notification when automation system encounters critical errors
"""

import sys
import traceback
from notification_manager import NotificationManager
import logging

def send_critical_error_notification(error_type, error_message, log_excerpt=None):
    """Send critical error notification to Slack"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize notification manager
        notifier = NotificationManager("notification_config.json")
        
        # Create detailed error message
        title = f"🚨 Critical Automation Error: {error_type}"
        
        message = f"**Error Type:** {error_type}\n"
        message += f"**Error Message:** {error_message}\n"
        message += f"**System:** Task Orchestrator Enhanced\n"
        message += f"**Status:** System terminated abnormally\n\n"
        
        if log_excerpt:
            message += f"**Log Excerpt:**\n```\n{log_excerpt[:1000]}...\n```\n\n"
        
        message += "**Action Required:**\n"
        message += "• Check system logs for details\n"
        message += "• Resolve dependency issues\n"
        message += "• Restart automation system\n"
        
        # Send notification
        success = notifier.send_notification(
            message=message,
            title=title,
            severity="error"
        )
        
        if success:
            print("✅ Error notification sent successfully")
            logging.info("Critical error notification sent to Slack")
        else:
            print("❌ Failed to send error notification")
            logging.error("Failed to send critical error notification")
            
        return success
        
    except Exception as e:
        print(f"❌ Failed to send notification: {e}")
        logging.error(f"Exception in error notification system: {e}")
        return False

def send_pyautogui_dependency_error():
    """Send specific notification for PyAutoGUI dependency error"""
    
    error_type = "PyAutoGUI Dependency Error"
    error_message = "PyAutoGUI was unable to import pyscreeze. This is likely because Pillow (PIL) is not properly installed or incompatible with the current Python version."
    
    log_excerpt = """
PyAutoGUI error: PyAutoGUI was unable to import pyscreeze. 
(This is likely because you're running a version of Python that Pillow doesn't support currently.) 
Please install this module to enable the function you tried to call.

Failed to find image: continue_button.png
Failed to find image: projects_button.png
System terminated with KeyboardInterrupt
    """
    
    return send_critical_error_notification(error_type, error_message, log_excerpt)

if __name__ == "__main__":
    # Send PyAutoGUI dependency error notification
    success = send_pyautogui_dependency_error()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
