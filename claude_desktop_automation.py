import pyautogui
import time
import os
import logging
import argparse
import json
from typing import Optional, Tuple
from datetime import datetime, timedelta
try:
    import pyperclip
except ImportError:
    pyperclip = None
try:
    from PIL import ImageGrab
    import numpy as np
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Create logs directory
LOGS_DIR = "logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Logging configuration
log_file_path = os.path.join(LOGS_DIR, "claude_automation.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("claude_automation")

class ClaudeDesktopAutomation:
    def __init__(self, config_path="claude_desktop_config.json", project_root_path="."):
        """
        Initialize Claude Desktop GUI automation class
        
        Args:
            config_path (str, optional): Configuration file path.
            project_root_path (str, optional): Project root path. Base for assets_dir relative paths.
        """
        self.default_config = {
            "window_title": "Claude",
            "input_delay": 0.5,
            "screenshot_delay": 1.0,
            "max_retries": 3,
            "confidence_threshold": 0.7,
            "assets_dir": "assets",
            "continue_button_image": "continue_button.png",
            "projects_button_image": "projects_button.png",
            "project_button_image": "project_button.png",
            "max_length_message_image": "max_length_message.png",
            "usage_limit_message_image": "usage_limit_message.png",
            "usage_limit_wait_hours": 2,
            "debug_usage_limit_wait_seconds": 10,
            "response_initial_wait_s": 30,
            "response_max_wait_s": 300,
            "response_check_interval_normal_s": 15,
            "response_check_interval_after_continue_s": 5,
            "response_quick_check_duration_s": 60,
            # Enhanced timeout settings
            "dynamic_timeout_enabled": True,
            "activity_detection_enabled": True,
            "progressive_interval_enabled": True,
            "max_wait_for_complex_tasks_s": 1800,  # 30 minutes for complex tasks
            "activity_timeout_extension_s": 300,    # Extend by 5 minutes on activity
            "max_check_interval_s": 60,            # Max interval between checks
            "activity_detection_threshold": 0.02    # 2% pixel change threshold
        }
        
        self.config = self.default_config.copy()
        self.config_file_path = os.path.abspath(config_path) # Absolute path of config file
        
        if os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, 'r') as f:
                    user_config = json.load(f)
                    self.config.update(user_config)
                logger.info(f"Configuration file loaded: {self.config_file_path}")
            except Exception as e:
                logger.error(f"Failed to load configuration file ({self.config_file_path}): {e}")
        else:
            logger.warning(f"Configuration file not found: {self.config_file_path}. Using default configuration.")

        # Process assets_dir: if path in config is not absolute, combine with config file directory
        if not os.path.isabs(self.config["assets_dir"]):
            self.assets_dir = os.path.join(os.path.dirname(self.config_file_path), self.config["assets_dir"])
        else:
            self.assets_dir = self.config["assets_dir"]
        
        if not os.path.exists(self.assets_dir):
            try:
                os.makedirs(self.assets_dir)
                logger.info(f"Assets directory created: {self.assets_dir}")
            except OSError as e:
                logger.error(f"Failed to create assets directory ({self.assets_dir}): {e}. Image-based automation may fail.")
                # Fallback to current directory's 'assets' if creation fails
                self.assets_dir = os.path.join(os.getcwd(), "assets")
                if not os.path.exists(self.assets_dir):
                    os.makedirs(self.assets_dir, exist_ok=True)


        self.continue_button_image = os.path.join(self.assets_dir, self.config["continue_button_image"])
        self.usage_limit_message_image_path = os.path.join(self.assets_dir, self.config["usage_limit_message_image"])
        self.max_length_message_image_path = os.path.join(self.assets_dir, self.config["max_length_message_image"])
        self.projects_button_image_path = os.path.join(self.assets_dir, self.config["projects_button_image"])
        
        # Check required images
        self._check_required_images()
        
        self.window_active = False
        self.last_screenshot = None
        self.task_complexity_score = 5  # Default complexity score
        logger.info("Claude Desktop automation initialization complete")
    
    def _check_required_images(self):
        """Check if required image files exist"""
        required_images_config_keys = [
            "continue_button_image",
            "projects_button_image",
            "max_length_message_image",
            "usage_limit_message_image"
        ]
        
        missing_images = []
        for key in required_images_config_keys:
            filename = self.config.get(key)
            if not filename:
                missing_images.append(f"{key} (config key missing)")
                continue
            image_path = os.path.join(self.assets_dir, filename)
            if not os.path.exists(image_path):
                missing_images.append(filename)
        
        if missing_images:
            logger.warning(f"The following image files/configs are missing: {', '.join(missing_images)}")
            logger.warning(f"Please add images to '{self.assets_dir}' or use --setup to capture them.")
            logger.warning(f"See {os.path.join(self.assets_dir, 'CAPTURE_GUIDE.md')} for details.")
    
    def set_task_complexity(self, complexity_score: int):
        """Set task complexity score (1-10) to adjust timeouts accordingly"""
        self.task_complexity_score = max(1, min(10, complexity_score))
        logger.info(f"Task complexity set to: {self.task_complexity_score}/10")
    
    def activate_window(self):
        try:
            windows = pyautogui.getWindowsWithTitle(self.config["window_title"])
            if windows:
                window = windows[0]
                if not window.isActive: # Don't reactivate if already active
                    window.activate()
                if not window.isMaximized: # Maximize if not already maximized (optional)
                    window.maximize()
                time.sleep(1) 
                self.window_active = True
                logger.info(f"'{self.config['window_title']}' window activated successfully")
                return True
            else:
                logger.error(f"'{self.config['window_title']}' window not found.")
                return False
        except Exception as e:
            logger.error(f"Error activating window: {e}")
            return False
    
    def find_and_click_image(self, image_path, max_retries=None, confidence=None):
        if max_retries is None:
            max_retries = self.config["max_retries"]
        if confidence is None:
            confidence = self.config["confidence_threshold"]
        
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            logger.error(f"Please add images to assets folder or use --setup option to capture them.")
            return False
        
        for attempt in range(max_retries):
            try:
                # pyautogui.locateCenterOnScreen searches entire screen
                # To search only within active window, additional logic needed (e.g., capture window area first)
                # Using simple full screen search here
                location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
                if location:
                    pyautogui.click(location)
                    logger.info(f"Image clicked successfully: {image_path} at {location}")
                    return True
                else:
                    logger.warning(f"Image not found on screen ({attempt+1}/{max_retries}): {image_path}")
                    time.sleep(self.config["screenshot_delay"])
            except pyautogui.PyAutoGUIException as e: # PyAutoGUI specific exceptions
                logger.error(f"PyAutoGUI error while finding/clicking image ({image_path}): {e}")
                time.sleep(self.config["screenshot_delay"])
            except Exception as e: # Other exceptions
                logger.error(f"Unexpected error while finding/clicking image ({image_path}): {e}")
                time.sleep(self.config["screenshot_delay"])
        
        logger.error(f"Failed to find image (max retries exceeded): {image_path}")
        return False
    
    def _detect_screen_activity(self) -> bool:
        """Detect if Claude is still actively working by checking screen changes"""
        if not PIL_AVAILABLE:
            logger.debug("PIL not available, activity detection disabled")
            return False
            
        if not self.config.get("activity_detection_enabled", True):
            return False
            
        try:
            # Take screenshot
            current_screenshot = ImageGrab.grab()
            current_array = np.array(current_screenshot)
            
            if self.last_screenshot is not None:
                # Calculate difference between screenshots
                diff = np.abs(current_array.astype(float) - self.last_screenshot.astype(float))
                change_ratio = np.sum(diff > 30) / diff.size  # Pixels with significant change
                
                logger.debug(f"Screen change ratio: {change_ratio:.4f}")
                
                # If change is above threshold, Claude is still working
                if change_ratio > self.config.get("activity_detection_threshold", 0.02):
                    logger.info("Activity detected - Claude is still working")
                    self.last_screenshot = current_array
                    return True
            
            self.last_screenshot = current_array
            return False
            
        except Exception as e:
            logger.error(f"Error in activity detection: {e}")
            return False
    
    def _calculate_check_interval(self, elapsed_time: int, base_interval: int) -> int:
        """Calculate progressive check interval based on elapsed time"""
        if not self.config.get("progressive_interval_enabled", True):
            return base_interval
            
        # Progressive interval: increases as time passes
        # First 5 minutes: base interval
        # 5-15 minutes: 1.5x base interval
        # 15-30 minutes: 2x base interval
        # 30+ minutes: 3x base interval (capped at max_check_interval)
        
        if elapsed_time < 300:  # < 5 minutes
            multiplier = 1.0
        elif elapsed_time < 900:  # < 15 minutes
            multiplier = 1.5
        elif elapsed_time < 1800:  # < 30 minutes
            multiplier = 2.0
        else:
            multiplier = 3.0
            
        interval = int(base_interval * multiplier)
        max_interval = self.config.get("max_check_interval_s", 60)
        
        return min(interval, max_interval)
    
    def _calculate_dynamic_timeout(self) -> int:
        """Calculate dynamic timeout based on task complexity"""
        base_timeout = self.config.get("response_max_wait_s", 300)
        complex_timeout = self.config.get("max_wait_for_complex_tasks_s", 1800)
        
        if not self.config.get("dynamic_timeout_enabled", True):
            return base_timeout
            
        # Linear interpolation based on complexity score (1-10)
        # Score 1-3: base timeout
        # Score 4-7: interpolated
        # Score 8-10: complex timeout
        
        if self.task_complexity_score <= 3:
            return base_timeout
        elif self.task_complexity_score >= 8:
            return complex_timeout
        else:
            # Linear interpolation
            ratio = (self.task_complexity_score - 3) / 5.0
            return int(base_timeout + (complex_timeout - base_timeout) * ratio)
    
    def capture_and_save_button(self, button_name_key, image_file_name, prompt_message):
        """
        Capture a specific area of the screen and save as button image.
        
        Args:
            button_name_key (str): Button name key to use in config (e.g., "continue_button_image")
            image_file_name (str): Image file name to save (e.g., "continue_button.png")
            prompt_message (str): Message to guide user
        """
        try:
            logger.info(prompt_message)
            logger.info("Please hover mouse over the button to capture and wait 5 seconds...")
            time.sleep(5)
            x, y = pyautogui.position()
            
            # Capture area around button (could be improved to allow user to adjust size)
            # Example: 100px width, 50px height area
            # More accurate would be to let user drag to select area
            logger.info("Specify button area. First click: top-left, Second click: bottom-right (within 10 seconds)")
            
            # Simple fixed-size capture for simplicity
            # Could use pyautogui.prompt or tkinter for more sophisticated UI
            capture_width = 150 
            capture_height = 60
            region = (x - capture_width // 2, y - capture_height // 2, capture_width, capture_height)
            
            screenshot = pyautogui.screenshot(region=region)
            
            image_path = os.path.join(self.assets_dir, image_file_name)
            screenshot.save(image_path)
            logger.info(f"'{image_file_name}' button image saved: {image_path}")
            
            # Optionally update config file with saved image filename
            # self.config[button_name_key] = image_file_name
            # with open(self.config_file_path, 'w') as f:
            #     json.dump(self.config, f, indent=2)
            # logger.info(f"Configuration file updated: {self.config_file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error capturing button ({image_file_name}): {e}")
            return False
    
    def input_text(self, text):
        if not self.window_active:
            if not self.activate_window():
                return False
        try:
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.press('delete')
            time.sleep(0.1)
            
            # Use clipboard for long text input for better reliability
            if pyperclip and len(text) > 100:
                pyperclip.copy(text)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.2)
                logger.info(f"Text input complete via clipboard (first 50 chars): {text[:50]}...")
            else:
                pyautogui.write(text, interval=0.01)
                logger.info(f"Text input complete (first 50 chars): {text[:50]}...")
            
            return True
        except Exception as e:
            logger.error(f"Error inputting text: {e}")
            return False
    
    def press_enter(self):
        if not self.window_active: # Check window activation before Enter
            if not self.activate_window():
                logger.warning("Failed to activate window before pressing Enter.")
                # Policy needed: fail or continue
        try:
            pyautogui.press('enter')
            logger.info("Enter key pressed")
            return True
        except Exception as e:
            logger.error(f"Error pressing Enter key: {e}")
            return False
    
    def click_continue_button(self):
        logger.info(f"Attempting to find 'Continue' button ({self.config['continue_button_image']})...")
        return self.find_and_click_image(self.continue_button_image)
    
    def check_image_on_screen(self, image_path, confidence=None) -> bool:
        """Checks if an image is present on the screen."""
        if confidence is None:
            confidence = self.config["confidence_threshold"]
        if not os.path.exists(image_path):
            logger.debug(f"Image file not found for check: {image_path}")
            return False
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            return location is not None
        except pyautogui.PyAutoGUIException as e:
            logger.error(f"PyAutoGUI error checking image {image_path}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error checking image {image_path}: {e}")
        return False

    def check_usage_limit_message(self) -> bool:
        """Check if usage limit message is displayed."""
        logger.debug(f"Checking for usage limit message: {self.usage_limit_message_image_path}")
        return self.check_image_on_screen(self.usage_limit_message_image_path)
    
    def check_max_length_message(self) -> bool:
        """Check if max length message is displayed on screen"""
        max_length_image = os.path.join(self.assets_dir, self.config.get("max_length_message_image", "max_length_message.png"))
        if os.path.exists(max_length_image):
            try:
                location = pyautogui.locateOnScreen(max_length_image, confidence=self.config["confidence_threshold"])
                if location:
                    logger.info("Max length message detected")
                    return True
            except Exception as e:
                logger.error(f"Error checking max length message: {e}")
        return False
    
    def click_projects_button(self):
        """Click Projects button"""
        projects_button_image = os.path.join(self.assets_dir, self.config.get("projects_button_image", "projects_button.png"))
        logger.info(f"Attempting to find 'Projects' button ({projects_button_image})...")
        return self.find_and_click_image(projects_button_image)
    
    def click_project_button(self, project_name):
        """Click specific project button"""
        project_button_image = os.path.join(self.assets_dir, f"{project_name}_button.png")
        if not os.path.exists(project_button_image):
            # Use generic project button image
            project_button_image = os.path.join(self.assets_dir, self.config.get("project_button_image", "project_button.png"))
        
        logger.info(f"Attempting to find '{project_name}' project button ({project_button_image})...")
        return self.find_and_click_image(project_button_image)
    
    def create_new_chat_via_projects(self, project_name: str) -> bool:
        """Create new chat through Projects for the given project name."""
        logger.info(f"Creating new chat via Projects for project: '{project_name}'")
        
        # 1. Click Projects button
        if not self.click_projects_button():
            logger.error("Projects button not found.")
            return False
        
        time.sleep(1)  # Wait for Projects menu to load
        
        # 2. Click project button
        if not self.click_project_button(project_name):
            logger.error(f"{project_name} project button not found.")
            return False
        
        time.sleep(2)  # Wait for project to load
        logger.info(f"New chat ready in '{project_name}' project")
        return True
    
    def handle_max_length(self, project_name):
        """Handle max length situation - create new chat using same logic"""
        return self.create_new_chat_via_projects(project_name)
    
    def click_new_chat_button(self):
        # Deprecated: Now using Projects for new chat creation
        logger.warning("click_new_chat_button is deprecated. Use create_new_chat_via_projects instead.")
        return False
    
    def _wait_for_response_core(self, project_name_for_new_chat: str, wait_for_continue_flag: bool) -> str:
        """
        Enhanced core logic for waiting for Claude's response with dynamic timeout and activity detection.
        Returns a status string: "success", "usage_limit_reached", "max_length_handled", "timeout", "failure".
        """
        logger.info("Waiting for Claude's response...")
        
        # Calculate dynamic timeout based on task complexity
        max_wait_total = self._calculate_dynamic_timeout()
        logger.info(f"Dynamic timeout set to {max_wait_total}s based on task complexity: {self.task_complexity_score}/10")
        
        # Timing parameters from config
        initial_wait = self.config.get("response_initial_wait_s", 30)
        check_interval_normal = self.config.get("response_check_interval_normal_s", 15)
        check_interval_after_continue = self.config.get("response_check_interval_after_continue_s", 5)
        quick_check_duration_after_continue = self.config.get("response_quick_check_duration_s", 60)
        activity_extension = self.config.get("activity_timeout_extension_s", 300)

        time.sleep(initial_wait)
        elapsed_time = initial_wait
        
        last_continue_click_time = 0
        continue_clicked_this_cycle = False
        last_activity_time = elapsed_time
        extended_timeout = max_wait_total

        while elapsed_time < extended_timeout:
            # 1. Check for Usage Limit (highest priority)
            if self.check_usage_limit_message():
                logger.warning("Usage limit message detected on screen.")
                return "usage_limit_reached"

            # 2. Check for Max Length
            if self.check_max_length_message():
                logger.warning("Max length message detected on screen.")
                if not project_name_for_new_chat:
                    logger.error("Project name not provided, cannot handle max length by creating new chat.")
                    return "failure"
                if self.create_new_chat_via_projects(project_name_for_new_chat):
                    logger.info("Successfully created new chat to handle max length.")
                    return "max_length_handled"
                else:
                    logger.error("Failed to create new chat to handle max length.")
                    return "failure"

            # 3. Check for Continue button (if applicable)
            if wait_for_continue_flag:
                if self.find_and_click_image(self.continue_button_image, max_retries=1):
                    logger.info("'Continue' button clicked.")
                    continue_clicked_this_cycle = True
                    last_continue_click_time = elapsed_time
                    # Reset activity detection after continue click
                    self.last_screenshot = None
                elif continue_clicked_this_cycle:
                    logger.info("Response generation appears complete after 'Continue' button.")
                    return "success"
            
            # 4. Activity detection - check if Claude is still working
            if self._detect_screen_activity():
                last_activity_time = elapsed_time
                # Extend timeout if activity detected and we're close to timeout
                if elapsed_time > extended_timeout * 0.8:  # Within 80% of timeout
                    extended_timeout = min(
                        elapsed_time + activity_extension,
                        max_wait_total * 2  # Never exceed 2x original timeout
                    )
                    logger.info(f"Activity detected - extending timeout to {extended_timeout}s")
            
            # Calculate progressive check interval
            base_interval = check_interval_after_continue \
                           if continue_clicked_this_cycle and (elapsed_time - last_continue_click_time < quick_check_duration_after_continue) \
                           else check_interval_normal
            
            current_interval = self._calculate_check_interval(elapsed_time, base_interval)
            
            # Log progress every 5 checks or every 5 minutes
            if elapsed_time % 300 < current_interval:
                progress_pct = (elapsed_time / extended_timeout) * 100
                logger.info(f"Progress: {elapsed_time}s / {extended_timeout}s ({progress_pct:.1f}%) - "
                          f"Last activity: {elapsed_time - last_activity_time}s ago")
            
            logger.debug(f"Waiting for {current_interval}s... (Total elapsed: {elapsed_time}s)")
            time.sleep(current_interval)
            elapsed_time += current_interval

        # Check if we should consider it successful based on activity
        if last_activity_time > extended_timeout * 0.9:  # Activity in last 10% of time
            logger.info("Recent activity detected - assuming task completion")
            return "success"
            
        if not wait_for_continue_flag and not continue_clicked_this_cycle:
            logger.info("Short prompt response assumed complete.")
            return "success"
            
        if continue_clicked_this_cycle:
            logger.info("Response generation complete (final 'Continue' button likely processed).")
            return "success"

        logger.warning(f"Response timeout after {extended_timeout} seconds (no recent activity for {elapsed_time - last_activity_time}s).")
        return "timeout"
    
    def get_token_info(self) -> dict:
        """Get current token usage information"""
        return {
            'current_tokens': self.current_conversation_tokens,
            'max_tokens': self.max_tokens_per_conversation,
            'percentage_used': (self.current_conversation_tokens / self.max_tokens_per_conversation) * 100,
            'interaction_count': self.interaction_count,
            'interaction_threshold': self.interaction_count_threshold
        }
    
    def reset_conversation_tracking(self):
        """Reset token and interaction tracking"""
        self.current_conversation_tokens = 0
        self.interaction_count = 0
        self.current_conversation_summary = ""
        logger.info("Conversation tracking reset")
    
    def setup_buttons(self):
        logger.info("Starting button image setup...")
        logger.info("TIP: You can skip this step if you already have captured images.")
        
        if not self.activate_window():
            logger.error("Cannot activate Claude window. Unable to proceed with button setup.")
            return

        # Check existing images and capture buttons
        buttons_to_capture = [
            ("continue_button_image", self.config["continue_button_image"], "'Continue' button"),
            ("projects_button_image", self.config.get("projects_button_image", "projects_button.png"), "'Projects' button (top left)"),
            ("max_length_message_image", self.config.get("max_length_message_image", "max_length_message.png"), "'Max length' message (bottom)"),
            ("usage_limit_message_image", self.config.get("usage_limit_message_image", "usage_limit_message.png"), "Usage limit message (e.g., '...try again in 2 hours')")
        ]
        
        for config_key, filename, description in buttons_to_capture:
            image_path = os.path.join(self.assets_dir, filename)
            if os.path.exists(image_path):
                response = input(f"{filename} already exists. Overwrite? (y/N): ").strip().lower()
                if response != 'y':
                    logger.info(f"Skipping {filename} capture.")
                    continue
            
            self.capture_and_save_button(config_key, filename, description)
        
        # Project button (optional)
        project_name = input("Enter project name (optional, press Enter to skip): ").strip()
        if project_name:
            project_filename = f"{project_name}_button.png"
            project_image_path = os.path.join(self.assets_dir, project_filename)
            if os.path.exists(project_image_path):
                response = input(f"{project_filename} already exists. Overwrite? (y/N): ").strip().lower()
                if response == 'y':
                    self.capture_and_save_button(
                        f"{project_name}_button_image",
                        project_filename,
                        f"'{project_name}' project button"
                    )
            else:
                self.capture_and_save_button(
                    f"{project_name}_button_image",
                    project_filename,
                    f"'{project_name}' project button"
                )
        
        logger.info("Button image setup complete.")
        logger.info(f"Images saved in {self.assets_dir}.")
    
    def run_automation(self, input_text_content: str, wait_for_continue: bool = True, create_new_chat: bool = False, 
                      project_name: Optional[str] = None, task_complexity: Optional[int] = None):
        if not self.activate_window():
            return False

        if not project_name:
            logger.error("Project name is required for Claude Desktop automation.")
            return False

        # Set task complexity if provided
        if task_complexity is not None:
            self.set_task_complexity(task_complexity)

        max_usage_limit_retries = 1
        usage_limit_retry_count = 0

        # Initial new chat creation if requested
        if create_new_chat:
            logger.info("Explicit request to create a new chat at the beginning.")
            if not self.create_new_chat_via_projects(project_name):
                logger.error("Failed to create initial new chat as requested.")
                return False
        
        while usage_limit_retry_count <= max_usage_limit_retries:
            if usage_limit_retry_count > 0:
                logger.info(f"Retrying after usage limit. Attempt {usage_limit_retry_count}/{max_usage_limit_retries}.")
                if not self.create_new_chat_via_projects(project_name):
                    logger.error("Failed to create new chat for retry. Aborting task.")
                    return False

            if not self.input_text(input_text_content):
                return False
            
            if not self.press_enter():
                return False
            
            response_status = self._wait_for_response_core(project_name, wait_for_continue)

            if response_status == "success":
                logger.info("Automation for the current prompt completed successfully.")
                return True
            elif response_status == "usage_limit_reached":
                if usage_limit_retry_count < max_usage_limit_retries:
                    wait_duration_hours = self.config.get("usage_limit_wait_hours", 2)
                    wait_duration_seconds = wait_duration_hours * 60 * 60
                    
                    # For testing, allow shorter wait via config
                    if "debug_usage_limit_wait_seconds" in self.config:
                        test_wait_seconds = self.config.get("debug_usage_limit_wait_seconds", 10)
                        logger.warning(f"DEBUG: Short wait of {test_wait_seconds}s instead of {wait_duration_hours}h for usage limit.")
                        time.sleep(test_wait_seconds)
                    else:
                        logger.info(f"Usage limit reached. Waiting for {wait_duration_hours} hours before retrying...")
                        time.sleep(wait_duration_seconds)

                    usage_limit_retry_count += 1
                else:
                    logger.error("Usage limit reached and max retries exceeded. Aborting.")
                    return False
            elif response_status == "max_length_handled":
                logger.warning("Max length reached; new chat is ready with context preserved.")
                # Continue with the same prompt in the new chat
                if self.input_text(input_text_content):
                    self.press_enter()
                    response_status = self._wait_for_response_core(project_name, wait_for_continue)
                    if response_status == "success":
                        return True
                return False
            elif response_status == "failure" or response_status == "timeout":
                logger.error(f"Response handling failed or timed out ({response_status}).")
                return False
            else:
                logger.error(f"Unknown status from _wait_for_response_core: {response_status}")
                return False
        
        logger.error("Exited usage limit retry loop without success.")
        return False

