import os
import json
import logging
import requests
import time
import re

class NotificationManager:
    def __init__(self, config_path=None):
        """Initialize notification manager class"""
        # Default configuration
        self.default_config = {
            "enabled": True,
            "slack": {
                "enabled": False,
                "webhook_url": "",
                "channel": "",
                "username": "Automation Bot"
            },
            "telegram": {
                "enabled": False,
                "bot_token": "",
                "chat_id": ""
            },
            "notification_cooldown": 300,  # 5 minutes
            "last_notification_time": {}
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
        
        logging.info("Notification manager initialization complete")
    
    def send_slack_notification(self, message, attachments=None):
        """Send notification to Slack."""
        if not self.config["enabled"] or not self.config["slack"]["enabled"]:
            logging.info("Slack notifications disabled")
            return False
        
        if not self.config["slack"]["webhook_url"]:
            logging.error("Slack webhook URL not configured")
            return False
        
        # Check cooldown
        notification_key = f"slack_{hash(message)}"
        last_time = self.config["last_notification_time"].get(notification_key, 0)
        current_time = time.time()
        
        if current_time - last_time < self.config["notification_cooldown"]:
            logging.info(f"Slack notification on cooldown (remaining: {int(self.config['notification_cooldown'] - (current_time - last_time))} seconds)")
            return False
        
        try:
            # Compose notification data
            payload = {
                "text": message,
                "username": self.config["slack"]["username"]
            }
            
            if self.config["slack"]["channel"]:
                payload["channel"] = self.config["slack"]["channel"]
            
            if attachments:
                payload["attachments"] = attachments
            
            # Send notification
            response = requests.post(
                self.config["slack"]["webhook_url"],
                json=payload
            )
            
            if response.status_code == 200:
                logging.info("Slack notification sent successfully")
                
                # Update last notification time
                self.config["last_notification_time"][notification_key] = current_time
                
                return True
            else:
                logging.error(f"Failed to send Slack notification: {response.status_code} {response.text}")
                return False
        
        except Exception as e:
            logging.error(f"Error sending Slack notification: {e}")
            return False
    
    def send_telegram_notification(self, message):
        """Send notification to Telegram."""
        if not self.config["enabled"] or not self.config["telegram"]["enabled"]:
            logging.info("Telegram notifications disabled")
            return False
        
        if not self.config["telegram"]["bot_token"] or not self.config["telegram"]["chat_id"]:
            logging.error("Telegram bot token or chat ID not configured")
            return False
        
        # Check cooldown
        notification_key = f"telegram_{hash(message)}"
        last_time = self.config["last_notification_time"].get(notification_key, 0)
        current_time = time.time()
        
        if current_time - last_time < self.config["notification_cooldown"]:
            logging.info(f"Telegram notification on cooldown (remaining: {int(self.config['notification_cooldown'] - (current_time - last_time))} seconds)")
            return False
        
        try:
            # Send notification
            url = f"https://api.telegram.org/bot{self.config['telegram']['bot_token']}/sendMessage"
            payload = {
                "chat_id": self.config["telegram"]["chat_id"],
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                logging.info("Telegram notification sent successfully")
                
                # Update last notification time
                self.config["last_notification_time"][notification_key] = current_time
                
                return True
            else:
                logging.error(f"Failed to send Telegram notification: {response.status_code} {response.text}")
                return False
        
        except Exception as e:
            logging.error(f"Error sending Telegram notification: {e}")
            return False
    
    def send_notification(self, message, title=None, severity="info", attachments=None):
        """Send notification to all enabled channels."""
        if not self.config["enabled"]:
            logging.info("Notification system disabled")
            return False
        
        # Add title
        if title:
            formatted_message = f"*{title}*\n{message}"
        else:
            formatted_message = message
        
        # Add icon based on severity
        if severity == "error":
            icon = "🚨"
        elif severity == "warning":
            icon = "⚠️"
        else:
            icon = "ℹ️"
        
        formatted_message = f"{icon} {formatted_message}"
        
        # Send to each channel
        results = []
        
        # Slack notification
        if self.config["slack"]["enabled"]:
            slack_result = self.send_slack_notification(formatted_message, attachments)
            results.append(slack_result)
        
        # Telegram notification
        if self.config["telegram"]["enabled"]:
            telegram_result = self.send_telegram_notification(formatted_message)
            results.append(telegram_result)
        
        # Success if at least one channel succeeded
        return any(results) if results else False
    
    def notify_subtask_failure(self, task_id, task_name, subtask_id, subtask_name, failure_count, error_message=None):
        """Send subtask failure notification."""
        title = f"Subtask Failure Alert (Attempt {failure_count})"
        message = f"Task: {task_name} ({task_id})\n"
        message += f"Subtask: {subtask_name} ({subtask_id})\n"
        message += f"Failure Count: {failure_count}\n"
        
        if error_message:
            message += f"Error Message: ```{error_message}```"
        
        return self.send_notification(message, title, "error")
    
    def notify_test_failure(self, task_id, subtask_id, test_result):
        """Send test failure notification."""
        title = "Test Failure Alert"
        message = f"Task: {task_id}\n"
        message += f"Subtask: {subtask_id}\n"
        
        # Safe dictionary access
        if isinstance(test_result, dict):
            message += f"Failed Tests: {test_result.get('failed_count', 0)}\n"
            message += f"Error Tests: {test_result.get('error_count', 0)}\n"
            
            # Extract failed test list (max 5)
            output = test_result.get("output", "")
            if output:
                failure_pattern = r"FAILED\s+([\w\.]+)::\w+\s+"
                failures = re.findall(failure_pattern, output)
                
                if failures:
                    message += "\nFailed Test List:\n"
                    for i, failure in enumerate(failures[:5]):
                        message += f"{i+1}. {failure}\n"
                    
                    if len(failures) > 5:
                        message += f"And {len(failures) - 5} more..."
        else:
            message += "Unable to parse test result information."
        
        return self.send_notification(message, title, "error")
    
    def notify_mock_detection(self, analysis_result):
        """Send code quality warning notification."""
        if analysis_result["total_mocks"] == 0 and analysis_result["total_commented_code"] == 0:
            return False
        
        title = "Code Quality Warning"
        message = ""
        
        if analysis_result["total_mocks"] > 0:
            message += f"Mock usage detected: {analysis_result['total_mocks']} instances ({analysis_result['files_with_mocks']} files)\n\n"
            
            # Top 3 files
            top_files = sorted(
                [f for f in analysis_result["details"] if f["mocks"]],
                key=lambda x: len(x["mocks"]),
                reverse=True
            )[:3]
            
            for file_result in top_files:
                message += f"- {file_result['file']}: {len(file_result['mocks'])} instances\n"
        
        if analysis_result["total_commented_code"] > 0:
            if message:
                message += "\n"
            
            message += f"Commented code detected: {analysis_result['total_commented_code']} blocks ({analysis_result['files_with_commented_code']} files)\n\n"
            
            # Top 3 files
            top_files = sorted(
                [f for f in analysis_result["details"] if f["commented_code"]],
                key=lambda x: len(x["commented_code"]),
                reverse=True
            )[:3]
            
            for file_result in top_files:
                message += f"- {file_result['file']}: {len(file_result['commented_code'])} blocks\n"
        
        return self.send_notification(message, title, "warning")
    
    def notify_task_completion(self, task_id, task_name):
        """Send task completion notification."""
        title = "Task Completion Alert"
        message = f"Task '{task_name}' ({task_id}) has been completed successfully."
        
        return self.send_notification(message, title, "info")


# Test code
if __name__ == "__main__":
    # Logging setup
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create notification manager
    notification_manager = NotificationManager()
    
    # Send test notification
    notification_manager.send_notification(
        "This is a test notification.",
        "Test Notification",
        "info"
    )
