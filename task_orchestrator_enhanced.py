"""
Enhanced Task Orchestrator
Version with Task Master MCP integration and progress tracking
Now includes comprehensive error handling and notification system
"""

import os
import sys
import logging
import argparse
import json
import time
import subprocess
import re
import platform
import signal
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Module imports
from claude_desktop_automation import ClaudeDesktopAutomation
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
logger = logging.getLogger("orchestrator_enhanced")


class EnhancedTaskOrchestrator:
    """Enhanced task orchestrator with improved automation capabilities"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.project_root = os.path.abspath(self.config.get("project_dir", "."))
        
        # Initialize components
        try:
            self.claude = ClaudeDesktopAutomation(self.config.get("claude_desktop", {}).get("config_path"))
            self.code_analyzer = CodeAnalyzer()
            self.notification = NotificationManager(self.config.get("notification", {}).get("config_path"))
            self.task_master_client = TaskMasterMCPClient(self.project_root)
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            self._send_critical_error_notification("Initialization Error", str(e))
            raise
        
        # Progress tracking state
        self.progress_state = {
            "initialized_at": datetime.now().isoformat(),
            "current_task": None,
            "current_subtask": None,
            "completed_tasks": [],
            "failed_tasks": [],
            "task_history": []
        }
        
        # Task Master MCP check flag
        self.task_master_checked = False
        
        # Error tracking
        self.error_count = 0
        self.last_error_time = None
        
        logger.info("Enhanced Task Orchestrator initialization complete")
        
    def _send_critical_error_notification(self, error_type: str, error_message: str, 
                                        log_excerpt: str = None, include_recovery_steps: bool = True):
        """Send critical error notification to Slack"""
        try:
            title = f"🚨 Critical Automation Error: {error_type}"
            
            message = f"**Error Type:** {error_type}\n"
            message += f"**Error Message:** {error_message}\n"
            message += f"**System:** Task Orchestrator Enhanced\n"
            message += f"**Timestamp:** {datetime.now().isoformat()}\n"
            message += f"**Status:** System encountered critical error\n\n"
            
            if log_excerpt:
                message += f"**Log Excerpt:**\n```\n{log_excerpt[:1000]}...\n```\n\n"
            
            if include_recovery_steps:
                if "pyscreeze" in error_message.lower() or "pyautogui" in error_message.lower():
                    message += "**Recovery Steps:**\n"
                    message += "1. Run: `python fix_pyautogui_dependencies.py`\n"
                    message += "2. Or run: `quick_fix.bat`\n"
                    message += "3. Restart automation system\n\n"
                else:
                    message += "**Action Required:**\n"
                    message += "• Check system logs for details\n"
                    message += "• Resolve dependency issues\n"
                    message += "• Restart automation system\n\n"
            
            message += f"**Project:** {self.config.get('dev_project_name', 'Unknown')}\n"
            message += f"**Project Path:** {self.config.get('dev_project_path', 'Unknown')}"
            
            # Send notification
            success = self.notification.send_notification(
                message=message,
                title=title,
                severity="error"
            )
            
            if success:
                logger.info("Critical error notification sent successfully")
            else:
                logger.error("Failed to send critical error notification")
                
        except Exception as e:
            logger.error(f"Exception in error notification system: {e}")
    
    def _handle_pyautogui_error(self, error: Exception):
        """Handle PyAutoGUI specific errors"""
        error_message = str(error)
        
        if "pyscreeze" in error_message.lower():
            logger.error("Detected PyAutoGUI pyscreeze dependency error")
            
            log_excerpt = f"""
PyAutoGUI Error: {error_message}
This error typically occurs when:
1. Pillow (PIL) is not properly installed
2. pyscreeze module is missing
3. Python version is incompatible with current Pillow version

