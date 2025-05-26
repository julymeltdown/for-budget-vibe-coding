#!/usr/bin/env python
"""
Task Master Wrapper - Compatibility wrapper for existing task-master commands
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from task_orchestrator import TaskOrchestrator


class TaskMasterWrapper:
    def __init__(self, config_path="config.json"):
        self.orchestrator = TaskOrchestrator(config_path)
        self.tasks_data = self.orchestrator.tasks_data
    
    def list_tasks(self, filter_status=None, show_details=False):
        """Display task list."""
        print("\n=== Task List ===\n")
        
        if not self.tasks_data.get("tasks"):
            print("No tasks registered.")
            return
        
        for task in self.tasks_data["tasks"]:
            if filter_status and task.get("status") != filter_status:
                continue
                
            status_emoji = {
                "pending": "⏳",
                "in_progress": "🔄",
                "completed": "✅",
                "failed": "❌"
            }.get(task.get("status", "pending"), "❓")
            
            print(f"{status_emoji} [{task['id']}] {task.get('name', 'Unnamed Task')}")
            print(f"   Status: {task.get('status', 'pending')}")
            
            if show_details and task.get("description"):
                print(f"   Description: {task['description']}")
            
            # Subtask information
            subtasks = task.get("subtasks", [])
            if subtasks:
                completed_subtasks = sum(1 for st in subtasks if st.get("status") == "completed")
                print(f"   Subtasks: {completed_subtasks}/{len(subtasks)} completed")
                
                if show_details:
                    for subtask in subtasks:
                        st_emoji = {
                            "pending": "  ⏳",
                            "in_progress": "  🔄",
                            "completed": "  ✅",
                            "failed": "  ❌"
                        }.get(subtask.get("status", "pending"), "  ❓")
                        print(f"     {st_emoji} [{subtask['id']}] {subtask.get('name', 'Unnamed Subtask')}")
            
            # Start/completion time
            if task.get("started_at"):
                print(f"   Started: {task['started_at']}")
            if task.get("completed_at"):
                print(f"   Completed: {task['completed_at']}")
                
            print()  # Empty line
    
    def show_status(self):
        """Summarize project progress."""
        print("\n=== Project Progress ===\n")
        
        total_tasks = len(self.tasks_data.get("tasks", []))
        if total_tasks == 0:
            print("No tasks registered.")
            return
        
        # Aggregate by task status
        status_counts = {
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "failed": 0
        }
        
        total_subtasks = 0
        completed_subtasks = 0
        
        for task in self.tasks_data["tasks"]:
            status = task.get("status", "pending")
            status_counts[status] = status_counts.get(status, 0) + 1
            
            subtasks = task.get("subtasks", [])
            total_subtasks += len(subtasks)
            completed_subtasks += sum(1 for st in subtasks if st.get("status") == "completed")
        
        # Calculate progress
        completed_tasks = status_counts["completed"]
        task_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        subtask_progress = (completed_subtasks / total_subtasks * 100) if total_subtasks > 0 else 0
        
        print(f"Total tasks: {total_tasks}")
        print(f"  - Pending: {status_counts['pending']}")
        print(f"  - In Progress: {status_counts['in_progress']}")
        print(f"  - Completed: {status_counts['completed']}")
        print(f"  - Failed: {status_counts['failed']}")
        print(f"\nTask Progress: {task_progress:.1f}%")
        print(f"Subtask Progress: {subtask_progress:.1f}% ({completed_subtasks}/{total_subtasks})")
        
        # Test history information
        test_history_file = os.path.join("logs", "test_history.json")
        if os.path.exists(test_history_file):
            try:
                with open(test_history_file, 'r') as f:
                    test_history = json.load(f)
                    
                print(f"\nTest Execution Statistics:")
                print(f"  - Total runs: {test_history.get('total_runs', 0)}")
                print(f"  - Passed: {test_history.get('total_passes', 0)}")
                print(f"  - Failed: {test_history.get('total_failures', 0)}")
                
                if test_history.get('last_run'):
                    last_run = datetime.fromtimestamp(test_history['last_run'])
                    print(f"  - Last run: {last_run.strftime('%Y-%m-%d %H:%M:%S')}")
            except Exception as e:
                pass
    
    def reset_task(self, task_id=None, subtask_id=None):
        """Reset status of task or subtask."""
        if task_id:
            task = self.orchestrator.get_task_by_id(task_id)
            if not task:
                print(f"Task '{task_id}' not found.")
                return False
                
            if subtask_id:
                subtask = self.orchestrator.get_subtask_by_id(task, subtask_id)
                if not subtask:
                    print(f"Subtask '{subtask_id}' not found.")
                    return False
                    
                subtask["status"] = "pending"
                subtask["failure_count"] = 0
                print(f"Reset subtask '{subtask.get('name', subtask_id)}' status.")
            else:
                task["status"] = "pending"
                task["failure_count"] = 0
                task.pop("started_at", None)
                task.pop("completed_at", None)
                
                # Reset all subtasks too
                for subtask in task.get("subtasks", []):
                    subtask["status"] = "pending"
                    subtask["failure_count"] = 0
                    
                print(f"Reset task '{task.get('name', task_id)}' status.")
        else:
            # Reset all tasks
            for task in self.tasks_data["tasks"]:
                task["status"] = "pending"
                task["failure_count"] = 0
                task.pop("started_at", None)
                task.pop("completed_at", None)
                
                for subtask in task.get("subtasks", []):
                    subtask["status"] = "pending"
                    subtask["failure_count"] = 0
                    
            print("Reset all task statuses.")
        
        self.orchestrator._save_tasks_data()
        return True


def main():
    parser = argparse.ArgumentParser(
        description='Task Master - AI Automation Project Management Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
  python task_master_wrapper.py list              # Show all tasks
  python task_master_wrapper.py list --status pending  # Show only pending tasks
  python task_master_wrapper.py list --details    # Include detailed information
  python task_master_wrapper.py status            # Summarize project progress
  python task_master_wrapper.py reset             # Reset all task statuses
  python task_master_wrapper.py reset --task task-1  # Reset specific task
  python task_master_wrapper.py run               # Run tasks (calls task_orchestrator.py)
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # list command
    list_parser = subparsers.add_parser('list', help='Display task list')
    list_parser.add_argument('--status', choices=['pending', 'in_progress', 'completed', 'failed'],
                           help='Show only tasks with specific status')
    list_parser.add_argument('--details', '-d', action='store_true',
                           help='Show detailed information')
    
    # status command
    status_parser = subparsers.add_parser('status', help='Summarize project progress')
    
    # reset command
    reset_parser = subparsers.add_parser('reset', help='Reset task status')
    reset_parser.add_argument('--task', '-t', help='Task ID to reset')
    reset_parser.add_argument('--subtask', '-s', help='Subtask ID to reset')
    
    # run command
    run_parser = subparsers.add_parser('run', help='Run tasks')
    run_parser.add_argument('--task', '-t', help='Task ID to run')
    run_parser.add_argument('--subtask', '-s', help='Subtask ID to run')
    
    # Config file option (common to all commands)
    parser.add_argument('--config', '-c', default='config.json',
                       help='Configuration file path (default: config.json)')
    
    args = parser.parse_args()
    
    # Show status if no command
    if not args.command:
        args.command = 'status'
    
    # Initialize TaskMasterWrapper
    wrapper = TaskMasterWrapper(args.config)
    
    # Execute command
    if args.command == 'list':
        wrapper.list_tasks(filter_status=args.status, show_details=args.details)
    
    elif args.command == 'status':
        wrapper.show_status()
    
    elif args.command == 'reset':
        wrapper.reset_task(task_id=args.task, subtask_id=args.subtask)
    
    elif args.command == 'run':
        # Execute task_orchestrator.py
        from task_orchestrator import main as orchestrator_main
        sys.argv = ['task_orchestrator.py', '--config', args.config]
        if args.task:
            sys.argv.extend(['--task', args.task])
        if args.subtask:
            sys.argv.extend(['--subtask', args.subtask])
        orchestrator_main()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