def main():
    parser = argparse.ArgumentParser(description='Claude Desktop GUI Automation Tool')
    parser.add_argument('--config', type=str, default="claude_desktop_config.json", help='Claude automation configuration file path')
    parser.add_argument('--project-root', type=str, default=".", help='Project root path (base for assets relative paths)')
    parser.add_argument('--project-name', type=str, help='Claude project name')
    parser.add_argument('--setup', action='store_true', help='Button image setup mode')
    parser.add_argument('--input', type=str, help='Text to input or text file path')
    parser.add_argument('--wait-continue', action='store_true', help="Wait for and click 'Continue' button (for long responses)")
    parser.add_argument('--new-chat', action='store_true', help='Create new chat before inputting prompt')
    parser.add_argument('--task-complexity', type=int, choices=range(1, 11), help='Task complexity score (1-10) for dynamic timeout')
    
    args = parser.parse_args()
    
    automation = ClaudeDesktopAutomation(config_path=args.config, project_root_path=args.project_root)
    
    if args.setup:
        automation.setup_buttons()
        return
    
    # Check required images when not in setup mode
    if not args.project_name:
        logger.error("--project-name is required when not in --setup mode.")
        return
    
    required_images = [
        automation.continue_button_image,
        os.path.join(automation.assets_dir, automation.config.get("projects_button_image", "projects_button.png")),
        os.path.join(automation.assets_dir, automation.config.get("max_length_message_image", "max_length_message.png")),
        os.path.join(automation.assets_dir, automation.config.get("usage_limit_message_image", "usage_limit_message.png"))
    ]
    
    missing_images = [img for img in required_images if not os.path.exists(img)]
    if missing_images:
        logger.error(f"Required image files are missing: {', '.join(missing_images)}")
        logger.error("Please do one of the following:")
        logger.error("1. Add necessary image files to assets folder")
        logger.error("2. Run python claude_desktop_automation.py --setup to capture images")
        return
    
    input_text_content = ""
    if args.input:
        if os.path.isfile(args.input):
            try:
                with open(args.input, 'r', encoding='utf-8') as f:
                    input_text_content = f.read()
                logger.info(f"Text loaded from file: {args.input}")
            except Exception as e:
                logger.error(f"Failed to read input file ({args.input}): {e}")
                return
        else:
            input_text_content = args.input
    
    if not input_text_content:
        logger.error("No input text provided. Please provide text or file path with --input argument.")
        return
    
    success = automation.run_automation(
        input_text_content=input_text_content,
        wait_for_continue=args.wait_continue,
        create_new_chat=args.new_chat,
        project_name=args.project_name,
        task_complexity=args.task_complexity
    )

    if success:
        logger.info("Automation run completed successfully.")
    else:
        logger.error("Automation run failed or was aborted.")

if __name__ == "__main__":
    main()
