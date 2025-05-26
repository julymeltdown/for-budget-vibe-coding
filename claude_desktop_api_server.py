#!/usr/bin/env python3
"""
Claude Desktop Automation API Server
Flask wrapper for claude_desktop_automation.py to enable HTTP API access
"""

from flask import Flask, jsonify, request
import logging
import json
import threading
import queue
import uuid
from datetime import datetime
from pathlib import Path
from claude_desktop_automation import ClaudeDesktopAutomation

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global automation instance
claude_automation = None

# Task queue for async execution
task_queue = queue.Queue()
task_results = {}
task_status = {}

# Background worker thread
def automation_worker():
    """Background worker to process automation tasks"""
    while True:
        try:
            task = task_queue.get(timeout=1)
            if task is None:
                break
                
            task_id = task['id']
            task_status[task_id] = 'running'
            
            try:
                # Execute automation
                result = claude_automation.run_automation(
                    input_text_content=task['prompt'],
                    wait_for_continue=task.get('wait_for_continue', True),
                    create_new_chat=task.get('create_new_chat', False),
                    project_name=task.get('project_name'),
                    conversation_summary_for_new_chat=task.get('context_summary', '')
                )
                
                task_results[task_id] = {
                    'success': result,
                    'completed_at': datetime.now().isoformat(),
                    'error': None
                }
                task_status[task_id] = 'completed'
                
            except Exception as e:
                logger.error(f"Error processing task {task_id}: {str(e)}")
                task_results[task_id] = {
                    'success': False,
                    'completed_at': datetime.now().isoformat(),
                    'error': str(e)
                }
                task_status[task_id] = 'failed'
                
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"Worker thread error: {str(e)}")

# Initialize automation on startup
def initialize_automation():
    global claude_automation
    try:
        claude_automation = ClaudeDesktopAutomation()
        logger.info("Claude Desktop Automation initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Claude Desktop Automation: {str(e)}")
        return False

# API Endpoints

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'automation_initialized': claude_automation is not None,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/automation/run', methods=['POST'])
def run_automation_api():
    """
    Run Claude Desktop automation
    
    Request body:
    {
        "prompt": "string",
        "wait_for_continue": bool (optional, default: true),
        "create_new_chat": bool (optional, default: false),
        "project_name": "string" (optional),
        "context_summary": "string" (optional)
    }
    """
    if not claude_automation:
        return jsonify({'error': 'Automation not initialized'}), 503
    
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'prompt' not in data:
            return jsonify({'error': 'Missing required field: prompt'}), 400
        
        # Create task
        task_id = str(uuid.uuid4())
        task = {
            'id': task_id,
            'prompt': data['prompt'],
            'wait_for_continue': data.get('wait_for_continue', True),
            'create_new_chat': data.get('create_new_chat', False),
            'project_name': data.get('project_name'),
            'context_summary': data.get('context_summary', ''),
            'created_at': datetime.now().isoformat()
        }
        
        # Add to queue
        task_queue.put(task)
        task_status[task_id] = 'queued'
        
        return jsonify({
            'task_id': task_id,
            'status': 'queued',
            'message': 'Automation task queued for execution'
        }), 202
        
    except Exception as e:
        logger.error(f"Error creating automation task: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/automation/status/<task_id>', methods=['GET'])
def get_task_status_api(task_id):
    """Get status of an automation task"""
    if task_id not in task_status:
        return jsonify({'error': 'Task not found'}), 404
    
    response = {
        'task_id': task_id,
        'status': task_status[task_id]
    }
    
    if task_id in task_results:
        response['result'] = task_results[task_id]
    
    return jsonify(response)

@app.route('/api/automation/create_new_chat', methods=['POST'])
def create_new_chat_api():
    """Create a new chat via projects"""
    if not claude_automation:
        return jsonify({'error': 'Automation not initialized'}), 503
    
    try:
        data = request.get_json()
        project_name = data.get('project_name')
        context_summary = data.get('context_summary', '')
        
        if not project_name:
            return jsonify({'error': 'Missing required field: project_name'}), 400
        
        success = claude_automation.create_new_chat_via_projects(
            project_name=project_name,
            context_summary=context_summary
        )
        
        return jsonify({
            'success': success,
            'message': 'New chat created' if success else 'Failed to create new chat'
        })
        
    except Exception as e:
        logger.error(f"Error creating new chat: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/automation/check_max_length', methods=['GET'])
def check_max_length_api():
    """Check if max length message is displayed"""
    if not claude_automation:
        return jsonify({'error': 'Automation not initialized'}), 503
    
    try:
        is_max_length = claude_automation.check_max_length_message()
        return jsonify({
            'max_length_detected': is_max_length,
            'current_tokens': getattr(claude_automation, 'current_conversation_tokens', 0)
        })
    except Exception as e:
        logger.error(f"Error checking max length: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/automation/window_status', methods=['GET'])
def get_window_status_api():
    """Get Claude Desktop window status"""
    if not claude_automation:
        return jsonify({'error': 'Automation not initialized'}), 503
    
    try:
        is_active = claude_automation.window_active
        window_found = claude_automation.activate_window()
        
        return jsonify({
            'window_active': is_active,
            'window_found': window_found,
            'window_title': claude_automation.window_title
        })
    except Exception as e:
        logger.error(f"Error getting window status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/automation/tokens', methods=['GET'])
def get_token_count_api():
    """Get current conversation token count"""
    if not claude_automation:
        return jsonify({'error': 'Automation not initialized'}), 503
    
    return jsonify({
        'current_tokens': getattr(claude_automation, 'current_conversation_tokens', 0),
        'max_tokens': getattr(claude_automation, 'max_tokens_per_conversation', 90000),
        'percentage_used': (getattr(claude_automation, 'current_conversation_tokens', 0) / 
                          getattr(claude_automation, 'max_tokens_per_conversation', 90000) * 100)
    })

@app.route('/api/automation/reset_tokens', methods=['POST'])
def reset_token_count_api():
    """Reset conversation token count"""
    if not claude_automation:
        return jsonify({'error': 'Automation not initialized'}), 503
    
    if hasattr(claude_automation, 'current_conversation_tokens'):
        claude_automation.current_conversation_tokens = 0
        return jsonify({
            'success': True,
            'message': 'Token count reset',
            'current_tokens': 0
        })
    else:
        return jsonify({'error': 'Token counting not implemented'}), 501

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Initialization
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Claude Desktop Automation API Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5001, help='Port to listen on')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Initialize automation
    if not initialize_automation():
        logger.error("Failed to initialize automation. Exiting.")
        exit(1)
    
    # Start worker thread
    worker_thread = threading.Thread(target=automation_worker, daemon=True)
    worker_thread.start()
    logger.info("Worker thread started")
    
    # Start Flask app
    logger.info(f"Starting Claude Desktop Automation API Server on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)