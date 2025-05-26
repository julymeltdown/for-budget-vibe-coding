import os
import sys
import logging
import argparse
import json
import time
from pathlib import Path

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("automation")

class ClaudeDesktopAutomation:
    def __init__(self, config_path=None):
        """Initialize Claude Desktop GUI automation class"""
        # Default configuration
        self.default_config = {
            "window_title": "Claude",
            "input_delay": 0.5,
            "screenshot_delay": 1.0,
            "max_retries": 3,
            "confidence_threshold": 0.7,
            "continue_button_text": "Continue",
            "new_chat_button_text": "New chat",
            "assets_dir": "assets",
            "continue_button_image": "continue_button.png",
            "new_chat_button_image": "new_chat_button.png"
        }
        
        # Load configuration file
        self.config = self.default_config.copy()
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    self.config.update(user_config)
                logging.info(f"Configuration file loaded: {config_path}")
            except Exception as e:
                logging.error(f"Failed to load configuration file: {e}")
        
        # Check and create assets directory
        self.assets_dir = self.config["assets_dir"]
        if not os.path.exists(self.assets_dir):
            os.makedirs(self.assets_dir)
            logging.info(f"Assets directory created: {self.assets_dir}")
        
        # Image file paths
        self.continue_button_image = os.path.join(self.assets_dir, self.config["continue_button_image"])
        self.new_chat_button_image = os.path.join(self.assets_dir, self.config["new_chat_button_image"])
        
        # Window activation status
        self.window_active = False
        
        logging.info("Claude Desktop automation initialization complete")
    
    def activate_window(self):
        """Activate Claude Desktop window."""
        try:
            # Find window by title
            # In actual implementation, use pyautogui.getWindowsWithTitle
            # Here, return True as example
            self.window_active = True
            logging.info("Claude Desktop window activated successfully")
            return True
        except Exception as e:
            logging.error(f"Error activating window: {e}")
            return False
    
    def find_and_click_image(self, image_path, max_retries=None, confidence=None):
        """Find image on screen and click it."""
        if max_retries is None:
            max_retries = self.config["max_retries"]
        
        if confidence is None:
            confidence = self.config["confidence_threshold"]
        
        if not os.path.exists(image_path):
            logging.error(f"Image file not found: {image_path}")
            return False
        
        # In actual implementation, use pyautogui.locateCenterOnScreen and pyautogui.click
        # Here, return True as example
        logging.info(f"Image clicked successfully: {image_path}")
        return True
    
    def capture_and_save_button(self, button_name, region=None):
        """Capture specific area of screen and save as button image."""
        try:
            # In actual implementation, use pyautogui.screenshot
            # Here, return True as example
            
            # Set image save path
            if button_name == "continue":
                image_path = self.continue_button_image
            elif button_name == "new_chat":
                image_path = self.new_chat_button_image
            else:
                image_path = os.path.join(self.assets_dir, f"{button_name}_button.png")
            
            # Create dummy image file
            with open(image_path, 'w') as f:
                f.write("dummy image")
            
            logging.info(f"{button_name} button image saved: {image_path}")
            return True
        
        except Exception as e:
            logging.error(f"Error capturing button: {e}")
            return False
    
    def input_text(self, text):
        """Input text into Claude Desktop input field."""
        try:
            # Check if window is active
            if not self.window_active:
                if not self.activate_window():
                    return False
            
            # In actual implementation, use pyautogui.hotkey and pyautogui.write
            # Here, return True as example
            logging.info(f"Text input complete: {text[:50]}..." if len(text) > 50 else f"Text input complete: {text}")
            return True
        
        except Exception as e:
            logging.error(f"Error inputting text: {e}")
            return False
    
    def press_enter(self):
        """Press Enter key."""
        try:
            # In actual implementation, use pyautogui.press
            # Here, return True as example
            logging.info("Enter key pressed")
            return True
        except Exception as e:
            logging.error(f"Error pressing Enter key: {e}")
            return False
    
    def click_continue_button(self):
        """Click 'Continue' button."""
        logging.info("Attempting to find 'Continue' button...")
        return self.find_and_click_image(self.continue_button_image)
    
    def click_new_chat_button(self):
        """Click 'New chat' button."""
        logging.info("Attempting to find 'New chat' button...")
        return self.find_and_click_image(self.new_chat_button_image)
    
    def setup_buttons(self):
        """Set up button images."""
        logging.info("Starting button image setup...")
        
        # Capture continue button
        logging.info("Please specify the 'Continue' button location.")
        self.capture_and_save_button("continue")
        
        # Capture new chat button
        logging.info("Please specify the 'New chat' button location.")
        self.capture_and_save_button("new_chat")
        
        logging.info("Button image setup complete.")
    
    def run_automation(self, input_text, wait_for_continue=True, create_new_chat=False):
        """Run automation task."""
        try:
            # Activate window
            if not self.activate_window():
                return False
            
            # Create new chat (if needed)
            if create_new_chat:
                if not self.click_new_chat_button():
                    logging.warning("Failed to create new chat, continuing anyway.")
                time.sleep(1)
            
            # Input text
            if not self.input_text(input_text):
                return False
            
            # Press Enter
            if not self.press_enter():
                return False
            
            # Wait for 'Continue' button (if needed)
            if wait_for_continue:
                logging.info("Waiting for 'Continue' button...")
                max_wait_time = 60  # Max 60 seconds wait
                wait_interval = 5   # Check every 5 seconds
                
                for _ in range(max_wait_time // wait_interval):
                    time.sleep(wait_interval)
                    if self.click_continue_button():
                        logging.info("'Continue' button clicked successfully")
                        break
                else:
                    logging.warning("'Continue' button not found. Timeout.")
            
            logging.info("Automation task complete")
            return True
        
        except Exception as e:
            logging.error(f"Error during automation task: {e}")
            return False


class TestRunner:
    def __init__(self, config_path=None):
        """Initialize test execution and monitoring class"""
        # Default configuration
        self.default_config = {
            "test_command": "pytest",
            "test_args": ["-v"],
            "max_retries": 5,
            "retry_delay": 2,
            "test_dir": "tests",
            "test_history_file": "test_history.json",
            "success_pattern": r"(\d+) passed",
            "failure_pattern": r"(\d+) failed",
            "error_pattern": r"(\d+) error"
        }
        
        # Load configuration file
        self.config = self.default_config.copy()
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    self.config.update(user_config)
                logging.info(f"Configuration file loaded: {config_path}")
            except Exception as e:
                logging.error(f"Failed to load configuration file: {e}")
        
        # Test history file path
        self.test_history_file = self.config["test_history_file"]
        
        # Load test history
        self.test_history = self._load_test_history()
        
        logging.info("Test runner initialization complete")
    
    def _load_test_history(self):
        """Load test history."""
        if os.path.exists(self.test_history_file):
            try:
                with open(self.test_history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Failed to load test history: {e}")
        
        # Default history structure
        return {
            "tasks": {},
            "last_run": None,
            "total_runs": 0,
            "total_passes": 0,
            "total_failures": 0
        }
    
    def _save_test_history(self):
        """Save test history."""
        try:
            with open(self.test_history_file, 'w') as f:
                json.dump(self.test_history, f, indent=2)
            logging.info(f"Test history saved: {self.test_history_file}")
            return True
        except Exception as e:
            logging.error(f"Failed to save test history: {e}")
            return False
    
    def run_tests(self, task_id=None, subtask_id=None, test_files=None):
        """Run tests and return results."""
        # Construct test command
        cmd = [self.config["test_command"]] + self.config["test_args"]
        
        # Run specific test files only
        if test_files:
            cmd.extend(test_files)
        else:
            cmd.append(self.config["test_dir"])
        
        try:
            # In actual implementation, use subprocess.Popen
            # Here, return dummy results as example
            
            # Dummy test results
            result = {
                "success": True,  # Test success status
                "return_code": 0,
                "success_count": 10,
                "failure_count": 0,
                "error_count": 0,
                "output": "10 passed, 0 failed, 0 error",
                "timestamp": time.time()
            }
            
            # Update test history
            self._update_test_history(task_id, subtask_id, result)
            
            logging.info(f"Test results: success={result['success_count']}, failure={result['failure_count']}, error={result['error_count']}")
            return result
        
        except Exception as e:
            logging.error(f"Error running tests: {e}")
            result = {
                "success": False,
                "return_code": -1,
                "success_count": 0,
                "failure_count": 0,
                "error_count": 0,
                "output": str(e),
                "timestamp": time.time()
            }
            
            # Update test history
            self._update_test_history(task_id, subtask_id, result)
            
            return result
    
    def _update_test_history(self, task_id, subtask_id, result):
        """Update test history."""
        # Update overall statistics
        self.test_history["total_runs"] += 1
        self.test_history["last_run"] = result["timestamp"]
        
        if result["success"]:
            self.test_history["total_passes"] += 1
        else:
            self.test_history["total_failures"] += 1
        
        # Update task/subtask history
        if task_id:
            if task_id not in self.test_history["tasks"]:
                self.test_history["tasks"][task_id] = {"subtasks": {}, "runs": 0, "passes": 0, "failures": 0}
            
            task_history = self.test_history["tasks"][task_id]
            task_history["runs"] += 1
            
            if result["success"]:
                task_history["passes"] += 1
            else:
                task_history["failures"] += 1
            
            # Update subtask history
            if subtask_id:
                if subtask_id not in task_history["subtasks"]:
                    task_history["subtasks"][subtask_id] = {"runs": 0, "passes": 0, "failures": 0, "last_result": None}
                
                subtask_history = task_history["subtasks"][subtask_id]
                subtask_history["runs"] += 1
                
                if result["success"]:
                    subtask_history["passes"] += 1
                else:
                    subtask_history["failures"] += 1
                
                subtask_history["last_result"] = {
                    "success": result["success"],
                    "success_count": result["success_count"],
                    "failure_count": result["failure_count"],
                    "error_count": result["error_count"],
                    "timestamp": result["timestamp"]
                }
        
        # Save history
        self._save_test_history()
    
    def get_failure_count(self, task_id, subtask_id):
        """Return consecutive failure count for specific task/subtask."""
        if task_id in self.test_history["tasks"]:
            task_history = self.test_history["tasks"][task_id]
            
            if subtask_id in task_history["subtasks"]:
                subtask_history = task_history["subtasks"][subtask_id]
                
                # Calculate consecutive failures
                consecutive_failures = 0
                for i in range(subtask_history["runs"]):
                    if i >= subtask_history["passes"]:
                        consecutive_failures += 1
                    else:
                        break
                
                return consecutive_failures
        
        return 0
    
    def run_until_success(self, task_id, subtask_id, test_files=None, max_retries=None, callback=None):
        """Run tests repeatedly until success."""
        if max_retries is None:
            max_retries = self.config["max_retries"]
        
        for attempt in range(max_retries):
            logging.info(f"Test attempt {attempt+1}/{max_retries}")
            
            # Run tests
            result = self.run_tests(task_id, subtask_id, test_files)
            
            # Exit on success
            if result["success"]:
                logging.info(f"Test success (attempt {attempt+1}/{max_retries})")
                return result
            
            # Call callback function (code modification, etc.)
            if callback:
                callback_result = callback(result, attempt)
                if not callback_result:
                    logging.warning(f"Callback function failed, stopping tests")
                    break
            
            # Wait before retry
            if attempt < max_retries - 1:
                time.sleep(self.config["retry_delay"])
        
        logging.error(f"Maximum retry count exceeded ({max_retries} attempts)")
        return result


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Claude Desktop automation and test execution')
    parser.add_argument('--setup', action='store_true', help='Initial setup mode')
    parser.add_argument('--prompt', type=str, help='Prompt to send to Claude')
    parser.add_argument('--test', action='store_true', help='Run tests')
    parser.add_argument('--task-id', type=str, help='Task ID')
    parser.add_argument('--subtask-id', type=str, help='Subtask ID')
    
    args = parser.parse_args()
    
    # Create Claude Desktop automation object
    claude = ClaudeDesktopAutomation()
    
    # Initial setup mode
    if args.setup:
        claude.setup_buttons()
        return
    
    # Send prompt
    if args.prompt:
        claude.run_automation(args.prompt)
    
    # Run tests
    if args.test:
        test_runner = TestRunner()
        result = test_runner.run_tests(args.task_id, args.subtask_id)
        print(f"Test results: {result}")


if __name__ == "__main__":
    main()
