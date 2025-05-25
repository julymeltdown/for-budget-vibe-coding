# 통합 자동화 시스템 설계 및 구현

## 1. 시스템 구조

```
automated_dev_pipeline/
├── gui_automation/
│   ├── claude_desktop.py       # Claude Desktop GUI 자동화
│   └── assets/                 # 버튼 이미지 등 자산 파일
├── test_monitor/
│   ├── test_runner.py          # 테스트 실행 및 모니터링
│   ├── code_analyzer.py        # 코드 품질 및 임시처리 감지
│   └── test_history.py         # 테스트 실행 이력 관리
├── task_manager/
│   ├── task_orchestrator.py    # 태스크/서브태스크 관리
│   ├── git_integration.py      # Git 통합 (커밋, 브랜치 등)
│   └── task_parser.py          # 태스크 정의 파일 파싱
├── notification/
│   ├── slack_notifier.py       # Slack 알림
│   ├── telegram_notifier.py    # Telegram 알림
│   └── notification_manager.py # 알림 통합 관리
├── config/
│   ├── system_config.json      # 시스템 전체 설정
│   ├── gui_config.json         # GUI 자동화 설정
│   ├── test_config.json        # 테스트 설정
│   └── notification_config.json # 알림 설정
├── main.py                     # 메인 실행 파일
├── requirements.txt            # 의존성 패키지 목록
└── README.md                   # 사용 설명서
```

## 2. 주요 모듈 설계

### 2.1 GUI 자동화 모듈 (gui_automation/claude_desktop.py)

```python
import pyautogui
import time
import os
import logging
import json
from PIL import Image, ImageGrab
import cv2
import numpy as np

class ClaudeDesktopAutomation:
    def __init__(self, config_path=None):
        """Claude Desktop GUI 자동화 클래스 초기화"""
        # 기본 설정
        self.default_config = {
            "window_title": "Claude",
            "input_delay": 0.5,
            "screenshot_delay": 1.0,
            "max_retries": 3,
            "confidence_threshold": 0.7,
            "continue_button_text": "Continue",
            "new_chat_button_text": "New chat",
            "assets_dir": "assets",
            "continue_button_image": "continue_button.png",
            "new_chat_button_image": "new_chat_button.png"
        }
        
        # 설정 파일 로드
        self.config = self.default_config.copy()
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    self.config.update(user_config)
                logging.info(f"설정 파일 로드 완료: {config_path}")
            except Exception as e:
                logging.error(f"설정 파일 로드 실패: {e}")
        
        # 에셋 디렉토리 확인 및 생성
        self.assets_dir = self.config["assets_dir"]
        if not os.path.exists(self.assets_dir):
            os.makedirs(self.assets_dir)
            logging.info(f"에셋 디렉토리 생성: {self.assets_dir}")
        
        # 이미지 파일 경로
        self.continue_button_image = os.path.join(self.assets_dir, self.config["continue_button_image"])
        self.new_chat_button_image = os.path.join(self.assets_dir, self.config["new_chat_button_image"])
        
        # 창 활성화 여부 확인
        self.window_active = False
        
        logging.info("Claude Desktop 자동화 초기화 완료")
    
    def activate_window(self):
        """Claude Desktop 창을 활성화합니다."""
        try:
            # 창 제목으로 창 찾기
            window = pyautogui.getWindowsWithTitle(self.config["window_title"])
            if window:
                window[0].activate()
                time.sleep(1)  # 창이 활성화될 때까지 대기
                self.window_active = True
                logging.info("Claude Desktop 창 활성화 성공")
                return True
            else:
                logging.error(f"Claude Desktop 창을 찾을 수 없습니다. 창 제목: {self.config['window_title']}")
                return False
        except Exception as e:
            logging.error(f"창 활성화 중 오류 발생: {e}")
            return False
    
    def find_and_click_image(self, image_path, max_retries=None, confidence=None):
        """화면에서 이미지를 찾아 클릭합니다."""
        if max_retries is None:
            max_retries = self.config["max_retries"]
        
        if confidence is None:
            confidence = self.config["confidence_threshold"]
        
        if not os.path.exists(image_path):
            logging.error(f"이미지 파일을 찾을 수 없습니다: {image_path}")
            return False
        
        for attempt in range(max_retries):
            try:
                location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
                if location:
                    pyautogui.click(location)
                    logging.info(f"이미지 클릭 성공: {image_path}")
                    return True
                else:
                    logging.warning(f"이미지를 찾을 수 없습니다 ({attempt+1}/{max_retries}): {image_path}")
                    time.sleep(self.config["screenshot_delay"])
            except Exception as e:
                logging.error(f"이미지 찾기 중 오류 발생: {e}")
                time.sleep(self.config["screenshot_delay"])
        
        logging.error(f"이미지 찾기 실패 (최대 재시도 횟수 초과): {image_path}")
        return False
    
    def capture_and_save_button(self, button_name, region=None):
        """화면의 특정 영역을 캡처하여 버튼 이미지로 저장합니다."""
        try:
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                # 사용자에게 버튼 위치 지정 요청
                logging.info(f"{button_name} 버튼 위치를 지정해주세요. 5초 후 마우스 위치를 캡처합니다...")
                time.sleep(5)
                x, y = pyautogui.position()
                
                # 버튼 주변 영역 캡처 (100x50 픽셀)
                region = (x-50, y-25, 100, 50)
                screenshot = pyautogui.screenshot(region=region)
            
            # 이미지 저장
            if button_name == "continue":
                image_path = self.continue_button_image
            elif button_name == "new_chat":
                image_path = self.new_chat_button_image
            else:
                image_path = os.path.join(self.assets_dir, f"{button_name}_button.png")
            
            screenshot.save(image_path)
            logging.info(f"{button_name} 버튼 이미지 저장 완료: {image_path}")
            return True
        
        except Exception as e:
            logging.error(f"버튼 캡처 중 오류 발생: {e}")
            return False
    
    def input_text(self, text):
        """Claude Desktop 입력창에 텍스트를 입력합니다."""
        try:
            # 창이 활성화되어 있는지 확인
            if not self.window_active:
                if not self.activate_window():
                    return False
            
            # 텍스트 입력 (Ctrl+A로 기존 텍스트 선택 후 삭제)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(self.config["input_delay"])
            pyautogui.write(text)
            logging.info(f"텍스트 입력 완료: {text[:50]}..." if len(text) > 50 else f"텍스트 입력 완료: {text}")
            return True
        
        except Exception as e:
            logging.error(f"텍스트 입력 중 오류 발생: {e}")
            return False
    
    def press_enter(self):
        """Enter 키를 누릅니다."""
        try:
            pyautogui.press('enter')
            logging.info("Enter 키 입력 완료")
            return True
        except Exception as e:
            logging.error(f"Enter 키 입력 중 오류 발생: {e}")
            return False
    
    def click_continue_button(self):
        """'계속하기' 버튼을 클릭합니다."""
        logging.info("'계속하기' 버튼 찾기 시도...")
        return self.find_and_click_image(self.continue_button_image)
    
    def click_new_chat_button(self):
        """'새 채팅' 버튼을 클릭합니다."""
        logging.info("'새 채팅' 버튼 찾기 시도...")
        return self.find_and_click_image(self.new_chat_button_image)
    
    def setup_buttons(self):
        """버튼 이미지를 설정합니다."""
        logging.info("버튼 이미지 설정을 시작합니다...")
        
        # 계속하기 버튼 캡처
        logging.info("'계속하기' 버튼 위치를 지정해주세요.")
        self.capture_and_save_button("continue")
        
        # 새 채팅 버튼 캡처
        logging.info("'새 채팅' 버튼 위치를 지정해주세요.")
        self.capture_and_save_button("new_chat")
        
        logging.info("버튼 이미지 설정이 완료되었습니다.")
    
    def run_automation(self, input_text, wait_for_continue=True, create_new_chat=False):
        """자동화 작업을 실행합니다."""
        try:
            # 창 활성화
            if not self.activate_window():
                return False
            
            # 새 채팅 생성 (필요한 경우)
            if create_new_chat:
                if not self.click_new_chat_button():
                    logging.warning("새 채팅 생성 실패, 계속 진행합니다.")
                time.sleep(1)
            
            # 텍스트 입력
            if not self.input_text(input_text):
                return False
            
            # Enter 키 입력
            if not self.press_enter():
                return False
            
            # '계속하기' 버튼 대기 (필요한 경우)
            if wait_for_continue:
                logging.info("'계속하기' 버튼 대기 중...")
                max_wait_time = 60  # 최대 60초 대기
                wait_interval = 5   # 5초마다 확인
                
                for _ in range(max_wait_time // wait_interval):
                    time.sleep(wait_interval)
                    if self.click_continue_button():
                        logging.info("'계속하기' 버튼 클릭 성공")
                        break
                else:
                    logging.warning("'계속하기' 버튼을 찾을 수 없습니다. 시간 초과.")
            
            logging.info("자동화 작업 완료")
            return True
        
        except Exception as e:
            logging.error(f"자동화 작업 중 오류 발생: {e}")
            return False
```

