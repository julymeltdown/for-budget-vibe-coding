import os
import sys
import logging
import argparse
import json
import time
import subprocess # Needed for TestRunner and git_commit
import re # Needed for TestRunner
import platform # For OS detection
from datetime import datetime

# Set module import path based on current file's directory (optional, better to use PYTHONPATH or packaging)
# sys.path.append(os.path.dirname(os.path.abspath(__file__))) # May be unnecessary with current structure

from claude_desktop_automation import ClaudeDesktopAutomation # Updated import
from code_analyzer import CodeAnalyzer
from notification_manager import NotificationManager
from task_master_mcp_client import TaskMasterMCPClient

# Create logs directory
LOGS_DIR = "logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Logging configuration
log_file_path = os.path.join(LOGS_DIR, "automation_orchestrator.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("orchestrator")


# TestRunner class integrated here or can be split into separate file
# Integrated form provided here (separate test_runner.py file recommended)
class TestRunner:
    def __init__(self, test_config=None, project_root=".", project_type=None): # project_type added
        self.default_config = {
            "test_command": "pytest", # or "mvn test", "npm test", etc.
            "test_args": ["-v"],
            "test_dir": "tests", # relative path from project_root
            "success_pattern": r"(\d+)\s+(?:passed|test(?:s)? ran)", # considers pytest, junit, etc.
            "failure_pattern": r"(\d+)\s+failed",
            "error_pattern": r"(\d+)\s+error(?:s)?", # pytest has errors, junit may include in failures
            "test_history_file": os.path.join(LOGS_DIR, "test_history.json") # saved in logs directory
        }
        self.config = self.default_config.copy()
        if test_config: # allows external config injection
            self.config.update(test_config)

        self.project_root = os.path.abspath(project_root)
        self.project_type = project_type
        
        # OS detection
        self.is_windows = platform.system() == "Windows"
        
        # Adjust test_command based on project_type
        if self.project_type == "gradle" and self.is_windows:
            # Use gradlew.bat on Windows
            if "test_command_windows" in self.config:
                self.config["test_command"] = self.config["test_command_windows"]
        elif self.project_type == "maven" and self.is_windows:
            # Use mvn.cmd on Windows
            if "test_command_windows" in self.config:
                self.config["test_command"] = self.config["test_command_windows"]
                
        # Check and set gradle/gradlew path
        if self.project_type == "gradle":
            gradlew_path = os.path.join(self.project_root, self.config["test_command"])
            if os.path.exists(gradlew_path):
                self.config["test_command"] = gradlew_path
                # Grant execution permission (Unix-like systems)
                if not self.is_windows:
                    try:
                        os.chmod(gradlew_path, 0o755)
                    except Exception as e:
                        logger.warning(f"Failed to set gradlew execution permissions: {e}")
        
        self.test_dir_abs = os.path.join(self.project_root, self.config["test_dir"]) if self.config.get("test_dir") else self.project_root
        
        self.test_history = self._load_test_history()
        logger.info(f"TestRunner initialization complete (project type: {self.project_type})")

    def _load_test_history(self):
        if os.path.exists(self.config["test_history_file"]):
            try:
                with open(self.config["test_history_file"], 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load test history: {e}")
        return {"tasks": {}, "last_run": None, "total_runs": 0, "total_passes": 0, "total_failures": 0}

    def _save_test_history(self):
        try:
            with open(self.config["test_history_file"], 'w') as f:
                json.dump(self.test_history, f, indent=2)
            logger.info(f"Test history saved: {self.config['test_history_file']}")
        except Exception as e:
            logger.error(f"Failed to save test history: {e}")

    def run_tests(self, task_id=None, subtask_id=None, specific_test_files=None):
        # test_command가 'mvn' 등을 포함할 수 있으므로, config에서 test