import os
import sys
import logging
import argparse
import json
import time
from pathlib import Path

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
            # 실제 구현에서는 pyautogui.getWindowsWithTitle 사용
            # 여기서는 예시로 True 반환
            self.window_active = True
            logging.info("Claude Desktop 창 활성화 성공")
            return True
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
        
        # 실제 구현에서는 pyautogui.locateCenterOnScreen 및 pyautogui.click 사용
        # 여기서는 예시로 True 반환
        logging.info(f"이미지 클릭 성공: {image_path}")
        return True
    
    def capture_and_save_button(self, button_name, region=None):
        """화면의 특정 영역을 캡처하여 버튼 이미지로 저장합니다."""
        try:
            # 실제 구현에서는 pyautogui.screenshot 사용
            # 여기서는 예시로 True 반환
            
            # 이미지 저장 경로 설정
            if button_name == "continue":
                image_path = self.continue_button_image
            elif button_name == "new_chat":
                image_path = self.new_chat_button_image
            else:
                image_path = os.path.join(self.assets_dir, f"{button_name}_button.png")
            
            # 더미 이미지 파일 생성
            with open(image_path, 'w') as f:
                f.write("dummy image")
            
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
            
            # 실제 구현에서는 pyautogui.hotkey 및 pyautogui.write 사용
            # 여기서는 예시로 True 반환
            logging.info(f"텍스트 입력 완료: {text[:50]}..." if len(text) > 50 else f"텍스트 입력 완료: {text}")
            return True
        
        except Exception as e:
            logging.error(f"텍스트 입력 중 오류 발생: {e}")
            return False
    
    def press_enter(self):
        """Enter 키를 누릅니다."""
        try:
            # 실제 구현에서는 pyautogui.press 사용
            # 여기서는 예시로 True 반환
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
            # 실제 구현에서는 subprocess.Popen 사용
            # 여기서는 예시로 더미 결과 반환
            
            # 더미 테스트 결과
            result = {
                "success": True,  # 테스트 성공 여부
                "return_code": 0,
                "success_count": 10,
                "failure_count": 0,
                "error_count": 0,
                "output": "10 passed, 0 failed, 0 error",
                "timestamp": time.time()
            }
            
            # 테스트 이력 업데이트
            self._update_test_history(task_id, subtask_id, result)
            
            logging.info(f"테스트 결과: 성공={result['success_count']}, 실패={result['failure_count']}, 에러={result['error_count']}")
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


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='Claude Desktop 자동화 및 테스트 실행')
    parser.add_argument('--setup', action='store_true', help='초기 설정 모드')
    parser.add_argument('--prompt', type=str, help='Claude에 전송할 프롬프트')
    parser.add_argument('--test', action='store_true', help='테스트 실행')
    parser.add_argument('--task-id', type=str, help='태스크 ID')
    parser.add_argument('--subtask-id', type=str, help='서브태스크 ID')
    
    args = parser.parse_args()
    
    # Claude Desktop 자동화 객체 생성
    claude = ClaudeDesktopAutomation()
    
    # 초기 설정 모드
    if args.setup:
        claude.setup_buttons()
        return
    
    # 프롬프트 전송
    if args.prompt:
        claude.run_automation(args.prompt)
    
    # 테스트 실행
    if args.test:
        test_runner = TestRunner()
        result = test_runner.run_tests(args.task_id, args.subtask_id)
        print(f"테스트 결과: {result}")


if __name__ == "__main__":
    main()
