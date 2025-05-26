#!/usr/bin/env python
"""
Project Setup Validation Script
Verifies that configuration files and environment are properly set up.
"""

import os
import sys
import json
import subprocess
import platform


def check_file_exists(filepath, description):
    """Check if file exists"""
    exists = os.path.exists(filepath)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {filepath}")
    return exists


def check_command_exists(command, description):
    """Check if command is executable"""
    try:
        result = subprocess.run([command, "--version"], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        exists = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        exists = False
    
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {command}")
    return exists


def validate_json_file(filepath):
    """Validate JSON file"""
    if not os.path.exists(filepath):
        return False, "File does not exist"
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return True, data
    except json.JSONDecodeError as e:
        return False, f"JSON parsing error: {e}"
    except Exception as e:
        return False, f"File read error: {e}"


def main():
    print("=" * 60)
    print("AI Automation Project Setup Validation")
    print("=" * 60)
    print()
    
    errors = []
    warnings = []
    
    # 1. Check required files
    print("### Required Files Check ###")
    required_files = [
        ("config.json", "Main configuration file"),
        ("tasks.json", "Task definition file"),
        ("claude_desktop_config.json", "Claude Desktop configuration"),
        ("notification_config.json", "Notification configuration"),
        ("requirements.txt", "Python package list")
    ]
    
    for filename, desc in required_files:
        if not check_file_exists(filename, desc):
            errors.append(f"{desc} missing: {filename}")
    print()
    
    # 2. Check directories
    print("### Directory Check ###")
    directories = [
        ("logs", "Log directory"),
        ("assets", "Button images directory"),
        ("venv", "Python virtual environment")
    ]
    
    for dirname, desc in directories:
        check_file_exists(dirname, desc)
        if not os.path.exists(dirname) and dirname != "venv":
            try:
                os.makedirs(dirname)
                print(f"  → Created {dirname} directory.")
            except Exception as e:
                errors.append(f"Failed to create {dirname} directory: {e}")
    print()
    
    # 3. Validate configuration files
    print("### Configuration File Validation ###")
    
    # Validate config.json
    valid, config_data = validate_json_file("config.json")
    if valid:
        print("✅ config.json valid")
        project_type = config_data.get("project_type", "unknown")
        print(f"  - Project type: {project_type}")
        
        # Check test commands by project type
        if project_type in ["gradle", "maven", "golang", "python"]:
            test_config = config_data.get("test_runner_config", {}).get(project_type, {})
            test_command = test_config.get("test_command", "")
            
            if project_type == "gradle":
                is_windows = platform.system() == "Windows"
                if is_windows:
                    test_command = test_config.get("test_command_windows", test_command)
                    
                # Check gradlew file
                gradlew_path = os.path.join(config_data.get("project_dir", "."), test_command)
                if not check_file_exists(gradlew_path, f"Gradle wrapper ({test_command})"):
                    errors.append(f"Gradle wrapper not found: {gradlew_path}")
            
            elif project_type == "maven":
                if not check_command_exists("mvn", "Maven"):
                    errors.append("Maven not installed or not in PATH")
            
            elif project_type == "golang":
                if not check_command_exists("go", "Go"):
                    errors.append("Go not installed or not in PATH")
            
            elif project_type == "python":
                if not check_command_exists("pytest", "pytest"):
                    warnings.append("pytest not installed. Run 'pip install pytest'")
    else:
        errors.append(f"config.json error: {config_data}")
    
    # Validate tasks.json
    valid, tasks_data = validate_json_file("tasks.json")
    if valid:
        print("✅ tasks.json valid")
        if isinstance(tasks_data, dict):
            task_count = len(tasks_data.get("tasks", []))
            print(f"  - Number of tasks: {task_count}")
        elif isinstance(tasks_data, list):
            print(f"  - Number of tasks: {len(tasks_data)}")
    else:
        errors.append(f"tasks.json error: {tasks_data}")
    print()
    
    # 4. Check button images
    print("### Claude Desktop Setup Check ###")
    button_images = [
        "assets/continue_button.png",
        "assets/new_chat_button.png"
    ]
    
    buttons_exist = all(check_file_exists(img, os.path.basename(img)) for img in button_images)
    if not buttons_exist:
        warnings.append("Button images missing. Run 'python claude_desktop_automation.py --setup'")
    print()
    
    # 5. Check Python packages
    print("### Python Package Check ###")
    try:
        import pyautogui
        print("✅ pyautogui installed")
    except ImportError:
        errors.append("pyautogui not installed")
    
    try:
        import cv2
        print("✅ opencv-python installed")
    except ImportError:
        warnings.append("opencv-python not installed")
    
    try:
        import numpy
        print("✅ numpy installed")
    except ImportError:
        errors.append("numpy not installed")
    print()
    
    # 6. Summary
    print("=" * 60)
    print("### Validation Results ###")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print()
    
    if errors:
        print("❌ Please fix the following errors:")
        for error in errors:
            print(f"  - {error}")
        print()
    
    if warnings:
        print("⚠️  Please check the following warnings:")
        for warning in warnings:
            print(f"  - {warning}")
        print()
    
    if not errors and not warnings:
        print("✅ All settings are properly configured!")
        print("\nStart with the following commands:")
        print("  python task_master_wrapper.py status")
        print("  python task_master_wrapper.py list")
        print("  python task_master_wrapper.py run")
    
    return len(errors)


if __name__ == "__main__":
    sys.exit(main())