### 2.2 테스트 모니터링 모듈 (test_monitor/test_runner.py)

```python
import subprocess
import os
import re
import logging
import json
import time
from pathlib import Path

class TestRunner:
    def __init__(self, config_path=None):
        """테스트 실행 및 모니터링 클래스 초기화"""
        # 기본 설정
        self.default_config = {
            "test_command": "pytest",
            "test_args": ["-v"],
            "max_retries": 5,
            "retry_delay": 2,
            "test_dir": "tests",
            "test_history_file": "test_history.json",
            "success_pattern": r"(\d+) passed",
            "failure_pattern": r"(\d+) failed",
            "error_pattern": r"(\d+) error"
        }
        
        # 설정 파일 로드
        self.config = self.default_config.copy()
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    self.config.update(user_config)
                logging.info(f"설정 파일 로드 완료: {config_path}")
            except Exception as e:
                logging.error(f"설정 파일 로드 실패: {e}")
        
        # 테스트 이력 파일 경로
        self.test_history_file = self.config["test_history_file"]
        
        # 테스트 이력 로드
        self.test_history = self._load_test_history()
        
        logging.info("테스트 러너 초기화 완료")
    
    def _load_test_history(self):
        """테스트 이력을 로드합니다."""
        if os.path.exists(self.test_history_file):
            try:
                with open(self.test_history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"테스트 이력 로드 실패: {e}")
        
        # 기본 이력 구조
        return {
            "tasks": {},
            "last_run": None,
            "total_runs": 0,
            "total_passes": 0,
            "total_failures": 0
        }
    
    def _save_test_history(self):
        """테스트 이력을 저장합니다."""
        try:
            with open(self.test_history_file, 'w') as f:
                json.dump(self.test_history, f, indent=2)
            logging.info(f"테스트 이력 저장 완료: {self.test_history_file}")
            return True
        except Exception as e:
            logging.error(f"테스트 이력 저장 실패: {e}")
            return False
    
    def run_tests(self, task_id=None, subtask_id=None, test_files=None):
        """테스트를 실행하고 결과를 반환합니다."""
        # 테스트 명령 구성
        cmd = [self.config["test_command"]] + self.config["test_args"]
        
        # 특정 테스트 파일만 실행
        if test_files:
            cmd.extend(test_files)
        else:
            cmd.append(self.config["test_dir"])
        
        try:
            # 테스트 실행
            logging.info(f"테스트 실행: {' '.join(cmd)}")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            
            # 테스트 결과 파싱
            output = stdout + stderr
            
            # 성공한 테스트 수
            success_match = re.search(self.config["success_pattern"], output)
            success_count = int(success_match.group(1)) if success_match else 0
            
            # 실패한 테스트 수
            failure_match = re.search(self.config["failure_pattern"], output)
            failure_count = int(failure_match.group(1)) if failure_match else 0
            
            # 에러 테스트 수
            error_match = re.search(self.config["error_pattern"], output)
            error_count = int(error_match.group(1)) if error_match else 0
            
            # 테스트 결과
            result = {
                "success": process.returncode == 0,
                "return_code": process.returncode,
                "success_count": success_count,
                "failure_count": failure_count,
                "error_count": error_count,
                "output": output,
                "timestamp": time.time()
            }
            
            # 테스트 이력 업데이트
            self._update_test_history(task_id, subtask_id, result)
            
            logging.info(f"테스트 결과: 성공={success_count}, 실패={failure_count}, 에러={error_count}")
            return result
        
        except Exception as e:
            logging.error(f"테스트 실행 중 오류 발생: {e}")
            result = {
                "success": False,
                "return_code": -1,
                "success_count": 0,
                "failure_count": 0,
                "error_count": 0,
                "output": str(e),
                "timestamp": time.time()
            }
            
            # 테스트 이력 업데이트
            self._update_test_history(task_id, subtask_id, result)
            
            return result
    
    def _update_test_history(self, task_id, subtask_id, result):
        """테스트 이력을 업데이트합니다."""
        # 전체 통계 업데이트
        self.test_history["total_runs"] += 1
        self.test_history["last_run"] = result["timestamp"]
        
        if result["success"]:
            self.test_history["total_passes"] += 1
        else:
            self.test_history["total_failures"] += 1
        
        # 태스크/서브태스크별 이력 업데이트
        if task_id:
            if task_id not in self.test_history["tasks"]:
                self.test_history["tasks"][task_id] = {"subtasks": {}, "runs": 0, "passes": 0, "failures": 0}
            
            task_history = self.test_history["tasks"][task_id]
            task_history["runs"] += 1
            
            if result["success"]:
                task_history["passes"] += 1
            else:
                task_history["failures"] += 1
            
            # 서브태스크별 이력 업데이트
            if subtask_id:
                if subtask_id not in task_history["subtasks"]:
                    task_history["subtasks"][subtask_id] = {"runs": 0, "passes": 0, "failures": 0, "last_result": None}
                
                subtask_history = task_history["subtasks"][subtask_id]
                subtask_history["runs"] += 1
                
                if result["success"]:
                    subtask_history["passes"] += 1
                else:
                    subtask_history["failures"] += 1
                
                subtask_history["last_result"] = {
                    "success": result["success"],
                    "success_count": result["success_count"],
                    "failure_count": result["failure_count"],
                    "error_count": result["error_count"],
                    "timestamp": result["timestamp"]
                }
        
        # 이력 저장
        self._save_test_history()
    
    def get_failure_count(self, task_id, subtask_id):
        """특정 태스크/서브태스크의 연속 실패 횟수를 반환합니다."""
        if task_id in self.test_history["tasks"]:
            task_history = self.test_history["tasks"][task_id]
            
            if subtask_id in task_history["subtasks"]:
                subtask_history = task_history["subtasks"][subtask_id]
                
                # 연속 실패 횟수 계산
                consecutive_failures = 0
                for i in range(subtask_history["runs"]):
                    if i >= subtask_history["passes"]:
                        consecutive_failures += 1
                    else:
                        break
                
                return consecutive_failures
        
        return 0
    
    def run_until_success(self, task_id, subtask_id, test_files=None, max_retries=None, callback=None):
        """테스트가 성공할 때까지 반복 실행합니다."""
        if max_retries is None:
            max_retries = self.config["max_retries"]
        
        for attempt in range(max_retries):
            logging.info(f"테스트 시도 {attempt+1}/{max_retries}")
            
            # 테스트 실행
            result = self.run_tests(task_id, subtask_id, test_files)
            
            # 성공 시 종료
            if result["success"]:
                logging.info(f"테스트 성공 (시도 {attempt+1}/{max_retries})")
                return result
            
            # 콜백 함수 호출 (코드 수정 등)
            if callback:
                callback_result = callback(result, attempt)
                if not callback_result:
                    logging.warning(f"콜백 함수 실패, 테스트 중단")
                    break
            
            # 재시도 전 대기
            if attempt < max_retries - 1:
                time.sleep(self.config["retry_delay"])
        
        logging.error(f"최대 재시도 횟수 초과 ({max_retries}회)")
        return result
```

