"""
Task Master MCP Client
MCP client module for integrating Claude Desktop with Task Master
"""

import os
import json
import logging
import asyncio
import subprocess
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class TaskMasterMCPClient:
    """Task Master MCP client"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).absolute()
        self.dev_project_path = None
        self.dev_project_name = None
        self._load_config()
        
    def _load_config(self):
        """Load configuration file"""
        config_path = self.project_root / "config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.dev_project_path = config.get('dev_project_path')
                self.dev_project_name = config.get('dev_project_name')
                
    def create_mcp_prompt(self) -> str:
        """Create prompt to check current development status through Task Master MCP"""
        if not self.dev_project_path:
            return "Task Master MCP configuration not found. Please set the development project path."
            
        prompt = f"""Please check the current development progress using Task Master MCP tools.

Project path: {self.dev_project_path}
Project name: {self.dev_project_name}

Please verify the following information:
1. Currently active task ID and name
2. Currently active subtask ID and name  
3. List of completed tasks/subtasks
4. List of remaining tasks/subtasks
5. Overall progress percentage

Example MCP commands:
- Use get_tasks command to view all tasks
- Use get_task --id [task_id] to view specific task details
- Use next_task command to identify the next task to work on

After checking, please provide the results in JSON format:
{{
    "current_task": {{"id": "...", "name": "...", "status": "..."}},
    "current_subtask": {{"id": "...", "name": "...", "status": "..."}},
    "completed_tasks": [...],
    "pending_tasks": [...],
    "progress_percentage": ...
}}
"""
        return prompt
        
    def parse_mcp_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse MCP response to extract progress information"""
        try:
            # Find JSON blocks
            import re
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, response, re.DOTALL)
            
            for match in matches:
                try:
                    data = json.loads(match)
                    if 'current_task' in data:
                        return data
                except json.JSONDecodeError:
                    continue
                    
            logger.warning("Could not find valid JSON in MCP response.")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing MCP response: {e}")
            return None
            
    def save_progress_state(self, progress_data: Dict[str, Any]):
        """Save progress state to file"""
        progress_file = self.project_root / "logs" / "task_progress_state.json"
        progress_file.parent.mkdir(exist_ok=True)
        
        try:
            # Load existing state
            if progress_file.exists():
                with open(progress_file, 'r') as f:
                    existing_data = json.load(f)
            else:
                existing_data = {"history": []}
                
            # Add current timestamp
            import time
            progress_data["timestamp"] = time.time()
            progress_data["timestamp_str"] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Update current state
            existing_data["current"] = progress_data
            existing_data["history"].append(progress_data)
            
            # Keep only last 100 history entries
            if len(existing_data["history"]) > 100:
                existing_data["history"] = existing_data["history"][-100:]
                
            # Save
            with open(progress_file, 'w') as f:
                json.dump(existing_data, f, indent=2)
                
            logger.info(f"Progress state saved: {progress_file}")
            
        except Exception as e:
            logger.error(f"Error saving progress state: {e}")
            
    def load_progress_state(self) -> Optional[Dict[str, Any]]:
        """Load saved progress state"""
        progress_file = self.project_root / "logs" / "task_progress_state.json"
        
        if not progress_file.exists():
            return None
            
        try:
            with open(progress_file, 'r') as f:
                data = json.load(f)
                return data.get("current")
        except Exception as e:
            logger.error(f"Error loading progress state: {e}")
            return None
            
    def get_task_file_path(self, task_id: str, subtask_id: Optional[str] = None) -> Optional[Path]:
        """Return file path for task/subtask"""
        if not self.dev_project_path:
            return None
            
        dev_path = Path(self.dev_project_path)
        task_files_dir = dev_path / "tasks"
        
        if not task_files_dir.exists():
            logger.warning(f"Task files directory not found: {task_files_dir}")
            return None
            
        # Find subtask file
        if subtask_id:
            subtask_file = task_files_dir / f"subtask_{task_id}_{subtask_id}.txt"
            if subtask_file.exists():
                return subtask_file
                
        # Find task file
        task_file = task_files_dir / f"task_{task_id}.txt"
        if task_file.exists():
            return task_file
            
        # Try with numeric ID
        if task_id.isdigit():
            task_file = task_files_dir / f"task_{int(task_id):03d}.txt"
            if task_file.exists():
                return task_file
                
        logger.warning(f"Task file not found: task_id={task_id}, subtask_id={subtask_id}")
        return None
        
    def create_task_prompt(self, task_id: str, subtask_id: Optional[str] = None) -> str:
        """Create prompt for task/subtask implementation"""
        task_file = self.get_task_file_path(task_id, subtask_id)
        
        if not task_file:
            return f"Task file not found: task_id={task_id}, subtask_id={subtask_id}"
            
        # Create prompt to read file through MCP
        file_path_in_project = str(task_file.relative_to(Path(self.dev_project_path)))
        
        prompt = f"""Please implement the following task using JetBrains MCP.

Project path: {self.dev_project_path}
Task file: {file_path_in_project}

Implementation steps:
1. First, use get_file_text_by_path command to read the task file content.
2. Analyze the task requirements and create an implementation plan.
3. Create or modify necessary files according to the plan.
4. Write comprehensive test code alongside the implementation.
5. Execute tests to verify the implementation.

Important guidelines:
- Follow the project structure and architecture patterns.
- Prioritize code quality and readability.
- Write JavaDoc comments for all public methods.
- Aim for at least 80% unit test coverage.
- Use meaningful variable and method names.
- Handle edge cases and error scenarios properly.
"""
        
        return prompt
