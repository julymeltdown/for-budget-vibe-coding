#!/usr/bin/env python
"""
프로젝트 설정 검증 스크립트
설정 파일과 환경이 올바르게 구성되었는지 확인합니다.
"""

import os
import sys
import json
import subprocess
import platform


def check_file_exists(filepath, description):
    """파일 존재 여부 확인"""
    exists = os.path.exists(filepath)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {filepath}")
    return exists


def check_command_exists(command, description):
    """명령어 실행 가능 여부 확인"""
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
    """JSON 파일 유효성 검사"""
    if not os.path.exists(filepath):
        return False, "파일이 존재하지 않습니다"
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return True, data
    except json.JSONDecodeError as e:
        return False, f"JSON 파싱 오류: {e}"
    except Exception as e:
        return False, f"파일 읽기 오류: {e}"


def main():
    print("=" * 60)
    print("AI 자동화 프로젝트 설정 검증")
    print("=" * 60)
    print()
    
    errors = []
    warnings = []
    
    # 1. 필수 파일 확인
    print("### 필수 파일 확인 ###")
    required_files = [
        ("config.json", "메인 설정 파일"),
        ("tasks.json", "태스크 정의 파일"),
        ("claude_desktop_config.json", "Claude Desktop 설정"),
        ("notification_config.json", "알림 설정"),
        ("requirements.txt", "Python 패키지 목록")
    ]
    
    for filename, desc in required_files:
        if not check_file_exists(filename, desc):
            errors.append(f"{desc}이(가) 없습니다: {filename}")
    print()
    
    # 2. 디렉토리 확인
    print("### 디렉토리 확인 ###")
    directories = [
        ("logs", "로그 디렉토리"),
        ("assets", "버튼 이미지 디렉토리"),
        ("venv", "Python 가상환경")
    ]
    
    for dirname, desc in directories:
        check_file_exists(dirname, desc)
        if not os.path.exists(dirname) and dirname != "venv":
            try:
                os.makedirs(dirname)
                print(f"  → {dirname} 디렉토리를 생성했습니다.")
            except Exception as e:
                errors.append(f"{dirname} 디렉토리 생성 실패: {e}")
    print()
    
    # 3. 설정 파일 검증
    print("### 설정 파일 검증 ###")
    
    # config.json 검증
    valid, config_data = validate_json_file("config.json")
    if valid:
        print("✅ config.json 유효")
        project_type = config_data.get("project_type", "unknown")
        print(f"  - 프로젝트 타입: {project_type}")
        
        # 프로젝트 타입별 테스트 명령어 확인
        if project_type in ["gradle", "maven", "golang", "python"]:
            test_config = config_data.get("test_runner_config", {}).get(project_type, {})
            test_command = test_config.get("test_command", "")
            
            if project_type == "gradle":
                is_windows = platform.system() == "Windows"
                if is_windows:
                    test_command = test_config.get("test_command_windows", test_command)
                    
                # gradlew 파일 확인
                gradlew_path = os.path.join(config_data.get("project_dir", "."), test_command)
                if not check_file_exists(gradlew_path, f"Gradle wrapper ({test_command})"):
                    errors.append(f"Gradle wrapper가 없습니다: {gradlew_path}")
            
            elif project_type == "maven":
                if not check_command_exists("mvn", "Maven"):
                    errors.append("Maven이 설치되지 않았거나 PATH에 없습니다")
            
            elif project_type == "golang":
                if not check_command_exists("go", "Go"):
                    errors.append("Go가 설치되지 않았거나 PATH에 없습니다")
            
            elif project_type == "python":
                if not check_command_exists("pytest", "pytest"):
                    warnings.append("pytest가 설치되지 않았습니다. 'pip install pytest' 실행 필요")
    else:
        errors.append(f"config.json 오류: {config_data}")
    
    # tasks.json 검증
    valid, tasks_data = validate_json_file("tasks.json")
    if valid:
        print("✅ tasks.json 유효")
        if isinstance(tasks_data, dict):
            task_count = len(tasks_data.get("tasks", []))
            print(f"  - 태스크 수: {task_count}")
        elif isinstance(tasks_data, list):
            print(f"  - 태스크 수: {len(tasks_data)}")
    else:
        errors.append(f"tasks.json 오류: {tasks_data}")
    print()
    
    # 4. 버튼 이미지 확인
    print("### Claude Desktop 설정 확인 ###")
    button_images = [
        "assets/continue_button.png",
        "assets/new_chat_button.png"
    ]
    
    buttons_exist = all(check_file_exists(img, os.path.basename(img)) for img in button_images)
    if not buttons_exist:
        warnings.append("버튼 이미지가 없습니다. 'python claude_desktop_automation.py --setup' 실행 필요")
    print()
    
    # 5. Python 패키지 확인
    print("### Python 패키지 확인 ###")
    try:
        import pyautogui
        print("✅ pyautogui 설치됨")
    except ImportError:
        errors.append("pyautogui가 설치되지 않았습니다")
    
    try:
        import cv2
        print("✅ opencv-python 설치됨")
    except ImportError:
        warnings.append("opencv-python이 설치되지 않았습니다")
    
    try:
        import numpy
        print("✅ numpy 설치됨")
    except ImportError:
        errors.append("numpy가 설치되지 않았습니다")
    print()
    
    # 6. 결과 요약
    print("=" * 60)
    print("### 검증 결과 ###")
    print(f"오류: {len(errors)}개")
    print(f"경고: {len(warnings)}개")
    print()
    
    if errors:
        print("❌ 다음 오류를 해결해야 합니다:")
        for error in errors:
            print(f"  - {error}")
        print()
    
    if warnings:
        print("⚠️  다음 경고 사항을 확인하세요:")
        for warning in warnings:
            print(f"  - {warning}")
        print()
    
    if not errors and not warnings:
        print("✅ 모든 설정이 올바르게 구성되었습니다!")
        print("\n다음 명령어로 시작하세요:")
        print("  python task_master_wrapper.py status")
        print("  python task_master_wrapper.py list")
        print("  python task_master_wrapper.py run")
    
    return len(errors)


if __name__ == "__main__":
    sys.exit(main())