### 2.3 코드 분석 모듈 (test_monitor/code_analyzer.py)

```python
import os
import re
import ast
import logging
import json
from pathlib import Path

class CodeAnalyzer:
    def __init__(self, config_path=None):
        """코드 분석 클래스 초기화"""
        # 기본 설정
        self.default_config = {
            "src_dir": "src",
            "test_dir": "tests",
            "ignore_dirs": ["venv", "__pycache__", ".git"],
            "ignore_files": ["__init__.py"],
            "mock_patterns": [
                r"# TODO:",
                r"# FIXME:",
                r"mock\.",
                r"@mock",
                r"unittest\.mock",
                r"pytest\.monkeypatch"
            ],
            "commented_code_patterns": [
                r"# [a-zA-Z_][a-zA-Z0-9_]*\s*\(",
                r"# def ",
                r"# class ",
                r"# if ",
                r"# for ",
                r"# while "
            ]
        }
        
        # 설정 파일 로드
        self.config = self.default_config.copy()
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    self.config.update(user_config)
                logging.info(f"설정 파일 로드 완료: {config_path}")
            except Exception as e:
                logging.error(f"설정 파일 로드 실패: {e}")
        
        logging.info("코드 분석기 초기화 완료")
    
    def find_files(self, directory, extensions=None):
        """지정된 디렉토리에서 파일을 찾습니다."""
        if extensions is None:
            extensions = ['.py']
        
        files = []
        for root, dirs, filenames in os.walk(directory):
            # 무시할 디렉토리 제외
            dirs[:] = [d for d in dirs if d not in self.config["ignore_dirs"]]
            
            for filename in filenames:
                # 확장자 확인
                if any(filename.endswith(ext) for ext in extensions):
                    # 무시할 파일 제외
                    if filename not in self.config["ignore_files"]:
                        files.append(os.path.join(root, filename))
        
        return files
    
    def detect_mocks(self, file_path):
        """파일에서 모의(mock) 처리를 감지합니다."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 모의 처리 패턴 검색
            mock_instances = []
            for pattern in self.config["mock_patterns"]:
                for match in re.finditer(pattern, content):
                    line_number = content[:match.start()].count('\n') + 1
                    line_content = content.splitlines()[line_number - 1]
                    mock_instances.append({
                        "line": line_number,
                        "content": line_content,
                        "pattern": pattern
                    })
            
            return mock_instances
        
        except Exception as e:
            logging.error(f"모의 처리 감지 중 오류 발생: {e}")
            return []
    
    def detect_commented_code(self, file_path):
        """파일에서 주석 처리된 코드를 감지합니다."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 주석 처리된 코드 패턴 검색
            commented_code = []
            for pattern in self.config["commented_code_patterns"]:
                for match in re.finditer(pattern, content):
                    line_number = content[:match.start()].count('\n') + 1
                    line_content = content.splitlines()[line_number - 1]
                    commented_code.append({
                        "line": line_number,
                        "content": line_content,
                        "pattern": pattern
                    })
            
            return commented_code
        
        except Exception as e:
            logging.error(f"주석 처리된 코드 감지 중 오류 발생: {e}")
            return []
    
    def analyze_project(self, directory=None):
        """프로젝트 전체를 분석합니다."""
        if directory is None:
            directory = self.config["src_dir"]
        
        # 파일 목록 가져오기
        files = self.find_files(directory)
        
        # 분석 결과
        analysis_result = {
            "total_files": len(files),
            "files_with_mocks": 0,
            "files_with_commented_code": 0,
            "total_mocks": 0,
            "total_commented_code": 0,
            "details": []
        }
        
        # 각 파일 분석
        for file_path in files:
            file_result = {
                "file": file_path,
                "mocks": self.detect_mocks(file_path),
                "commented_code": self.detect_commented_code(file_path)
            }
            
            # 통계 업데이트
            if file_result["mocks"]:
                analysis_result["files_with_mocks"] += 1
                analysis_result["total_mocks"] += len(file_result["mocks"])
            
            if file_result["commented_code"]:
                analysis_result["files_with_commented_code"] += 1
                analysis_result["total_commented_code"] += len(file_result["commented_code"])
            
            # 상세 정보 추가 (모의 처리 또는 주석 처리된 코드가 있는 경우에만)
            if file_result["mocks"] or file_result["commented_code"]:
                analysis_result["details"].append(file_result)
        
        logging.info(f"프로젝트 분석 완료: {analysis_result['total_files']} 파일, {analysis_result['total_mocks']} 모의 처리, {analysis_result['total_commented_code']} 주석 처리된 코드")
        return analysis_result
    
    def get_analysis_summary(self, analysis_result):
        """분석 결과 요약을 반환합니다."""
        summary = []
        
        # 모의 처리 요약
        if analysis_result["total_mocks"] > 0:
            summary.append(f"모의(mock) 처리 발견: {analysis_result['total_mocks']} 개 ({analysis_result['files_with_mocks']} 파일)")
            
            # 상위 5개 파일 목록
            top_files = sorted(
                [f for f in analysis_result["details"] if f["mocks"]],
                key=lambda x: len(x["mocks"]),
                reverse=True
            )[:5]
            
            for file_result in top_files:
                summary.append(f"  - {file_result['file']}: {len(file_result['mocks'])} 개")
        
        # 주석 처리된 코드 요약
        if analysis_result["total_commented_code"] > 0:
            summary.append(f"주석 처리된 코드 발견: {analysis_result['total_commented_code']} 개 ({analysis_result['files_with_commented_code']} 파일)")
            
            # 상위 5개 파일 목록
            top_files = sorted(
                [f for f in analysis_result["details"] if f["commented_code"]],
                key=lambda x: len(x["commented_code"]),
                reverse=True
            )[:5]
            
            for file_result in top_files:
                summary.append(f"  - {file_result['file']}: {len(file_result['commented_code'])} 개")
        
        return "\n".join(summary) if summary else "임시 처리 없음"
```

