import os
import sys
import logging
import argparse
import json
import time
import subprocess # TestRunner와 git_commit에 필요
import re # TestRunner에 필요
import platform # OS 감지용
from datetime import datetime

# 현재 파일의 디렉토리를 기준으로 모듈 임포트 경로 설정 (선택적, 더 나은 방법은 PYTHONPATH 설정 또는 패키지화)
# sys.path.append(os.path.dirname(os.path.abspath(__file__))) # 현재 구조에서는 불필요할 수 있음

from claude_desktop_automation import ClaudeDesktopAutomation # 수정된 임포트
from code_analyzer import CodeAnalyzer
from notification_manager import NotificationManager
from task_master_mcp_client import TaskMasterMCPClient

# 로그 디렉토리 생성
LOGS_DIR = "logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# 로깅 설정
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


# TestRunner 클래스를 여기에 통합하거나 별도 파일로 분리 후 임포트
# 여기서는 통합된 형태로 제공 (별도 파일 test_runner.py 권장)
class TestRunner:
    def __init__(self, test_config=None, project_root=".", project_type=None): # project_type 추가
        self.default_config = {
            "test_command": "pytest", # 또는 "mvn test", "npm test" 등
            "test_args": ["-v"],
            "test_dir": "tests", # project_root 기준 상대 경로
            "success_pattern": r"(\d+)\s+(?:passed|test(?:s)? ran)", # pytest, junit 등 고려
            "failure_pattern": r"(\d+)\s+failed",
            "error_pattern": r"(\d+)\s+error(?:s)?", # pytest는 errors, junit은 failures에 포함될 수 있음
            "test_history_file": os.path.join(LOGS_DIR, "test_history.json") # 로그 디렉토리에 저장
        }
        self.config = self.default_config.copy()
        if test_config: # 외부 설정 주입 가능
            self.config.update(test_config)

        self.project_root = os.path.abspath(project_root)
        self.project_type = project_type
        
        # OS 감지
        self.is_windows = platform.system() == "Windows"
        
        # project_type에 따라 test_command 조정
        if self.project_type == "gradle" and self.is_windows:
            # Windows에서는 gradlew.bat 사용
            if "test_command_windows" in self.config:
                self.config["test_command"] = self.config["test_command_windows"]
        elif self.project_type == "maven" and self.is_windows:
            # Windows에서는 mvn.cmd 사용
            if "test_command_windows" in self.config:
                self.config["test_command"] = self.config["test_command_windows"]
                
        # gradle/gradlew 경로 확인 및 설정
        if self.project_type == "gradle":
            gradlew_path = os.path.join(self.project_root, self.config["test_command"])
            if os.path.exists(gradlew_path):
                self.config["test_command"] = gradlew_path
                # 실행 권한 부여 (Unix-like 시스템)
                if not self.is_windows:
                    try:
                        os.chmod(gradlew_path, 0o755)
                    except Exception as e:
                        logger.warning(f"gradlew 실행 권한 설정 실패: {e}")
        
        self.test_dir_abs = os.path.join(self.project_root, self.config["test_dir"]) if self.config.get("test_dir") else self.project_root
        
        self.test_history = self._load_test_history()
        logger.info(f"TestRunner 초기화 완료 (프로젝트 타입: {self.project_type})")

    def _load_test_history(self):
        if os.path.exists(self.config["test_history_file"]):
            try:
                with open(self.config["test_history_file"], 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"테스트 이력 로드 실패: {e}")
        return {"tasks": {}, "last_run": None, "total_runs": 0, "total_passes": 0, "total_failures": 0}

    def _save_test_history(self):
        try:
            with open(self.config["test_history_file"], 'w') as f:
                json.dump(self.test_history, f, indent=2)
            logger.info(f"테스트 이력 저장 완료: {self.config['test_history_file']}")
        except Exception as e:
            logger.error(f"테스트 이력 저장 실패: {e}")

    def run_tests(self, task_id=None, subtask_id=None, specific_test_files=None):
        # test_command가 'mvn' 등을 포함할 수 있으므로, config에서 test