Time: {datetime.now().isoformat()}
            """
            
            self._send_critical_error_notification(
                "PyAutoGUI Dependency Error",
                error_message,
                log_excerpt
            )
            
            # Attempt automatic recovery
            logger.info("Attempting automatic dependency fix...")
            try:
                result = subprocess.run([
                    sys.executable, "fix_pyautogui_dependencies.py"
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    logger.info("Automatic dependency fix completed successfully")
                    return True
                else:
                    logger.error(f"Automatic dependency fix failed: {result.stderr}")
                    return False
                    
            except Exception as fix_error:
                logger.error(f"Failed to run automatic dependency fix: {fix_error}")
                return False
        else:
            # Other PyAutoGUI errors
            self._send_critical_error_notification(
                "PyAutoGUI Error",
                error_message,
                f"PyAutoGUI error occurred at {datetime.now().isoformat()}: {error_message}"
            )
            
        return False
    
    def _handle_system_error(self, error: Exception, context: str = "Unknown"):
        """Handle general system errors"""
        error_message = str(error)
        error_traceback = traceback.format_exc()
        
        self.error_count += 1
        self.last_error_time = datetime.now()
        
        logger.error(f"System error in {context}: {error_message}")
        logger.error(f"Traceback: {error_traceback}")
        
        # Send notification for critical errors
        if self.error_count >= 3 or "critical" in error_message.lower():
            log_excerpt = f"""
Context: {context}
Error Count: {self.error_count}
Error Message: {error_message}