### 2.4 태스크 관리 모듈 (task_manager/task_orchestrator.py)

```python
import os
import json
import logging
import time
import re
from pathlib import Path

class TaskOrchestrator:
    def __init__(self, config_path=None):
        """태스크 오케스트레이터 클래스 초기화"""
        # 기본 설정
        self.default_config = {
            "task_file": "tasks.json",
            "task_status_file": "task_status.json",
            "max_subtask_failures": 5,
            "task_timeout": 3600,  # 1시간
            "subtask_timeout": 600  # 10분
        }
        
        # 설정 파일 로드
        self.config = self.default_config.copy()
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    self.config.update(user_config)
                logging.info(f"설정 파일 로드 완료: {config_path}")
            except Exception as e:
                logging.error(f"설정 파일 로드 실패: {e}")
        
        # 태스크 파일 경로
        self.task_file = self.config["task_file"]
        self.task_status_file = self.config["task_status_file"]
        
        # 태스크 및 상태 로드
        self.tasks = self._load_tasks()
        self.task_status = self._load_task_status()
        
        logging.info("태스크 오케스트레이터 초기화 완료")
    
    def _load_tasks(self):
        """태스크 정의를 로드합니다."""
        if os.path.exists(self.task_file):
            try:
                with open(self.task_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"태스크 정의 로드 실패: {e}")
        
        # 기본 태스크 구조
        return {"tasks": []}
    
    def _load_task_status(self):
        """태스크 상태를 로드합니다."""
        if os.path.exists(self.task_status_file):
            try:
                with open(self.task_status_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"태스크 상태 로드 실패: {e}")
        
        # 기본 상태 구조
        return {
            "current_task_index": 0,
            "current_subtask_index": 0,
            "task_statuses": []
        }
    
    def _save_task_status(self):
        """태스크 상태를 저장합니다."""
        try:
            with open(self.task_status_file, 'w') as f:
                json.dump(self.task_status, f, indent=2)
            logging.info(f"태스크 상태 저장 완료: {self.task_status_file}")
            return True
        except Exception as e:
            logging.error(f"태스크 상태 저장 실패: {e}")
            return False
    
    def get_current_task(self):
        """현재 실행 중인 태스크를 반환합니다."""
        if not self.tasks["tasks"]:
            return None
        
        task_index = self.task_status["current_task_index"]
        if task_index >= len(self.tasks["tasks"]):
            return None
        
        return self.tasks["tasks"][task_index]
    
    def get_current_subtask(self):
        """현재 실행 중인 서브태스크를 반환합니다."""
        task = self.get_current_task()
        if not task or "subtasks" not in task:
            return None
        
        subtask_index = self.task_status["current_subtask_index"]
        if subtask_index >= len(task["subtasks"]):
            return None
        
        return task["subtasks"][subtask_index]
    
    def update_task_status(self, task_id, status, message=None):
        """태스크 상태를 업데이트합니다."""
        # 태스크 상태 목록 확인
        if "task_statuses" not in self.task_status:
            self.task_status["task_statuses"] = []
        
        # 태스크 상태 찾기
        task_status = None
        for ts in self.task_status["task_statuses"]:
            if ts["task_id"] == task_id:
                task_status = ts
                break
        
        # 태스크 상태가 없으면 새로 생성
        if not task_status:
            task_status = {
                "task_id": task_id,
                "status": status,
                "message": message,
                "subtasks": [],
                "start_time": time.time(),
                "update_time": time.time()
            }
            self.task_status["task_statuses"].append(task_status)
        else:
            # 기존 태스크 상태 업데이트
            task_status["status"] = status
            task_status["message"] = message
            task_status["update_time"] = time.time()
        
        # 상태 저장
        self._save_task_status()
        
        logging.info(f"태스크 상태 업데이트: {task_id} -> {status}")
        return True
    
    def update_subtask_status(self, task_id, subtask_id, status, message=None):
        """서브태스크 상태를 업데이트합니다."""
        # 태스크 상태 찾기
        task_status = None
        for ts in self.task_status["task_statuses"]:
            if ts["task_id"] == task_id:
                task_status = ts
                break
        
        # 태스크 상태가 없으면 새로 생성
        if not task_status:
            task_status = {
                "task_id": task_id,
                "status": "in_progress",
                "message": None,
                "subtasks": [],
                "start_time": time.time(),
                "update_time": time.time()
            }
            self.task_status["task_statuses"].append(task_status)
        
        # 서브태스크 상태 찾기
        subtask_status = None
        for sts in task_status["subtasks"]:
            if sts["subtask_id"] == subtask_id:
                subtask_status = sts
                break
        
        # 서브태스크 상태가 없으면 새로 생성
        if not subtask_status:
            subtask_status = {
                "subtask_id": subtask_id,
                "status": status,
                "message": message,
                "failure_count": 0,
                "start_time": time.time(),
                "update_time": time.time()
            }
            task_status["subtasks"].append(subtask_status)
        else:
            # 기존 서브태스크 상태 업데이트
            subtask_status["status"] = status
            subtask_status["message"] = message
            subtask_status["update_time"] = time.time()
            
            # 실패 시 카운트 증가
            if status == "failed":
                subtask_status["failure_count"] = subtask_status.get("failure_count", 0) + 1
        
        # 상태 저장
        self._save_task_status()
        
        logging.info(f"서브태스크 상태 업데이트: {task_id}/{subtask_id} -> {status}")
        return True
    
    def get_subtask_failure_count(self, task_id, subtask_id):
        """서브태스크의 실패 횟수를 반환합니다."""
        # 태스크 상태 찾기
        for ts in self.task_status["task_statuses"]:
            if ts["task_id"] == task_id:
                # 서브태스크 상태 찾기
                for sts in ts["subtasks"]:
                    if sts["subtask_id"] == subtask_id:
                        return sts.get("failure_count", 0)
        
        return 0
    
    def move_to_next_subtask(self):
        """다음 서브태스크로 이동합니다."""
        task = self.get_current_task()
        if not task or "subtasks" not in task:
            return False
        
        # 현재 서브태스크 인덱스 증가
        self.task_status["current_subtask_index"] += 1
        
        # 모든 서브태스크가 완료되었는지 확인
        if self.task_status["current_subtask_index"] >= len(task["subtasks"]):
            # 현재 태스크 완료 처리
            self.update_task_status(task["id"], "completed", "모든 서브태스크 완료")
            
            # 다음 태스크로 이동
            self.task_status["current_task_index"] += 1
            self.task_status["current_subtask_index"] = 0
            
            # 모든 태스크가 완료되었는지 확인
            if self.task_status["current_task_index"] >= len(self.tasks["tasks"]):
                logging.info("모든 태스크 완료")
            else:
                next_task = self.tasks["tasks"][self.task_status["current_task_index"]]
                logging.info(f"다음 태스크로 이동: {next_task['id']}")
        else:
            next_subtask = task["subtasks"][self.task_status["current_subtask_index"]]
            logging.info(f"다음 서브태스크로 이동: {next_subtask['id']}")
        
        # 상태 저장
        self._save_task_status()
        
        return True
    
    def is_subtask_failed_too_many_times(self, task_id, subtask_id):
        """서브태스크가 너무 많이 실패했는지 확인합니다."""
        failure_count = self.get_subtask_failure_count(task_id, subtask_id)
        return failure_count >= self.config["max_subtask_failures"]
    
    def parse_task_file(self, file_path):
        """태스크 정의 파일을 파싱합니다."""
        try:
            # 파일 확장자 확인
            if file_path.endswith('.json'):
                # JSON 파일 파싱
                with open(file_path, 'r') as f:
                    tasks = json.load(f)
            elif file_path.endswith('.md'):
                # Markdown 파일 파싱
                tasks = self._parse_markdown_tasks(file_path)
            else:
                logging.error(f"지원되지 않는 파일 형식: {file_path}")
                return None
            
            # 태스크 저장
            self.tasks = tasks
            
            # 태스크 상태 초기화
            self.task_status = {
                "current_task_index": 0,
                "current_subtask_index": 0,
                "task_statuses": []
            }
            
            # 상태 저장
            self._save_task_status()
            
            logging.info(f"태스크 정의 파싱 완료: {len(tasks['tasks'])} 태스크")
            return tasks
        
        except Exception as e:
            logging.error(f"태스크 정의 파싱 실패: {e}")
            return None
    
    def _parse_markdown_tasks(self, file_path):
        """Markdown 형식의 태스크 정의 파일을 파싱합니다."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 태스크 및 서브태스크 추출
            tasks = {"tasks": []}
            
            # 태스크 패턴: ### Task N: [태스크명]
            task_pattern = r'###\s+Task\s+(\d+):\s+(.*)'
            
            # 서브태스크 패턴: #### Subtask N.M: [서브태스크명]
            subtask_pattern = r'####\s+Subtask\s+(\d+)\.(\d+):\s+(.*)'
            
            # 현재 태스크
            current_task = None
            
            # 각 줄 처리
            for line in content.splitlines():
                # 태스크 매칭
                task_match = re.match(task_pattern, line)
                if task_match:
                    task_num = task_match.group(1)
                    task_name = task_match.group(2)
                    
                    current_task = {
                        "id": f"task_{task_num}",
                        "name": task_name,
                        "description": "",
                        "subtasks": []
                    }
                    
                    tasks["tasks"].append(current_task)
                    continue
                
                # 서브태스크 매칭
                subtask_match = re.match(subtask_pattern, line)
                if subtask_match and current_task:
                    task_num = subtask_match.group(1)
                    subtask_num = subtask_match.group(2)
                    subtask_name = subtask_match.group(3)
                    
                    subtask = {
                        "id": f"subtask_{task_num}_{subtask_num}",
                        "name": subtask_name,
                        "description": ""
                    }
                    
                    current_task["subtasks"].append(subtask)
                    continue
                
                # 설명 추가 (들여쓰기된 줄)
                if line.startswith('  ') and current_task:
                    # 마지막 서브태스크가 있으면 서브태스크 설명에 추가
                    if current_task["subtasks"]:
                        current_task["subtasks"][-1]["description"] += line.strip() + "\n"
                    # 없으면 태스크 설명에 추가
                    else:
                        current_task["description"] += line.strip() + "\n"
            
            return tasks
        
        except Exception as e:
            logging.error(f"Markdown 태스크 파싱 실패: {e}")
            return {"tasks": []}
```

