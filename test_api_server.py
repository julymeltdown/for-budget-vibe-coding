#!/usr/bin/env python3
"""
Simple Test API Server for Task Master endpoints
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
import time
from pathlib import Path
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent
TASKS_FILE = PROJECT_ROOT / "tasks.json"

def read_json_file(file_path: Path, default_data=None):
    """Read JSON file with error handling"""
    if not file_path.exists():
        return default_data if default_data is not None else {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return default_data if default_data is not None else {}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Test API Server is running',
        'version': '1.0.0'
    })

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
        "message": "Test API Server Routes",
        "routes": routes,
        "total": len(routes)
    })

@app.route('/api/taskmaster/show/<string:task_id>', methods=['GET'])
def taskmaster_show_task(task_id: str):
    """Get detailed task information"""
    try:
        # Read tasks data directly
        tasks_data = read_json_file(TASKS_FILE, {"tasks": []})
        
        # Find the task
        for task in tasks_data.get("tasks", []):
            if str(task.get("id")) == task_id:
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
                    "subtasks": task.get("subtasks", [])
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
        print(f"Error in taskmaster show: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "stdout": f"Error: {str(e)}"
        }), 500

@app.route('/api/taskmaster/list', methods=['GET'])
def taskmaster_list_tasks():
    """List all tasks"""
    try:
        tasks_data = read_json_file(TASKS_FILE, {"tasks": []})
        status_filter = request.args.get('status')
        
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
                "priority": task.get("priority", "medium"),
                "description": task.get("description", "")
            }
            
            tasks.append(task_info)
        
        return jsonify({
            "success": True,
            "tasks": tasks,
            "total": len(tasks)
        })
        
    except Exception as e:
        print(f"Error in taskmaster list: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/taskmaster/status', methods=['GET'])
def taskmaster_project_status():
    """Get project progress status"""
    try:
        tasks_data = read_json_file(TASKS_FILE, {"tasks": []})
        
        total_tasks = len(tasks_data.get("tasks", []))
        if total_tasks == 0:
            return jsonify({
                "success": True,
                "message": "No tasks registered",
                "stats": {"total_tasks": 0, "progress": 0}
            })
        
        # Calculate statistics
        status_counts = {"pending": 0, "in_progress": 0, "completed": 0, "failed": 0}
        
        for task in tasks_data.get("tasks", []):
            status = task.get("status", "pending")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        completed_tasks = status_counts["completed"]
        task_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        stats = {
            "total_tasks": total_tasks,
            "task_counts": status_counts,
            "task_progress": round(task_progress, 1)
        }
        
        return jsonify({
            "success": True,
            "stats": stats
        })
        
    except Exception as e:
        print(f"Error in taskmaster status: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/taskmaster/run-tests', methods=['POST'])
def taskmaster_run_tests():
    """Run tests for a specific task (mock implementation)"""
    try:
        data = request.get_json() or {}
        task_id = data.get('task_id')
        
        if not task_id:
            return jsonify({
                "success": False,
                "error": "task_id is required"
            }), 400
        
        # Mock test execution
        return jsonify({
            "success": True,
            "exit_code": 0,
            "stdout": f"Mock test execution for task {task_id} completed successfully",
            "stderr": "",
            "task_id": task_id,
            "note": "This is a mock test implementation"
        })
        
    except Exception as e:
        print(f"Error running tests for task {task_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "task_id": task_id
        }), 500

# Mock Claude Desktop API endpoints
@app.route('/api/automation/run', methods=['POST'])
def mock_claude_automation_run():
    """Mock Claude Desktop automation endpoint"""
    try:
        data = request.get_json() or {}
        
        print(f"=== MOCK CLAUDE AUTOMATION API CALLED ===")
        print(f"Received data: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        prompt = data.get('prompt')
        if not prompt:
            return jsonify({
                "success": False,
                "error": "Missing required field: prompt"
            }), 400
        
        # Mock successful response
        result = {
            "success": True,
            "task_id": f"mock_task_{int(time.time())}",
            "status": "started",
            "message": "Mock Claude automation started successfully",
            "prompt_received": prompt[:100] + "..." if len(prompt) > 100 else prompt,
            "project_name": data.get('project_name', 'unknown'),
            "wait_for_continue": data.get('wait_for_continue', False),
            "create_new_chat": data.get('create_new_chat', False)
        }
        
        print(f"Mock response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in mock Claude automation: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/automation/status/<string:task_id>', methods=['GET'])
def mock_claude_automation_status(task_id: str):
    """Mock Claude Desktop automation status endpoint"""
    try:
        print(f"=== MOCK CLAUDE STATUS CHECK ===")
        print(f"Checking status for task: {task_id}")
        
        # Mock status response
        result = {
            "success": True,
            "task_id": task_id,
            "status": "completed",  # Always return completed for testing
            "progress": 100,
            "message": "Mock task completed successfully",
            "completed_at": datetime.now().isoformat(),
            "results": {
                "files_created": ["mock_file1.py", "mock_file2.py"],
                "tests_passed": True,
                "implementation_successful": True
            }
        }
        
        print(f"Mock status response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in mock status check: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Original tasks API for compatibility
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks with optional filtering"""
    try:
        status_filter = request.args.get('status')
        tasks_data = read_json_file(TASKS_FILE, {"tasks": []})
        tasks_list = tasks_data.get("tasks", [])
        
        # Apply filters
        if status_filter:
            tasks_list = [task for task in tasks_list if task.get("status") == status_filter]
        
        return jsonify({
            'tasks': tasks_list,
            'total': len(tasks_list)
        })
    except Exception as e:
        print(f"Error getting tasks: {str(e)}")
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
                task_found = True
                break
        
        if not task_found:
            return jsonify({'error': 'Task not found'}), 404
        
        # Save updated data
        with open(TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(tasks_data, f, indent=2)
        
        return jsonify({'message': 'Task status updated'}), 200
            
    except Exception as e:
        print(f"Error updating task status: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test API Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5003, help='Port to listen on')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    print(f"Starting Test API Server on {args.host}:{args.port}")
    print(f"Tasks file: {TASKS_FILE}")
    print(f"Available endpoints:")
    print(f"  - GET  /health")
    print(f"  - GET  /api/debug/routes")
    print(f"  - GET  /api/taskmaster/show/<task_id>")
    print(f"  - GET  /api/taskmaster/list")
    print(f"  - GET  /api/taskmaster/status")
    print(f"  - POST /api/taskmaster/run-tests")
    print(f"  - GET  /api/tasks")
    print(f"  - PUT  /api/tasks/<task_id>/status")
    print(f"  - POST /api/automation/run (Mock Claude API)")
    print(f"  - GET  /api/automation/status/<task_id> (Mock Claude API)")
    
    app.run(host=args.host, port=args.port, debug=args.debug)