Traceback:
{error_traceback}
            """
            
            self._send_critical_error_notification(
                f"System Error ({context})",
                error_message,
                log_excerpt
            )
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
            
            # Send shutdown notification
            try:
                self.notification.send_notification(
                    "System received shutdown signal. Gracefully terminating automation.",
                    "🛑 Automation Shutdown",
                    "warning"
                )
            except:
                pass
            
            # Save progress state
            try:
                self.save_progress_state()
            except:
                pass
            
            logger.info("Graceful shutdown completed")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration file"""
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            logger.warning(f"Configuration file not found: {config_path}")
            return {}
            
    def check_task_master_progress(self):
        """Check current development progress through Task Master MCP"""
        if self.task_master_checked:
            logger.info("Task Master progress already checked.")
            return
            
        logger.info("Checking development progress through Task Master MCP...")
        
        # Task Master MCP check prompt - enhanced version in English
        tasks_dir = f"{self.config.get('dev_project_path')}/tasks"
        prompt = f"""Please check the current development progress using Task Master MCP tools.

Project path: {self.config.get('dev_project_path')}
Tasks directory: {tasks_dir}

Please use the following MCP tools to check progress:

1. Use the initialize_project tool to verify project initialization:
   - projectRoot: "{self.config.get('dev_project_path')}"
   
2. Use the get_tasks tool to retrieve the complete task list:
   - projectRoot: "{self.config.get('dev_project_path')}"
   - withSubtasks: true
   
3. Use the next_task tool to identify the next task to work on:
   - projectRoot: "{self.config.get('dev_project_path')}"
   
4. Use the complexity_report tool to check the complexity analysis report (if available):
   - projectRoot: "{self.config.get('dev_project_path')}"

After checking, please organize the results in the following format:

## Current Progress Summary

### Next Task to Work On
- Task ID: [ID]
- Task Name: [task name]
- Status: [status]
- Subtasks: [number of subtasks]

### Overall Progress
- Completed tasks: X
- In-progress tasks: Y  
- Pending tasks: Z
- Overall progress: XX%

### Major Completed Tasks
- [list of completed tasks]

### Current Work Recommendations
- [recommended next steps]
"""
        
        # Send prompt to Claude
        logger.info("Sending Task Master MCP check request to Claude Desktop...")
        project_name = self.config.get("dev_project_name", "default")
        if self.claude.run_automation(prompt, wait_for_continue=True, create_new_chat=True, project_name=project_name):
            logger.info("Task Master MCP check request sent successfully")
            
            # Increase wait time for Task Master MCP execution
            time.sleep(10)
            
            # TODO: Actually capture and parse Claude's response
            # Currently just improving the prompt to ensure Task Master executes properly
            
            self.task_master_checked = True
            logger.info("Task Master MCP progress check request completed")
        else:
            logger.error("Task Master MCP check request failed")
            
    def update_progress_from_task_master(self, progress_data: Dict[str, Any]):
        """Update internal state with progress data from Task Master"""
        if progress_data:
            if progress_data.get("current_task"):
                self.progress_state["current_task"] = progress_data["current_task"]
            if progress_data.get("current_subtask"):
                self.progress_state["current_subtask"] = progress_data["current_subtask"]
            if progress_data.get("completed_tasks"):
                self.progress_state["completed_tasks"] = progress_data["completed_tasks"]
                
            # Save progress state
            self.save_progress_state()
            
    def save_progress_state(self):
        """Save current progress state to file"""
        progress_file = Path(self.project_root) / "logs" / "orchestrator_progress.json"
        progress_file.parent.mkdir(exist_ok=True)
        
        try:
            # Add timestamp
            self.progress_state["last_updated"] = datetime.now().isoformat()
            
            with open(progress_file, 'w') as f:
                json.dump(self.progress_state, f, indent=2)
                
            logger.info(f"Progress state saved: {progress_file}")
        except Exception as e:
            logger.error(f"Failed to save progress state: {e}")
            
    def load_progress_state(self):
        """Load saved progress state"""
        progress_file = Path(self.project_root) / "logs" / "orchestrator_progress.json"
        
        if progress_file.exists():
            try:
                with open(progress_file, 'r') as f:
                    loaded_state = json.load(f)
                    self.progress_state.update(loaded_state)
                    logger.info("Previous progress state loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load progress state: {e}")
                
    def get_task_complexity_score(self, task_id: str) -> int:
        """Get task complexity score from Task Master MCP or estimate it"""
        try:
            # Try to get complexity report from Task Master
            complexity_report_path = Path(self.project_root) / "scripts" / "task-complexity-report.json"
            
            if complexity_report_path.exists():
                with open(complexity_report_path, 'r') as f:
                    report = json.load(f)
                    
                # Find task in report
                for task in report.get("tasks", []):
                    if str(task.get("id")) == str(task_id):
                        complexity = task.get("complexity", {})
                        score = complexity.get("score", 5)
                        logger.info(f"Task {task_id} complexity score from report: {score}/10")
                        return score
            
            # Default to medium complexity if not found
            logger.info(f"No complexity score found for task {task_id}, using default: 5/10")
            return 5
            
        except Exception as e:
            logger.error(f"Error getting task complexity: {e}")
            return 5  # Default to medium complexity
    
    def process_task_with_mcp(self, task_id: str, subtask_id: Optional[str] = None):
        """Process task using Task Master MCP"""
        logger.info(f"Starting task processing: task_id={task_id}, subtask_id={subtask_id}")
        
        # Get task complexity score
        complexity_score = self.get_task_complexity_score(task_id)
        
        # Update progress state
        self.progress_state["current_task"] = {"id": task_id, "started_at": datetime.now().isoformat(), "complexity": complexity_score}
        if subtask_id:
            self.progress_state["current_subtask"] = {"id": subtask_id, "started_at": datetime.now().isoformat()}
        self.save_progress_state()
        
        # Create prompt using both Task Master MCP and JetBrains MCP
        prompt = f"""Please implement the task using both Task Master MCP and JetBrains MCP tools together.

Project path: {self.config.get('dev_project_path')}
Task ID: {task_id}
Subtask ID: {subtask_id if subtask_id else 'None'}

## Work Order:

1. **Check task information with Task Master MCP**:
   - Use get_task tool:
     - projectRoot: "{self.config.get('dev_project_path')}"
     - id: "{task_id}"
   
2. **Read task file with JetBrains MCP**:
   - Use get_file_text_by_path tool:
     - pathInProject: "tasks/task_{task_id:03d}.txt" or corresponding task file
   
3. **Develop implementation plan**:
   - Analyze task requirements
   - Identify necessary classes/methods
   - Establish testing strategy
   
4. **Implement with JetBrains MCP**:
   - create_new_file_with_text: Create new files
   - replace_specific_text: Modify existing code
   - get_file_text_by_path: Check existing code when needed
   
5. **Write test code**:
   - Write unit tests
   - Write integration tests (if necessary)
   
6. **Execute tests**:
   - Use execute_terminal_command tool to run gradle test:
     - command: "gradlew.bat test" (Windows) or "./gradlew test" (Linux/Mac)
   
7. **Mark task as complete with Task Master MCP**:
   - Use set_task_status tool:
     - projectRoot: "{self.config.get('dev_project_path')}"
     - id: "{task_id}{'.' + subtask_id if subtask_id else ''}"
     - status: "done"

## Important Notes:
- Follow project structure and architecture conventions
- Consider code quality and readability
- Write JavaDoc for all public methods
- Aim for 80%+ unit test coverage
- If tests fail, identify the cause and fix it

Please start the implementation!
"""
        
        # Send prompt to Claude
        logger.info("Sending task implementation request to Claude Desktop...")
        project_name = self.config.get("dev_project_name", "default")
        if self.claude.run_automation(prompt, wait_for_continue=True, project_name=project_name, task_complexity=complexity_score):
            logger.info("Task implementation request sent successfully")
            
            # Wait for implementation completion (needs more time)
            time.sleep(30)  # Increased wait time for implementation
            
            # Tests are executed directly by Claude, so we just check results here
            # Update progress
            task_info = {"id": task_id, "completed_at": datetime.now().isoformat()}
            if subtask_id:
                task_info["subtask_id"] = subtask_id
            self.progress_state["completed_tasks"].append(task_info)
            self.progress_state["task_history"].append({
                "action": "completed",
                "task": task_info,
                "timestamp": datetime.now().isoformat()
            })
            self.save_progress_state()
            
            # Send completion notification
            self.notification.notify_task_completion(task_id, f"Task {task_id}" + (f" Subtask {subtask_id}" if subtask_id else ""))
            
            return True
        else:
            logger.error("Task implementation request failed")
            
            # Record failure
            task_info = {"id": task_id, "failed_at": datetime.now().isoformat(), "reason": "request_failure"}
            if subtask_id:
                task_info["subtask_id"] = subtask_id
            self.progress_state["failed_tasks"].append(task_info)
            self.progress_state["task_history"].append({
                "action": "failed",
                "task": task_info,
                "timestamp": datetime.now().isoformat()
            })
            self.save_progress_state()
            
            # Send failure notification
            self.notification.notify_subtask_failure(
                task_id, f"Task {task_id}",
                subtask_id or "main", f"Subtask {subtask_id}" if subtask_id else "Main task",
                1, "Task implementation request failed"
            )
            
            return False
            
    def run_tests_in_dev_project(self) -> bool:
        """Run tests in development project"""
        if not self.config.get("dev_project_path"):
            logger.warning("Development project path not configured.")
            return False
            
        dev_path = Path(self.config["dev_project_path"])
        project_type = self.config.get("project_type", "gradle")
        
        if project_type == "gradle":
            # Run Gradle project tests
            test_command = ["gradlew.bat" if platform.system() == "Windows" else "./gradlew", "test"]
            
            try:
                logger.info(f"Running tests: {' '.join(test_command)}")
                result = subprocess.run(
                    test_command,
                    cwd=dev_path,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                if result.returncode == 0:
                    logger.info("Tests passed successfully!")
                    return True
                else:
                    logger.error(f"Tests failed: {result.stderr}")
                    return False
                    
            except subprocess.TimeoutExpired:
                logger.error("Test execution timeout")
                return False
            except Exception as e:
                logger.error(f"Error running tests: {e}")
                return False
        else:
            logger.warning(f"Unsupported project type: {project_type}")
            return False
            
    def check_code_quality(self):
        """Check code quality"""
        if not self.config.get("dev_project_path"):
            return
            
        dev_path = Path(self.config["dev_project_path"])
        src_dir = dev_path / self.config.get("src_dir", "src")
        
        if src_dir.exists():
            logger.info("Starting code quality check...")
            analysis_result = self.code_analyzer.analyze_project(str(src_dir))
            
            if analysis_result["total_mocks"] > 0 or analysis_result["total_commented_code"] > 0:
                logger.warning("Code quality issues found!")
                self.notification.notify_mock_detection(analysis_result)
            else:
                logger.info("Code quality check passed")
                
    def commit_changes(self, task_id: str, subtask_id: Optional[str] = None):
        """Perform Git commit"""
        if not self.config.get("git_enabled", False):
            return
            
        dev_path = Path(self.config.get("dev_project_path", "."))
        
        try:
            # Git add
            subprocess.run(["git", "add", "."], cwd=dev_path, check=True)
            
            # Create commit message
            commit_message = f"Task {task_id}"
            if subtask_id:
                commit_message += f" Subtask {subtask_id}"
            commit_message += " implementation complete"
            
            # Git commit
            subprocess.run(["git", "commit", "-m", commit_message], cwd=dev_path, check=True)
            
            logger.info(f"Git commit complete: {commit_message}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git commit failed: {e}")
            
    def run(self):
        """Run the orchestrator with comprehensive error handling"""
        logger.info("Starting Enhanced Task Orchestrator")
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
        try:
            # Load previous progress state
            self.load_progress_state()
            
            # Check current progress through Task Master MCP with initial prompt
            logger.info("Sending initial prompt to Claude Desktop...")
            initial_prompt = f"Use task-master MCP to check the progress status of tasks, and perform code modifications at {self.config.get('dev_project_path')} using JetBrains MCP. However, if task-master MCP is unavailable, read the task.json file containing prioritized tasks in the ./tasks directory under the project root and perform the work accordingly."
            
            project_name = self.config.get("dev_project_name", "default")
            try:
                if self.claude.run_automation(initial_prompt, wait_for_continue=True, create_new_chat=True, project_name=project_name):
                    logger.info("Initial prompt sent successfully")
                    time.sleep(10)
                else:
                    logger.error("Failed to send initial prompt")
            except Exception as e:
                if "pyscreeze" in str(e).lower() or "pyautogui" in str(e).lower():
                    logger.error("PyAutoGUI dependency error detected during initial prompt")
                    if self._handle_pyautogui_error(e):
                        logger.info("Dependency fix completed. Attempting to continue...")
                        # Retry the initial prompt
                        if self.claude.run_automation(initial_prompt, wait_for_continue=True, create_new_chat=True, project_name=project_name):
                            logger.info("Initial prompt sent successfully after fix")
                        else:
                            logger.error("Initial prompt still failing after dependency fix")
                            return False
                    else:
                        logger.error("Dependency fix failed. Cannot continue.")
                        return False
                else:
                    self._handle_system_error(e, "Initial Prompt")
                    raise
            
            # Process tasks continuously
            logger.info("Starting automatic task processing through Task Master MCP...")
            
            # Maximum tasks to process (prevent infinite loop)
            max_tasks = self.config.get("max_tasks_per_run", 10)
            processed_tasks = 0
            consecutive_failures = 0
            max_consecutive_failures = 3
            
            while processed_tasks < max_tasks and consecutive_failures < max_consecutive_failures:
                try:
                    # Prompt for checking next task
                    next_task_prompt = f"""Please check the next task to work on using Task Master MCP and implement it.

Project path: {self.config.get('dev_project_path')}

## Work sequence:

1. **Check next task with next_task tool**:
   - projectRoot: "{self.config.get('dev_project_path')}"
   
2. **If there is a next task**:
   - Follow the task implementation process described in previous messages
   - Complete testing
   - Mark as done with set_task_status
   
3. **If all tasks are completed**:
   - Respond with "ALL_TASKS_COMPLETED"

Note: When implementing tasks, please follow the complete process explained in previous messages.
"""
                    
                    logger.info(f"Checking and processing next task... ({processed_tasks + 1}/{max_tasks})")
                    
                    # Send prompt to Claude
                    project_name = self.config.get("dev_project_name", "default")
                    # Use higher complexity for next task checking (might involve analysis)
                    if self.claude.run_automation(next_task_prompt, wait_for_continue=True, project_name=project_name, task_complexity=7):
                        logger.info("Task processing request sent successfully")
                        
                        # Wait for completion - adjust based on recent task complexity
                        wait_time = 30 if processed_tasks == 0 else 60  # Longer wait after first task
                        time.sleep(wait_time)
                        
                        # TODO: Actually parse Claude's response to check for "ALL_TASKS_COMPLETED"
                        # Currently just incrementing count
                        processed_tasks += 1
                        consecutive_failures = 0  # Reset failure counter on success
                        
                        # Save progress state
                        self.save_progress_state()
                        
                    else:
                        logger.error("Task processing request failed")
                        consecutive_failures += 1
                        if consecutive_failures >= max_consecutive_failures:
                            logger.error(f"Too many consecutive failures ({consecutive_failures}). Stopping.")
                            self._send_critical_error_notification(
                                "Task Processing Failure",
                                f"System failed {consecutive_failures} consecutive times during task processing",
                                f"Consecutive failures: {consecutive_failures}/{max_consecutive_failures}\nProcessed tasks: {processed_tasks}/{max_tasks}"
                            )
                            break
                        else:
                            logger.warning(f"Failure {consecutive_failures}/{max_consecutive_failures}. Retrying...")
                            time.sleep(10)  # Brief pause before retry
                
                except Exception as e:
                    if "pyscreeze" in str(e).lower() or "pyautogui" in str(e).lower():
                        logger.error("PyAutoGUI dependency error during task processing")
                        if self._handle_pyautogui_error(e):
                            logger.info("Dependency fix completed during task processing. Continuing...")
                            consecutive_failures = 0  # Reset on successful fix
                            continue
                        else:
                            logger.error("Dependency fix failed during task processing. Stopping.")
                            break
                    else:
                        self._handle_system_error(e, "Task Processing Loop")
                        consecutive_failures += 1
                        if consecutive_failures >= max_consecutive_failures:
                            logger.error("Too many errors during task processing. Stopping.")
                            break
                        else:
                            logger.warning(f"Error {consecutive_failures}/{max_consecutive_failures}. Continuing...")
                            time.sleep(5)
                    
            logger.info(f"Task processing complete: {processed_tasks} tasks processed")
            
            # Send completion notification
            try:
                self.notification.send_notification(
                    f"Task processing session completed. Processed {processed_tasks} tasks with {consecutive_failures} failures.",
                    "🎉 Automation Session Complete",
                    "info"
                )
            except:
                pass
            
            # Print final progress summary
            self.print_progress_summary()
            
            return True
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt. Shutting down gracefully...")
            try:
                self.notification.send_notification(
                    "Automation system interrupted by user (Ctrl+C)",
                    "🛑 Manual Shutdown",
                    "warning"
                )
            except:
                pass
            return False
            
        except Exception as e:
            self._handle_system_error(e, "Main Run Loop")
            logger.error(f"Critical error in main run loop: {e}")
            
            # Send final error notification
            try:
                self._send_critical_error_notification(
                    "Critical System Failure",
                    str(e),
                    f"System failed in main run loop at {datetime.now().isoformat()}\n\nException: {str(e)}\n\nTraceback: {traceback.format_exc()}"
                )
            except:
                pass
            
            return False
        
    def print_progress_summary(self):
        """Print progress summary"""
        logger.info("=" * 50)
        logger.info("Progress Summary")
        logger.info("=" * 50)
        logger.info(f"Completed tasks: {len(self.progress_state.get('completed_tasks', []))}")
        logger.info(f"Failed tasks: {len(self.progress_state.get('failed_tasks', []))}")
        
        if self.progress_state.get('completed_tasks'):
            logger.info("\nCompleted task list:")
            for task in self.progress_state['completed_tasks']:
                logger.info(f"  - {task}")
                
        if self.progress_state.get('failed_tasks'):
            logger.info("\nFailed task list:")
            for task in self.progress_state['failed_tasks']:
                logger.info(f"  - {task}")
                
        logger.info("=" * 50)


def main():
    """Main function with comprehensive error handling"""
    try:
        parser = argparse.ArgumentParser(description='Enhanced Task Orchestrator with Task Master MCP')
        parser.add_argument('--config', type=str, default='config.json', help='Configuration file path')
        parser.add_argument('--task', type=str, help='Run specific task only')
        parser.add_argument('--subtask', type=str, help='Run specific subtask only')
        parser.add_argument('--check-progress', action='store_true', help='Check progress only')
        
        args = parser.parse_args()
        
        # Create orchestrator
        orchestrator = EnhancedTaskOrchestrator(args.config)
        
        if args.check_progress:
            # Check progress only
            orchestrator.check_task_master_progress()
            orchestrator.print_progress_summary()
        elif args.task:
            # Run specific task only
            success = orchestrator.process_task_with_mcp(args.task, args.subtask)
            if not success:
                logger.error(f"Task {args.task} processing failed")
                sys.exit(1)
        else:
            # Run all
            success = orchestrator.run()
            if not success:
                logger.error("Orchestrator run failed")
                sys.exit(1)
                
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
        print("\nProgram interrupted by user")
        sys.exit(130)  # Standard exit code for Ctrl+C
        
    except Exception as e:
        logger.error(f"Unhandled exception in main: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Try to send emergency notification
        try:
            from notification_manager import NotificationManager
            notifier = NotificationManager("notification_config.json")
            notifier.send_notification(
                f"**Unhandled Exception in Main Function**\n\nError: {str(e)}\n\nTraceback:\n```\n{traceback.format_exc()}\n```",
                "🚨 Critical System Error",
                "error"
            )
        except:
            pass  # If notification fails, just continue with exit
        
        print(f"\nCritical error: {e}")
        print("Check logs for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