### 2.5 알림 모듈 (notification/notification_manager.py)

```python
import os
import json
import logging
import requests
import time

class NotificationManager:
    def __init__(self, config_path=None):
        """알림 관리자 클래스 초기화"""
        # 기본 설정
        self.default_config = {
            "enabled": True,
            "slack": {
                "enabled": False,
                "webhook_url": "",
                "channel": "",
                "username": "Automation Bot"
            },
            "telegram": {
                "enabled": False,
                "bot_token": "",
                "chat_id": ""
            },
            "notification_cooldown": 300,  # 5분
            "last_notification_time": {}
        }
        
        # 설정 파일 로드
        self.config = self.default_config.copy()
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    self.config.update(user_config)
                logging.info(f"설정 파일 로드 완료: {config_path}")
            except Exception as e:
                logging.error(f"설정 파일 로드 실패: {e}")
        
        logging.info("알림 관리자 초기화 완료")
    
    def send_slack_notification(self, message, attachments=None):
        """Slack으로 알림을 전송합니다."""
        if not self.config["enabled"] or not self.config["slack"]["enabled"]:
            logging.info("Slack 알림 비활성화됨")
            return False
        
        if not self.config["slack"]["webhook_url"]:
            logging.error("Slack webhook URL이 설정되지 않음")
            return False
        
        # 쿨다운 확인
        notification_key = f"slack_{hash(message)}"
        last_time = self.config["last_notification_time"].get(notification_key, 0)
        current_time = time.time()
        
        if current_time - last_time < self.config["notification_cooldown"]:
            logging.info(f"Slack 알림 쿨다운 중 (남은 시간: {int(self.config['notification_cooldown'] - (current_time - last_time))}초)")
            return False
        
        try:
            # 알림 데이터 구성
            payload = {
                "text": message,
                "username": self.config["slack"]["username"]
            }
            
            if self.config["slack"]["channel"]:
                payload["channel"] = self.config["slack"]["channel"]
            
            if attachments:
                payload["attachments"] = attachments
            
            # 알림 전송
            response = requests.post(
                self.config["slack"]["webhook_url"],
                json=payload
            )
            
            if response.status_code == 200:
                logging.info("Slack 알림 전송 성공")
                
                # 마지막 알림 시간 업데이트
                self.config["last_notification_time"][notification_key] = current_time
                
                return True
            else:
                logging.error(f"Slack 알림 전송 실패: {response.status_code} {response.text}")
                return False
        
        except Exception as e:
            logging.error(f"Slack 알림 전송 중 오류 발생: {e}")
            return False
    
    def send_telegram_notification(self, message):
        """Telegram으로 알림을 전송합니다."""
        if not self.config["enabled"] or not self.config["telegram"]["enabled"]:
            logging.info("Telegram 알림 비활성화됨")
            return False
        
        if not self.config["telegram"]["bot_token"] or not self.config["telegram"]["chat_id"]:
            logging.error("Telegram 봇 토큰 또는 채팅 ID가 설정되지 않음")
            return False
        
        # 쿨다운 확인
        notification_key = f"telegram_{hash(message)}"
        last_time = self.config["last_notification_time"].get(notification_key, 0)
        current_time = time.time()
        
        if current_time - last_time < self.config["notification_cooldown"]:
            logging.info(f"Telegram 알림 쿨다운 중 (남은 시간: {int(self.config['notification_cooldown'] - (current_time - last_time))}초)")
            return False
        
        try:
            # 알림 전송
            url = f"https://api.telegram.org/bot{self.config['telegram']['bot_token']}/sendMessage"
            payload = {
                "chat_id": self.config["telegram"]["chat_id"],
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                logging.info("Telegram 알림 전송 성공")
                
                # 마지막 알림 시간 업데이트
                self.config["last_notification_time"][notification_key] = current_time
                
                return True
            else:
                logging.error(f"Telegram 알림 전송 실패: {response.status_code} {response.text}")
                return False
        
        except Exception as e:
            logging.error(f"Telegram 알림 전송 중 오류 발생: {e}")
            return False
    
    def send_notification(self, message, title=None, severity="info", attachments=None):
        """모든 활성화된 채널로 알림을 전송합니다."""
        if not self.config["enabled"]:
            logging.info("알림 시스템 비활성화됨")
            return False
        
        # 제목 추가
        if title:
            formatted_message = f"*{title}*\n{message}"
        else:
            formatted_message = message
        
        # 심각도에 따른 아이콘 추가
        if severity == "error":
            icon = "🚨"
        elif severity == "warning":
            icon = "⚠️"
        else:
            icon = "ℹ️"
        
        formatted_message = f"{icon} {formatted_message}"
        
        # 각 채널로 알림 전송
        results = []
        
        # Slack 알림
        if self.config["slack"]["enabled"]:
            slack_result = self.send_slack_notification(formatted_message, attachments)
            results.append(slack_result)
        
        # Telegram 알림
        if self.config["telegram"]["enabled"]:
            telegram_result = self.send_telegram_notification(formatted_message)
            results.append(telegram_result)
        
        # 하나 이상의 채널에서 성공했으면 성공으로 간주
        return any(results) if results else False
    
    def notify_subtask_failure(self, task_id, task_name, subtask_id, subtask_name, failure_count, error_message=None):
        """서브태스크 실패 알림을 전송합니다."""
        title = f"서브태스크 실패 알림 ({failure_count}회)"
        message = f"태스크: {task_name} ({task_id})\n"
        message += f"서브태스크: {subtask_name} ({subtask_id})\n"
        message += f"실패 횟수: {failure_count}\n"
        
        if error_message:
            message += f"오류 메시지: ```{error_message}```"
        
        return self.send_notification(message, title, "error")
    
    def notify_test_failure(self, task_id, subtask_id, test_result):
        """테스트 실패 알림을 전송합니다."""
        title = "테스트 실패 알림"
        message = f"태스크: {task_id}\n"
        message += f"서브태스크: {subtask_id}\n"
        message += f"실패한 테스트: {test_result['failure_count']}\n"
        message += f"오류 테스트: {test_result['error_count']}\n"
        
        # 실패한 테스트 목록 추출 (최대 5개)
        failure_pattern = r"FAILED\s+([\w\.]+)::\w+\s+"
        failures = re.findall(failure_pattern, test_result["output"])
        
        if failures:
            message += "\n실패한 테스트 목록:\n"
            for i, failure in enumerate(failures[:5]):
                message += f"{i+1}. {failure}\n"
            
            if len(failures) > 5:
                message += f"외 {len(failures) - 5}개 더..."
        
        return self.send_notification(message, title, "error")
    
    def notify_mock_detection(self, analysis_result):
        """모의 처리 감지 알림을 전송합니다."""
        if analysis_result["total_mocks"] == 0 and analysis_result["total_commented_code"] == 0:
            return False
        
        title = "코드 품질 경고"
        message = ""
        
        if analysis_result["total_mocks"] > 0:
            message += f"모의(mock) 처리 발견: {analysis_result['total_mocks']} 개 ({analysis_result['files_with_mocks']} 파일)\n\n"
            
            # 상위 3개 파일 목록
            top_files = sorted(
                [f for f in analysis_result["details"] if f["mocks"]],
                key=lambda x: len(x["mocks"]),
                reverse=True
            )[:3]
            
            for file_result in top_files:
                message += f"- {file_result['file']}: {len(file_result['mocks'])} 개\n"
        
        if analysis_result["total_commented_code"] > 0:
            if message:
                message += "\n"
            
            message += f"주석 처리된 코드 발견: {analysis_result['total_commented_code']} 개 ({analysis_result['files_with_commented_code']} 파일)\n\n"
            
            # 상위 3개 파일 목록
            top_files = sorted(
                [f for f in analysis_result["details"] if f["commented_code"]],
                key=lambda x: len(x["commented_code"]),
                reverse=True
            )[:3]
            
            for file_result in top_files:
                message += f"- {file_result['file']}: {len(file_result['commented_code'])} 개\n"
        
        return self.send_notification(message, title, "warning")
    
    def notify_task_completion(self, task_id, task_name):
        """태스크 완료 알림을 전송합니다."""
        title = "태스크 완료 알림"
        message = f"태스크 '{task_name}' ({task_id})가 성공적으로 완료되었습니다."
        
        return self.send_notification(message, title, "info")
```

