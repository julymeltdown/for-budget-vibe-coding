#!/usr/bin/env python3
"""
Dashboard API Server
Provides REST API endpoints for monitoring automation tasks and system status
"""

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import json
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import subprocess

# Add current directory to Python path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Task Master functionality - with error handling
try:
    from task_master_wrapper import TaskMasterWrapper
    TASKMASTER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"TaskMasterWrapper not available: {e}")
    TASKMASTER_AVAILABLE = False

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for web dashboard access

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent
TASKS_FILE = PROJECT_ROOT / "tasks.json"
ORCHESTRATOR_PROGRESS_FILE = PROJECT_ROOT / "logs" / "orchestrator_progress.json"
TEST_HISTORY_FILE = PROJECT_ROOT / "logs" / "test_history.json"
ORCHESTRATOR_LOG_FILE = PROJECT_ROOT / "logs" / "automation_orchestrator.log"
CLAUDE_LOG_FILE = PROJECT_ROOT / "logs" / "claude_automation.log"

# --- Helper Functions ---

def read_json_file(file_path: Path, default_data: Any = None) -> Any:
    """Read JSON file with error handling"""
    if not file_path.exists():
        return default_data if default_data is not None else {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return default_data if default_data is not None else {}

def write_json_file(file_path: Path, data: Any) -> bool:
    """Write JSON file with error handling"""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error writing {file_path}: {e}")
        return False

def read_log_tail(file_path: Path, lines: int = 100) -> List[str]:
    """Read the last N lines from a log file"""
    if not file_path.exists():
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            return all_lines[-lines:]
    except Exception as e:
        logger.error(f"Error reading log {file_path}: {e}")
        return []

# --- API Endpoints ---

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

# Task Management Endpoints

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks with optional filtering"""
    status_filter = request.args.get('status')
    priority_filter = request.args.get('priority')
    
    tasks_data = read_json_file(TASKS_FILE, {"tasks": []})
    tasks_list = tasks_data.get("tasks", [])
    
    # Apply filters
    if status_filter:
        tasks_list = [task for task in tasks_list if task.get("status") == status_filter]
    if priority_filter:
        tasks_list = [task for task in tasks_list if task.get("priority") == priority_filter]
    
    # Add subtask counts
    for task in tasks_list:
        subtasks = task.get("subtasks", [])
        task['subtask_count'] = len(subtasks)
        task['completed_subtasks'] = len([st for st in subtasks if st.get("status") == "done"])
    
    return jsonify({
        'tasks': tasks_list,
        'total': len(tasks_list)
    })

@app.route('/api/tasks/<string:task_id>', methods=['GET'])
def get_task_detail(task_id: str):
    """Get detailed information about a specific task"""
    tasks_data = read_json_file(TASKS_FILE, {"tasks": []})
    
    for task in tasks_data.get("tasks", []):
        if str(task.get("id")) == task_id:
            return jsonify(task)
    
    return jsonify({'error': 'Task not found'}), 404

@app.route('/api/tasks/<string:task_id>/subtasks/<string:subtask_id>', methods=['GET'])
def get_subtask_detail(task_id: str, subtask_id: str):
    """Get detailed information about a specific subtask"""
    tasks_data = read_json_file(TASKS_FILE, {"tasks": []})
    
    for task in tasks_data.get("tasks", []):
        if str(task.get("id")) == task_id:
            for subtask in task.get("subtasks", []):
                if str(subtask.get("id")) == subtask_id:
                    return jsonify({
                        **subtask,
                        'parent_task_id': task_id,
                        'parent_task_name': task.get('name')
                    })
    
    return jsonify({'error': 'Subtask not found'}), 404

@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Create a new task"""
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Task name is required'}), 400
        
        tasks_data = read_json_file(TASKS_FILE, {"tasks": []})
        tasks_list = tasks_data.get("tasks", [])
        
        # Generate new ID
        max_id = max([int(task.get("id", 0)) for task in tasks_list], default=0)
        new_id = str(max_id + 1)
        
        new_task = {
            'id': new_id,
            'name': data['name'],
            'description': data.get('description', ''),
            'priority': data.get('priority', 'medium'),
            'status': data.get('status', 'pending'),
            'created_at': datetime.now().isoformat(),
            'subtasks': []
        }
        
        tasks_list.append(new_task)
        tasks_data['tasks'] = tasks_list
        
        if write_json_file(TASKS_FILE, tasks_data):
            return jsonify(new_task), 201
        else:
            return jsonify({'error': 'Failed to save task'}), 500
            
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<string:task_id>/status', methods=['PUT'])
def update_task_status(task_id: str):
    """Update task status"""
    try:
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({'error': 'Status is required'}), 400
        
        tasks_data = read_json_file(TASKS_FILE, {"tasks": []})
        tasks_list = tasks_data.get("tasks", [])
        
        task_found = False
        for task in tasks_list:
            if str(task.get("id")) == task_id:
                task['status'] = data['status']
                task['updated_at'] = datetime.now().isoformat()
                task_found = True
                break
        
        if not task_found:
            return jsonify({'error': 'Task not found'}), 404
        
        tasks_data['tasks'] = tasks_list
        if write_json_file(TASKS_FILE, tasks_data):
            return jsonify({'message': 'Task status updated'}), 200
        else:
            return jsonify({'error': 'Failed to update task'}), 500
            
    except Exception as e:
        logger.error(f"Error updating task status: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Progress and History Endpoints

@app.route('/api/progress/current', methods=['GET'])
def get_current_progress():
    """Get current automation progress"""
    progress_data = read_json_file(ORCHESTRATOR_PROGRESS_FILE)
    
    # Calculate overall progress
    if progress_data:
        total_tasks = progress_data.get('total_tasks', 0)
        completed_tasks = progress_data.get('completed_tasks', 0)
        progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        progress_data['progress_percentage'] = progress_percentage
    
    return jsonify(progress_data)

@app.route('/api/progress/history', methods=['GET'])
def get_progress_history():
    """Get historical execution data"""
    # This would typically query a database, but for now we'll use log parsing
    history = []
    
    # Parse orchestrator log for execution history
    log_lines = read_log_tail(ORCHESTRATOR_LOG_FILE, 1000)
    
    for line in log_lines:
        if "Task completed:" in line or "Task failed:" in line:
            # Simple parsing - in production, use structured logging
            parts = line.split(' - ')
            if len(parts) >= 4:
                timestamp = parts[0]
                status = 'completed' if 'completed' in line else 'failed'
                history.append({
                    'timestamp': timestamp,
                    'status': status,
                    'message': parts[-1].strip()
                })
    
    return jsonify({
        'history': history[-50:],  # Last 50 entries
        'total_entries': len(history)
    })

@app.route('/api/progress/stats', methods=['GET'])
def get_progress_stats():
    """Get automation statistics"""
    tasks_data = read_json_file(TASKS_FILE, {"tasks": []})
    tasks_list = tasks_data.get("tasks", [])
    
    # Calculate statistics
    stats = {
        'total_tasks': len(tasks_list),
        'completed_tasks': len([t for t in tasks_list if t.get('status') == 'done']),
        'pending_tasks': len([t for t in tasks_list if t.get('status') == 'pending']),
        'in_progress_tasks': len([t for t in tasks_list if t.get('status') == 'in-progress']),
        'failed_tasks': len([t for t in tasks_list if t.get('status') == 'failed']),
        'priority_breakdown': {
            'high': len([t for t in tasks_list if t.get('priority') == 'high']),
            'medium': len([t for t in tasks_list if t.get('priority') == 'medium']),
            'low': len([t for t in tasks_list if t.get('priority') == 'low'])
        }
    }
    
    # Add subtask statistics
    total_subtasks = sum(len(task.get('subtasks', [])) for task in tasks_list)
    completed_subtasks = sum(
        len([st for st in task.get('subtasks', []) if st.get('status') == 'done'])
        for task in tasks_list
    )
    
    stats['total_subtasks'] = total_subtasks
    stats['completed_subtasks'] = completed_subtasks
    
    return jsonify(stats)

# Log Endpoints

@app.route('/api/logs/orchestrator', methods=['GET'])
def get_orchestrator_logs():
    """Get orchestrator logs with pagination"""
    lines = int(request.args.get('lines', 100))
    offset = int(request.args.get('offset', 0))
    
    log_lines = read_log_tail(ORCHESTRATOR_LOG_FILE, lines + offset)
    
    if offset > 0:
        log_lines = log_lines[:-offset] if offset < len(log_lines) else []
    
    return jsonify({
        'logs': log_lines[-lines:],
        'total_lines': len(log_lines)
    })

@app.route('/api/logs/claude', methods=['GET'])
def get_claude_logs():
    """Get Claude automation logs"""
    lines = int(request.args.get('lines', 100))
    
    log_lines = read_log_tail(CLAUDE_LOG_FILE, lines)
    
    return jsonify({
        'logs': log_lines,
        'total_lines': len(log_lines)
    })

@app.route('/api/logs/stream', methods=['GET'])
def stream_logs():
    """Stream logs in real-time using Server-Sent Events"""
    log_file = request.args.get('source', 'orchestrator')
    
    if log_file == 'orchestrator':
        file_path = ORCHESTRATOR_LOG_FILE
    elif log_file == 'claude':
        file_path = CLAUDE_LOG_FILE
    else:
        return jsonify({'error': 'Invalid log source'}), 400
    
    def generate():
        # Start with existing content
        with open(file_path, 'r') as f:
            f.seek(0, 2)  # Go to end of file
            while True:
                line = f.readline()
                if line:
                    yield f"data: {json.dumps({'log': line.strip()})}\n\n"
                else:
                    import time
                    time.sleep(0.5)
    
    return Response(generate(), mimetype='text/event-stream')

# Test Results Endpoints

@app.route('/api/tests/history', methods=['GET'])
def get_test_history():
    """Get test execution history"""
    test_history = read_json_file(TEST_HISTORY_FILE, [])
    
    # Sort by timestamp (most recent first)
    test_history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    return jsonify({
        'test_runs': test_history[:50],  # Last 50 test runs
        'total_runs': len(test_history)
    })

@app.route('/api/tests/latest', methods=['GET'])
def get_latest_tests():
    """Get the most recent test results"""
    test_history = read_json_file(TEST_HISTORY_FILE, [])
    
    if not test_history:
        return jsonify({'message': 'No test results found'}), 404
    
    # Get the most recent test run
    test_history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    latest = test_history[0]
    
    return jsonify(latest)

# System Control Endpoints (Optional - Use with caution)

@app.route('/api/orchestrator/status', methods=['GET'])
def get_orchestrator_status():
    """Get orchestrator process status"""
    try:
        # Check if orchestrator process is running
        result = subprocess.run(['pgrep', '-f', 'task_orchestrator'], capture_output=True, text=True)
        is_running = result.returncode == 0
        
        return jsonify({
            'running': is_running,
            'pid': result.stdout.strip() if is_running else None
        })
    except Exception as e:
        logger.error(f"Error checking orchestrator status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/orchestrator/start', methods=['POST'])
def start_orchestrator():
    """Start the orchestrator process"""
    try:
        # Check if already running
        status_result = subprocess.run(['pgrep', '-f', 'task_orchestrator'], capture_output=True)
        if status_result.returncode == 0:
            return jsonify({'message': 'Orchestrator already running'}), 200
        
        # Start orchestrator in background
        process = subprocess.Popen(
            ['python', 'task_orchestrator_enhanced.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        
        return jsonify({
            'message': 'Orchestrator started',
            'pid': process.pid
        }), 202
        
    except Exception as e:
        logger.error(f"Error starting orchestrator: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/orchestrator/stop', methods=['POST'])
def stop_orchestrator():
    """Stop the orchestrator process"""
    try:
        result = subprocess.run(['pkill', '-f', 'task_orchestrator'], capture_output=True)
        
        if result.returncode == 0:
            return jsonify({'message': 'Orchestrator stopped'}), 200
        else:
            return jsonify({'message': 'Orchestrator not running'}), 200
            
    except Exception as e:
        logger.error(f"Error stopping orchestrator: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Task Master Integration Endpoints (Direct implementation)

@app.route('/api/taskmaster/show/<string:task_id>', methods=['GET'])
def taskmaster_show_task(task_id: str):
    """Get detailed task information via Task Master"""
    try:
        # Read tasks data directly
        tasks_data = read_json_file(TASKS_FILE, {"tasks": []})
        
        # Find the task
        for task in tasks_data.get("tasks", []):
            if str(task.get("id")) == task_id:
                # Format the output similar to task_master_wrapper.py show command
                status_emoji = {
                    "pending": "⏳",
                    "in_progress": "🔄", 
                    "completed": "✅",
                    "failed": "❌"
                }.get(task.get("status", "pending"), "❓")
                
                result = {
                    "task_id": task_id,
                    "name": task.get("name", "Unnamed Task"),
                    "description": task.get("description", ""),
                    "status": task.get("status", "pending"),
                    "status_emoji": status_emoji,
                    "priority": task.get("priority", "medium"),
                    "subtasks": task.get("subtasks", []),
                    "started_at": task.get("started_at"),
                    "completed_at": task.get("completed_at"),
                    "created_at": task.get("created_at"),
                    "updated_at": task.get("updated_at")
                }
                
                # Add subtask progress
                subtasks = task.get("subtasks", [])
                if subtasks:
                    completed_subtasks = sum(1 for st in subtasks if st.get("status") == "completed")
                    result["subtask_progress"] = {
                        "total": len(subtasks),
                        "completed": completed_subtasks,
                        "percentage": (completed_subtasks / len(subtasks) * 100) if subtasks else 0
                    }
                
                return jsonify({
                    "success": True,
                    "task": result,
                    "stdout": f"Task {task_id}: {task.get('name', 'Unnamed Task')}\nStatus: {task.get('status', 'pending')}\nDescription: {task.get('description', '')}"
                })
        
        return jsonify({
            "success": False,
            "error": f"Task '{task_id}' not found",
            "stdout": f"Error: Task '{task_id}' not found"
        }), 404
        
    except Exception as e:
        logger.error(f"Error in taskmaster show: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "stdout": f"Error: {str(e)}"
        }), 500

@app.route('/api/taskmaster/list', methods=['GET'])
def taskmaster_list_tasks():
    """List all tasks via Task Master"""
    try:
        # Read tasks data directly
        tasks_data = read_json_file(TASKS_FILE, {"tasks": []})
        status_filter = request.args.get('status')
        show_details = request.args.get('details', 'false').lower() == 'true'
        
        tasks = []
        for task in tasks_data.get("tasks", []):
            if status_filter and task.get("status") != status_filter:
                continue
                
            status_emoji = {
                "pending": "⏳",
                "in_progress": "🔄",
                "completed": "✅", 
                "failed": "❌"
            }.get(task.get("status", "pending"), "❓")
            
            task_info = {
                "id": task["id"],
                "name": task.get("name", "Unnamed Task"),
                "status": task.get("status", "pending"),
                "status_emoji": status_emoji,
                "priority": task.get("priority", "medium")
            }
            
            if show_details:
                task_info["description"] = task.get("description", "")
                task_info["started_at"] = task.get("started_at")
                task_info["completed_at"] = task.get("completed_at")
            
            # Subtask information
            subtasks = task.get("subtasks", [])
            if subtasks:
                completed_subtasks = sum(1 for st in subtasks if st.get("status") == "completed")
                task_info["subtasks"] = {
                    "total": len(subtasks),
                    "completed": completed_subtasks,
                    "percentage": (completed_subtasks / len(subtasks) * 100) if subtasks else 0
                }
                
                if show_details:
                    task_info["subtask_details"] = subtasks
            
            tasks.append(task_info)
        
        return jsonify({
            "success": True,
            "tasks": tasks,
            "total": len(tasks)
        })
        
    except Exception as e:
        logger.error(f"Error in taskmaster list: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/taskmaster/status', methods=['GET'])
def taskmaster_project_status():
    """Get project progress status via Task Master"""
    try:
        # Read tasks data directly
        tasks_data = read_json_file(TASKS_FILE, {"tasks": []})
        
        total_tasks = len(tasks_data.get("tasks", []))
        if total_tasks == 0:
            return jsonify({
                "success": True,
                "message": "No tasks registered",
                "stats": {
                    "total_tasks": 0,
                    "progress": 0
                }
            })
        
        # Calculate statistics
        status_counts = {
            "pending": 0,
            "in_progress": 0, 
            "completed": 0,
            "failed": 0
        }
        
        total_subtasks = 0
        completed_subtasks = 0
        
        for task in tasks_data.get("tasks", []):
            status = task.get("status", "pending")
            status_counts[status] = status_counts.get(status, 0) + 1
            
            subtasks = task.get("subtasks", [])
            total_subtasks += len(subtasks)
            completed_subtasks += sum(1 for st in subtasks if st.get("status") == "completed")
        
        # Calculate progress
        completed_tasks = status_counts["completed"]
        task_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        subtask_progress = (completed_subtasks / total_subtasks * 100) if total_subtasks > 0 else 0
        
        stats = {
            "total_tasks": total_tasks,
            "task_counts": status_counts,
            "task_progress": round(task_progress, 1),
            "total_subtasks": total_subtasks,
            "completed_subtasks": completed_subtasks,
            "subtask_progress": round(subtask_progress, 1)
        }
        
        # Add test history if available
        test_history_file = PROJECT_ROOT / "logs" / "test_history.json"
        if test_history_file.exists():
            try:
                test_history = read_json_file(test_history_file, {})
                stats["test_stats"] = {
                    "total_runs": test_history.get("total_runs", 0),
                    "total_passes": test_history.get("total_passes", 0),
                    "total_failures": test_history.get("total_failures", 0),
                    "last_run": test_history.get("last_run")
                }
            except Exception:
                pass
        
        return jsonify({
            "success": True,
            "stats": stats
        })
        
    except Exception as e:
        logger.error(f"Error in taskmaster status: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/taskmaster/reset', methods=['POST'])
def taskmaster_reset_task():
    """Reset task status via Task Master"""
    try:
        data = request.get_json() or {}
        task_id = data.get('task_id')
        subtask_id = data.get('subtask_id')
        
        # Read tasks data directly
        tasks_data = read_json_file(TASKS_FILE, {"tasks": []})
        
        task_found = False
        for task in tasks_data.get("tasks", []):
            if str(task.get("id")) == str(task_id):
                if subtask_id:
                    # Reset specific subtask
                    for subtask in task.get("subtasks", []):
                        if str(subtask.get("id")) == str(subtask_id):
                            subtask["status"] = "pending"
                            subtask["failure_count"] = 0
                            task_found = True
                            break
                else:
                    # Reset entire task
                    task["status"] = "pending"
                    task["failure_count"] = 0
                    task.pop("started_at", None)
                    task.pop("completed_at", None)
                    
                    # Reset all subtasks too
                    for subtask in task.get("subtasks", []):
                        subtask["status"] = "pending"
                        subtask["failure_count"] = 0
                    
                    task_found = True
                break
        
        if task_found:
            # Save the updated data
            if write_json_file(TASKS_FILE, tasks_data):
                return jsonify({
                    "success": True,
                    "message": f"Reset {'subtask' if subtask_id else 'task'} status successfully"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Failed to save updated task data"
                }), 500
        else:
            return jsonify({
                "success": False,
                "error": f"Task {'subtask' if subtask_id else 'task'} not found"
            }), 404
            
    except Exception as e:
        logger.error(f"Error in taskmaster reset: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/taskmaster/run-tests', methods=['POST'])
def taskmaster_run_tests():
    """Run tests for a specific task"""
    try:
        data = request.get_json() or {}
        task_id = data.get('task_id')
        
        if not task_id:
            return jsonify({
                "success": False,
                "error": "task_id is required"
            }), 400
        
        # Simple test simulation - replace with actual test execution
        # For now, just return a mock success result
        return jsonify({
            "success": True,
            "exit_code": 0,
            "stdout": f"Mock test execution for task {task_id} completed successfully",
            "stderr": "",
            "task_id": task_id,
            "note": "This is a mock implementation. Replace with actual test execution."
        })
        
    except Exception as e:
        logger.error(f"Error running tests for task {task_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "task_id": task_id
        }), 500

# Add debug route to list all registered routes
@app.route('/api/debug/routes', methods=['GET'])
def debug_routes():
    """Debug endpoint to list all registered routes"""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'rule': str(rule)
        })
    return jsonify({
        "routes": routes,
        "total": len(routes)
    })

# Error handlers

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Main execution
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Dashboard API Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5002, help='Port to listen on')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    logger.info(f"Starting Dashboard API Server on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)