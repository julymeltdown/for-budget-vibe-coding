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
        """
        Run tests and return results
        """
        try:
            # test_command가 'mvn' 등을 포함할 수 있으므로, config에서 test command 구성
            cmd = [self.config["test_command"]] + self.config["test_args"]
            
            # specific_test_files가 제공되면 해당 파일들만 테스트
            if specific_test_files:
                cmd.extend(specific_test_files)
            
            logger.info(f"Running tests with command: {' '.join(cmd)}")
            logger.info(f"Working directory: {self.project_root}")
            
            # Run tests
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            output = result.stdout + result.stderr
            success = result.returncode == 0
            
            # Parse test results
            passes = self._extract_count(output, self.config["success_pattern"])
            failures = self._extract_count(output, self.config["failure_pattern"])
            errors = self._extract_count(output, self.config["error_pattern"])
            
            test_result = {
                "task_id": task_id,
                "subtask_id": subtask_id,
                "timestamp": time.time(),
                "success": success,
                "exit_code": result.returncode,
                "output": output,
                "passes": passes,
                "failures": failures,
                "errors": errors,
                "command": " ".join(cmd)
            }
            
            # Update test history
            self._update_test_history(test_result)
            
            logger.info(f"Test results - Success: {success}, Passes: {passes}, Failures: {failures}, Errors: {errors}")
            
            return test_result
            
        except subprocess.TimeoutExpired:
            error_result = {
                "task_id": task_id,
                "subtask_id": subtask_id,
                "timestamp": time.time(),
                "success": False,
                "exit_code": -1,
                "output": "Test execution timed out after 5 minutes",
                "passes": 0,
                "failures": 1,
                "errors": 0,
                "command": " ".join(cmd) if 'cmd' in locals() else "unknown"
            }
            self._update_test_history(error_result)
            logger.error("Test execution timed out")
            return error_result
            
        except Exception as e:
            error_result = {
                "task_id": task_id,
                "subtask_id": subtask_id,
                "timestamp": time.time(),
                "success": False,
                "exit_code": -1,
                "output": f"Test execution failed: {str(e)}",
                "passes": 0,
                "failures": 1,
                "errors": 0,
                "command": " ".join(cmd) if 'cmd' in locals() else "unknown"
            }
            self._update_test_history(error_result)
            logger.error(f"Failed to run tests: {e}")
            return error_result

    def _extract_count(self, output, pattern):
        """Extract count from test output using regex pattern"""
        try:
            matches = re.findall(pattern, output, re.IGNORECASE)
            if matches:
                return int(matches[-1])  # Take the last match
            return 0
        except Exception as e:
            logger.warning(f"Failed to extract count with pattern '{pattern}': {e}")
            return 0

    def _update_test_history(self, test_result):
        """Update test history with new result"""
        try:
            task_key = f"task_{test_result['task_id']}"
            if test_result['subtask_id']:
                task_key += f"_subtask_{test_result['subtask_id']}"
            
            if task_key not in self.test_history["tasks"]:
                self.test_history["tasks"][task_key] = []
            
            self.test_history["tasks"][task_key].append(test_result)
            
            # Keep only last 10 results per task
            if len(self.test_history["tasks"][task_key]) > 10:
                self.test_history["tasks"][task_key] = self.test_history["tasks"][task_key][-10:]
            
            # Update global statistics
            self.test_history["last_run"] = test_result["timestamp"]
            self.test_history["total_runs"] += 1
            self.test_history["total_passes"] += test_result["passes"]
            self.test_history["total_failures"] += test_result["failures"]
            
            self._save_test_history()
            
        except Exception as e:
            logger.error(f"Failed to update test history: {e}")

    def get_test_summary(self, task_id=None):
        """Get test summary for a specific task or all tasks"""
        try:
            if task_id:
                task_key = f"task_{task_id}"
                return self.test_history["tasks"].get(task_key, [])
            else:
                return self.test_history
        except Exception as e:
            logger.error(f"Failed to get test summary: {e}")
            return []


class TaskOrchestrator:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self.tasks_data = self._load_tasks_data()
        self.test_runner = TestRunner(
            test_config=self.config.get("test_config"),
            project_root=self.config.get("dev_project_path", "."),
            project_type=self.config.get("project_type")
        )
        self.code_analyzer = CodeAnalyzer()
        self.notification_manager = NotificationManager()
        logger.info("TaskOrchestrator initialized")

    def _load_config(self):
        """Load configuration from file"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {self.config_file}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return {}

    def _load_tasks_data(self):
        """Load tasks data from tasks.json"""
        try:
            tasks_file = "tasks.json"
            if os.path.exists(tasks_file):
                with open(tasks_file, 'r') as f:
                    return json.load(f)
            logger.warning(f"Tasks file {tasks_file} not found")
            return {"tasks": []}
        except Exception as e:
            logger.error(f"Failed to load tasks data: {e}")
            return {"tasks": []}

    def _save_tasks_data(self):
        """Save tasks data to tasks.json"""
        try:
            with open("tasks.json", 'w') as f:
                json.dump(self.tasks_data, f, indent=2)
            logger.info("Tasks data saved")
            return True
        except Exception as e:
            logger.error(f"Failed to save tasks data: {e}")
            return False

    def get_task_by_id(self, task_id):
        """Get task by ID"""
        for task in self.tasks_data.get("tasks", []):
            if str(task.get("id")) == str(task_id):
                return task
        return None

    def get_subtask_by_id(self, task, subtask_id):
        """Get subtask by ID within a task"""
        for subtask in task.get("subtasks", []):
            if str(subtask.get("id")) == str(subtask_id):
                return subtask
        return None

    def run_task_tests(self, task_id=None, subtask_id=None):
        """Run tests for a specific task or subtask"""
        try:
            result = self.test_runner.run_tests(
                task_id=task_id,
                subtask_id=subtask_id
            )
            
            # Update task status based on test results
            if task_id:
                task = self.get_task_by_id(task_id)
                if task:
                    if result["success"]:
                        if subtask_id:
                            subtask = self.get_subtask_by_id(task, subtask_id)
                            if subtask:
                                subtask["status"] = "completed"
                                subtask["completed_at"] = datetime.now().isoformat()
                        else:
                            task["status"] = "completed"
                            task["completed_at"] = datetime.now().isoformat()
                    else:
                        if subtask_id:
                            subtask = self.get_subtask_by_id(task, subtask_id)
                            if subtask:
                                subtask["status"] = "failed"
                        else:
                            task["status"] = "failed"
                    
                    self._save_tasks_data()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to run task tests: {e}")
            return {
                "success": False,
                "error": str(e),
                "task_id": task_id,
                "subtask_id": subtask_id
            }


def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(description='Task Orchestrator')
    parser.add_argument('--config', '-c', default='config.json', help='Configuration file')
    parser.add_argument('--task', '-t', help='Task ID to run tests for')
    parser.add_argument('--subtask', '-s', help='Subtask ID to run tests for')
    parser.add_argument('--run-tests', action='store_true', help='Run tests only')
    
    args = parser.parse_args()
    
    orchestrator = TaskOrchestrator(args.config)
    
    if args.run_tests:
        result = orchestrator.run_task_tests(args.task, args.subtask)
        if result["success"]:
            logger.info("Tests passed successfully")
            sys.exit(0)
        else:
            logger.error("Tests failed")
            sys.exit(1)
    else:
        logger.info("TaskOrchestrator ready")


if __name__ == "__main__":
    main()