### 2.6 메인 모듈 (main.py)

```python
import os
import sys
import logging
import argparse
import json
import time
from pathlib import Path

# 모듈 임포트
from gui_automation.claude_desktop import ClaudeDesktopAutomation
from test_monitor.test_runner import TestRunner
from test_monitor.code_analyzer import CodeAnalyzer
from task_manager.task_orchestrator import TaskOrchestrator
from notification.notification_manager import NotificationManager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("automation")

class AutomationSystem:
    def __init__(self, config_path=None):
        """자동화 시스템 클래스 초기화"""
        # 기본 설정
        self.default_config = {
            "gui_config": "config/gui_config.json",
            "test_config": "config/test_config.json",
            "task_config": "config/task_config.json",
            "notification_config": "config/notification_config.json",
            "code_analyzer_config": "config/code_analyzer_config.json",
            "task_file": "tasks.json",
            "max_retries": 5,
            "retry_delay": 2,
            "check_mocks": True
        }
        
        # 설정 파일 로드
        self.config = self.default_config.copy()
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    self.config.update(user_config)
                logger.info(f"설정 파일 로드 완료: {config_path}")
            except Exception as e:
                logger.error(f"설정 파일 로드 실패: {e}")
        
        # 구성 요소 초기화
        self.claude = ClaudeDesktopAutomation(self.config["gui_config"])
        self.test_runner = TestRunner(self.config["test_config"])
        self.task_orchestrator = TaskOrchestrator(self.config["task_config"])
        self.notification = NotificationManager(self.config["notification_config"])
        self.code_analyzer = CodeAnalyzer(self.config["code_analyzer_config"])
        
        logger.info("자동화 시스템 초기화 완료")
    
    def setup(self):
        """초기 설정을 수행합니다."""
        # Claude Desktop 버튼 이미지 설정
        logger.info("Claude Desktop 버튼 이미지 설정 시작")
        self.claude.setup_buttons()
        
        # 태스크 파일 로드
        if os.path.exists(self.config["task_file"]):
            logger.info(f"태스크 파일 로드: {self.config['task_file']}")
            self.task_orchestrator.parse_task_file(self.config["task_file"])
        else:
            logger.warning(f"태스크 파일을 찾을 수 없음: {self.config['task_file']}")
        
        logger.info("초기 설정 완료")
        return True
    
    def process_subtask(self, task, subtask):
        """서브태스크를 처리합니다."""
        task_id = task["id"]
        task_name = task["name"]
        subtask_id = subtask["id"]
        subtask_name = subtask["name"]
        
        logger.info(f"서브태스크 처리 시작: {task_name} / {subtask_name}")
        
        # 서브태스크 상태 업데이트
        self.task_orchestrator.update_subtask_status(task_id, subtask_id, "in_progress")
        
        # 서브태스크 설명을 Claude에 전송
        prompt = f"Task: {task_name}\nSubtask: {subtask_name}\n\n{subtask['description']}"
        
        # Claude Desktop 자동화 실행
        logger.info("Claude Desktop에 프롬프트 전송")
        self.claude.run_automation(prompt, wait_for_continue=True, create_new_chat=True)
        
        # 테스트 실행
        logger.info("테스트 실행")
        test_result = self.test_runner.run_tests(task_id, subtask_id)
        
        # 테스트 성공 여부 확인
        if test_result["success"]:
            logger.info("테스트 성공")
            
            # 코드 품질 검사 (모의 처리 감지)
            if self.config["check_mocks"]:
                logger.info("코드 품질 검사 (모의 처리 감지)")
                analysis_result = self.code_analyzer.analyze_project()
                
                if analysis_result["total_mocks"] > 0 or analysis_result["total_commented_code"] > 0:
                    logger.warning("모의 처리 또는 주석 처리된 코드 발견")
                    
                    # 알림 전송
                    self.notification.notify_mock_detection(analysis_result)
                    
                    # 모의 처리 요약을 Claude에 전송
                    summary = self.code_analyzer.get_analysis_summary(analysis_result)
                    prompt = f"다음 코드 품질 문제를 해결해주세요:\n\n{summary}"
                    
                    # Claude Desktop 자동화 실행
                    logger.info("Claude Desktop에 코드 품질 문제 전송")
                    self.claude.run_automation(prompt, wait_for_continue=True)
                    
                    # 다시 테스트 실행
                    logger.info("테스트 다시 실행")
                    test_result = self.test_runner.run_tests(task_id, subtask_id)
                    
                    if not test_result["success"]:
                        logger.error("코드 품질 문제 해결 후 테스트 실패")
                        
                        # 서브태스크 실패 처리
                        failure_count = self.task_orchestrator.get_subtask_failure_count(task_id, subtask_id) + 1
                        self.task_orchestrator.update_subtask_status(task_id, subtask_id, "failed", "코드 품질 문제 해결 후 테스트 실패")
                        
                        # 실패 횟수가 너무 많으면 알림 전송
                        if self.task_orchestrator.is_subtask_failed_too_many_times(task_id, subtask_id):
                            logger.warning(f"서브태스크 실패 횟수 초과: {failure_count}회")
                            self.notification.notify_subtask_failure(
                                task_id, task_name, subtask_id, subtask_name,
                                failure_count, test_result["output"]
                            )
                        
                        return False
            
            # 서브태스크 완료 처리
            self.task_orchestrator.update_subtask_status(task_id, subtask_id, "completed")
            logger.info(f"서브태스크 완료: {task_name} / {subtask_name}")
            return True
        
        else:
            logger.error("테스트 실패")
            
            # 테스트 실패 정보를 Claude에 전송
            prompt = f"테스트가 실패했습니다. 다음 오류를 수정해주세요:\n\n{test_result['output']}"
            
            # 최대 재시도 횟수만큼 반복
            for attempt in range(self.config["max_retries"]):
                logger.info(f"테스트 수정 시도 {attempt+1}/{self.config['max_retries']}")
                
                # Claude Desktop 자동화 실행
                self.claude.run_automation(prompt, wait_for_continue=True)
                
                # 다시 테스트 실행
                test_result = self.test_runner.run_tests(task_id, subtask_id)
                
                # 테스트 성공 시 종료
                if test_result["success"]:
                    logger.info(f"테스트 수정 성공 (시도 {attempt+1}/{self.config['max_retries']})")
                    
                    # 서브태스크 완료 처리
                    self.task_orchestrator.update_subtask_status(task_id, subtask_id, "completed")
                    logger.info(f"서브태스크 완료: {task_name} / {subtask_name}")
                    return True
                
                # 실패 시 다음 시도 준비
                prompt = f"테스트가 여전히 실패했습니다. 다음 오류를 수정해주세요:\n\n{test_result['output']}"
                
                # 재시도 전 대기
                if attempt < self.config["max_retries"] - 1:
                    time.sleep(self.config["retry_delay"])
            
            # 최대 재시도 횟수 초과
            logger.error(f"최대 재시도 횟수 초과 ({self.config['max_retries']}회)")
            
            # 서브태스크 실패 처리
            failure_count = self.task_orchestrator.get_subtask_failure_count(task_id, subtask_id) + 1
            self.task_orchestrator.update_subtask_status(task_id, subtask_id, "failed", "최대 재시도 횟수 초과")
            
            # 실패 횟수가 너무 많으면 알림 전송
            if self.task_orchestrator.is_subtask_failed_too_many_times(task_id, subtask_id):
                logger.warning(f"서브태스크 실패 횟수 초과: {failure_count}회")
                self.notification.notify_subtask_failure(
                    task_id, task_name, subtask_id, subtask_name,
                    failure_count, test_result["output"]
                )
            
            return False
    
    def run(self):
        """자동화 시스템을 실행합니다."""
        logger.info("자동화 시스템 실행 시작")
        
        while True:
            # 현재 태스크 및 서브태스크 가져오기
            task = self.task_orchestrator.get_current_task()
            if not task:
                logger.info("더 이상 처리할 태스크가 없습니다.")
                break
            
            subtask = self.task_orchestrator.get_current_subtask()
            if not subtask:
                logger.info(f"태스크 '{task['name']}'에 더 이상 처리할 서브태스크가 없습니다.")
                
                # 다음 태스크로 이동
                self.task_orchestrator.move_to_next_subtask()
                continue
            
            # 서브태스크 처리
            result = self.process_subtask(task, subtask)
            
            # 서브태스크 처리 결과에 따라 다음 단계 결정
            if result:
                # 성공 시 다음 서브태스크로 이동
                self.task_orchestrator.move_to_next_subtask()
                
                # 태스크의 모든 서브태스크가 완료되었는지 확인
                if self.task_orchestrator.get_current_task() != task:
                    # 태스크 완료 알림
                    self.notification.notify_task_completion(task["id"], task["name"])
            else:
                # 실패 시 현재 서브태스크 유지 (다음 실행에서 다시 시도)
                logger.warning(f"서브태스크 '{subtask['name']}' 처리 실패, 다음 실행에서 다시 시도합니다.")
                
                # 실패 횟수가 너무 많으면 다음 서브태스크로 강제 이동
                if self.task_orchestrator.is_subtask_failed_too_many_times(task["id"], subtask["id"]):
                    logger.error(f"서브태스크 '{subtask['name']}' 실패 횟수 초과, 다음 서브태스크로 강제 이동합니다.")
                    self.task_orchestrator.move_to_next_subtask()
                
                # 일정 시간 대기 후 다시 시도
                time.sleep(self.config["retry_delay"])
        
        logger.info("자동화 시스템 실행 완료")
        return True


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='통합 자동화 시스템')
    parser.add_argument('--config', type=str, help='설정 파일 경로')
    parser.add_argument('--setup', action='store_true', help='초기 설정 모드')
    parser.add_argument('--task-file', type=str, help='태스크 정의 파일 경로')
    
    args = parser.parse_args()
    
    # 자동화 시스템 생성
    system = AutomationSystem(args.config)
    
    # 태스크 파일 설정
    if args.task_file:
        system.config["task_file"] = args.task_file
    
    # 초기 설정 모드
    if args.setup:
        system.setup()
        return
    
    # 자동화 시스템 실행
    system.run()


if __name__ == "__main__":
    main()
```

