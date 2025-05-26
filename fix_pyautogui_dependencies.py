#!/usr/bin/env python3
"""
PyAutoGUI Dependencies Fix Script
Resolves PyAutoGUI import issues by properly installing required dependencies
"""

import sys
import subprocess
import os
import logging
from pathlib import Path

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/dependency_fix.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def run_command(command, logger):
    """Run a command and return the result"""
    logger.info(f"Running command: {command}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        if result.returncode == 0:
            logger.info(f"Command succeeded: {command}")
            if result.stdout:
                logger.info(f"STDOUT: {result.stdout[:500]}")
        else:
            logger.error(f"Command failed: {command}")
            logger.error(f"Return code: {result.returncode}")
            if result.stderr:
                logger.error(f"STDERR: {result.stderr[:500]}")
        
        return result.returncode == 0, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {command}")
        return False, "", "Command timed out"
    except Exception as e:
        logger.error(f"Exception running command: {e}")
        return False, "", str(e)

def check_python_version(logger):
    """Check if Python version is compatible"""
    python_version = sys.version_info
    logger.info(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # PyAutoGUI works with Python 3.6+
    if python_version >= (3, 6):
        logger.info("✅ Python version is compatible")
        return True
    else:
        logger.error("❌ Python version is too old. Please upgrade to Python 3.6+")
        return False

def fix_pyautogui_dependencies(logger):
    """Fix PyAutoGUI dependencies step by step"""
    
    logger.info("🔧 Starting PyAutoGUI dependencies fix...")
    
    # Step 1: Uninstall potentially conflicting packages
    logger.info("Step 1: Uninstalling potentially conflicting packages...")
    uninstall_commands = [
        "pip uninstall -y pyautogui",
        "pip uninstall -y pillow",
        "pip uninstall -y pyscreeze",
        "pip uninstall -y pygetwindow",
        "pip uninstall -y pymsgbox",
        "pip uninstall -y pytweening"
    ]
    
    for cmd in uninstall_commands:
        success, stdout, stderr = run_command(cmd, logger)
        # Don't fail if uninstall fails (package might not be installed)
    
    # Step 2: Update pip
    logger.info("Step 2: Updating pip...")
    success, stdout, stderr = run_command("python -m pip install --upgrade pip", logger)
    if not success:
        logger.warning("Failed to update pip, continuing...")
    
    # Step 3: Install dependencies in correct order
    logger.info("Step 3: Installing dependencies in correct order...")
    install_commands = [
        "pip install --upgrade setuptools wheel",
        "pip install --upgrade pillow==10.4.0",
        "pip install --upgrade pyscreeze==0.1.30",
        "pip install --upgrade pygetwindow==0.0.9",
        "pip install --upgrade pymsgbox==1.0.9",
        "pip install --upgrade pytweening==1.2.0",
        "pip install --upgrade pyautogui==0.9.54"
    ]
    
    for cmd in install_commands:
        success, stdout, stderr = run_command(cmd, logger)
        if not success:
            logger.error(f"❌ Failed to execute: {cmd}")
            return False
    
    # Step 4: Verify installation
    logger.info("Step 4: Verifying installation...")
    return verify_installation(logger)

def verify_installation(logger):
    """Verify that PyAutoGUI can be imported properly"""
    
    logger.info("🔍 Verifying PyAutoGUI installation...")
    
    try:
        # Test basic import
        import pyautogui
        logger.info("✅ PyAutoGUI imported successfully")
        
        # Test pyscreeze specifically
        import pyscreeze
        logger.info("✅ pyscreeze imported successfully")
        
        # Test basic screenshot functionality
        logger.info("Testing screenshot functionality...")
        screenshot = pyautogui.screenshot()
        logger.info(f"✅ Screenshot successful: {screenshot.size}")
        
        # Test image location (with a simple test)
        logger.info("Testing image location functionality...")
        # This will fail if image doesn't exist, but that's expected
        try:
            pyautogui.locateOnScreen("nonexistent.png")
        except pyautogui.ImageNotFoundException:
            logger.info("✅ Image location functionality working (expected error for nonexistent image)")
        except Exception as e:
            if "pyscreeze" in str(e).lower():
                logger.error(f"❌ pyscreeze still not working: {e}")
                return False
            else:
                logger.info("✅ Image location functionality working")
        
        logger.info("🎉 All PyAutoGUI functionality verified successfully!")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during verification: {e}")
        return False

def send_fix_notification(success, logger):
    """Send notification about fix results"""
    try:
        from notification_manager import NotificationManager
        
        notifier = NotificationManager("notification_config.json")
        
        if success:
            title = "✅ PyAutoGUI Dependencies Fixed"
            message = """
**Status:** Successfully resolved PyAutoGUI dependency issues

**Actions Taken:**
• Reinstalled Pillow with correct version
• Reinstalled pyscreeze with correct version  
• Reinstalled PyAutoGUI with all dependencies
• Verified all functionality

**Result:** Automation system ready to restart
            """
            severity = "info"
        else:
            title = "❌ PyAutoGUI Dependencies Fix Failed"
            message = """
**Status:** Failed to resolve PyAutoGUI dependency issues

**Actions Attempted:**
• Attempted to reinstall Pillow
• Attempted to reinstall pyscreeze
• Attempted to reinstall PyAutoGUI

**Action Required:**
• Check dependency_fix.log for details
• Consider manual installation
• Check Python version compatibility
            """
            severity = "error"
        
        notifier.send_notification(message, title, severity)
        
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")

def main():
    """Main function"""
    
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    
    logger = setup_logging()
    logger.info("🚀 Starting PyAutoGUI Dependencies Fix")
    
    # Check Python version
    if not check_python_version(logger):
        return False
    
    # Fix dependencies
    success = fix_pyautogui_dependencies(logger)
    
    # Send notification
    send_fix_notification(success, logger)
    
    if success:
        logger.info("🎉 PyAutoGUI dependencies fixed successfully!")
        print("\n" + "="*50)
        print("✅ SUCCESS: PyAutoGUI dependencies fixed!")
        print("You can now restart the automation system:")
        print("python task_orchestrator_enhanced.py")
        print("="*50)
    else:
        logger.error("❌ Failed to fix PyAutoGUI dependencies")
        print("\n" + "="*50)
        print("❌ FAILED: Could not fix PyAutoGUI dependencies")
        print("Please check logs/dependency_fix.log for details")
        print("You may need to manually install dependencies")
        print("="*50)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