## 3. 설정 파일 예시

### 3.1 시스템 설정 (config/system_config.json)

```json
{
  "gui_config": "config/gui_config.json",
  "test_config": "config/test_config.json",
  "task_config": "config/task_config.json",
  "notification_config": "config/notification_config.json",
  "code_analyzer_config": "config/code_analyzer_config.json",
  "task_file": "tasks.json",
  "max_retries": 5,
  "retry_delay": 2,
  "check_mocks": true
}
```

### 3.2 GUI 설정 (config/gui_config.json)

```json
{
  "window_title": "Claude",
  "input_delay": 0.5,
  "screenshot_delay": 1.0,
  "max_retries": 3,
  "confidence_threshold": 0.7,
  "continue_button_text": "Continue",
  "new_chat_button_text": "New chat",
  "assets_dir": "assets",
  "continue_button_image": "continue_button.png",
  "new_chat_button_image": "new_chat_button.png"
}
```

### 3.3 테스트 설정 (config/test_config.json)

```json
{
  "test_command": "pytest",
  "test_args": ["-v"],
  "max_retries": 5,
  "retry_delay": 2,
  "test_dir": "tests",
  "test_history_file": "test_history.json",
  "success_pattern": "(\\d+) passed",
  "failure_pattern": "(\\d+) failed",
  "error_pattern": "(\\d+) error"
}
```

### 3.4 알림 설정 (config/notification_config.json)

```json
{
  "enabled": true,
  "slack": {
    "enabled": true,
    "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    "channel": "#automation",
    "username": "Automation Bot"
  },
  "telegram": {
    "enabled": true,
    "bot_token": "YOUR_BOT_TOKEN",
    "chat_id": "YOUR_CHAT_ID"
  },
  "notification_cooldown": 300
}
```

## 4. 사용 방법

### 4.1 초기 설정

1. 필요한 패키지 설치:
   ```bash
   pip install pyautogui opencv-python numpy pillow requests pytest
   ```

2. 설정 파일 준비:
   - `config/` 디렉토리에 필요한 설정 파일 생성
   - 알림을 위한 Slack 웹훅 URL 또는 Telegram 봇 토큰 설정

3. 버튼 이미지 설정:
   ```bash
   python main.py --setup
   ```
   - 화면에 표시되는 안내에 따라 '계속하기' 버튼과 '새 채팅' 버튼 위치 지정

### 4.2 태스크 정의 파일 작성

JSON 형식:
```json
{
  "tasks": [
    {
      "id": "task_1",
      "name": "사용자 인증 기능 구현",
      "description": "사용자 로그인, 회원가입, 비밀번호 재설정 기능 구현",
      "subtasks": [
        {
          "id": "subtask_1_1",
          "name": "사용자 모델 구현",
          "description": "사용자 정보를 저장할 모델 클래스 구현"
        },
        {
          "id": "subtask_1_2",
          "name": "회원가입 API 구현",
          "description": "새 사용자 등록을 위한 API 엔드포인트 구현"
        }
      ]
    }
  ]
}
```

Markdown 형식:
```markdown
# 프로젝트 태스크 정의

## 프로젝트 개요
- 프로젝트명: 사용자 인증 시스템
- 기술 스택: Python, Flask, SQLAlchemy

## 태스크 정의

### Task 1: 사용자 인증 기능 구현
  사용자 로그인, 회원가입, 비밀번호 재설정 기능 구현

#### Subtask 1.1: 사용자 모델 구현
  사용자 정보를 저장할 모델 클래스 구현
  
#### Subtask 1.2: 회원가입 API 구현
  새 사용자 등록을 위한 API 엔드포인트 구현
```

### 4.3 자동화 시스템 실행

```bash
python main.py --task-file tasks.md
```

## 5. 작동 원리

1. **태스크 정의 파싱**:
   - JSON 또는 Markdown 형식의 태스크 정의 파일 파싱
   - 태스크 및 서브태스크 구조화

2. **서브태스크 처리 흐름**:
   - 현재 서브태스크 정보를 Claude Desktop에 전송
   - Claude가 코드 생성 또는 수정
   - 테스트 실행 및 결과 확인
   - 테스트 실패 시 오류 정보를 Claude에 전송하고 재시도
   - 코드 품질 검사 (모의 처리, 주석 처리된 코드 감지)
   - 서브태스크 완료 시 다음 서브태스크로 이동

3. **알림 시스템**:
   - 서브태스크 실패 횟수가 임계값 초과 시 알림 전송
   - 코드 품질 문제 발견 시 알림 전송
   - 태스크 완료 시 알림 전송

4. **예외 처리**:
   - 최대 재시도 횟수 초과 시 다음 서브태스크로 강제 이동
   - GUI 자동화 실패 시 로그 기록 및 재시도
   - 알림 전송 실패 시 대체 채널 시도

## 6. 확장 및 커스터마이징

- **테스트 프레임워크 변경**: `test_config.json`에서 테스트 명령 및 인자 수정
- **추가 알림 채널**: `notification_manager.py`에 새 알림 채널 추가
- **코드 품질 검사 규칙**: `code_analyzer_config.json`에서 패턴 추가/수정
- **GUI 자동화 확장**: `claude_desktop.py`에 추가 기능 구현
