import pyautogui
import time
import os
import logging
import argparse
import json
# from PIL import Image, ImageGrab # pyautogui가 내부적으로 사용하므로 직접 임포트 불필요할 수 있음
# import cv2 # pyautogui가 내부적으로 사용하거나, 이미지 처리 시 직접 사용
# import numpy as np # cv2 사용 시 필요할 수 있음

# 로그 디렉토리 생성
LOGS_DIR = "logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# 로깅 설정
log_file_path = os.path.join(LOGS_DIR, "claude_automation.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("claude_automation")

class ClaudeDesktopAutomation:
    def __init__(self, config_path="claude_desktop_config.json", project_root_path="."):
        """
        Claude Desktop GUI 자동화 클래스 초기화
        
        Args:
            config_path (str, optional): 설정 파일 경로.
            project_root_path (str, optional): 프로젝트 루트 경로. assets_dir 상대 경로의 기준.
        """
        self.default_config = {
            "window_title": "Claude",
            "input_delay": 0.5,
            "screenshot_delay": 1.0,
            "max_retries": 3,
            "confidence_threshold": 0.7,
            "assets_dir": "assets", # 설정 파일 위치 기준 상대 경로 또는 절대 경로
            "continue_button_image": "continue_button.png",
            "new_chat_button_image": "new_chat_button.png"
            # "continue_button_text" and "new_chat_button_text" are not used for image-based search
        }
        
        self.config = self.default_config.copy()
        self.config_file_path = os.path.abspath(config_path) # 설정 파일의 절대 경로
        
        if os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, 'r') as f:
                    user_config = json.load(f)
                    self.config.update(user_config)
                logger.info(f"설정 파일 로드 완료: {self.config_file_path}")
            except Exception as e:
                logger.error(f"설정 파일 로드 실패 ({self.config_file_path}): {e}")
        else:
            logger.warning(f"설정 파일을 찾을 수 없습니다: {self.config_file_path}. 기본 설정을 사용합니다.")

        # assets_dir 처리: 설정 파일에 지정된 경로가 절대 경로가 아니면, 설정 파일의 디렉토리를 기준으로 경로 조합
        # 또는 project_root_path를 기준으로 할 수도 있음. 여기서는 설정 파일 기준.
        if not os.path.isabs(self.config["assets_dir"]):
            self.assets_dir = os.path.join(os.path.dirname(self.config_file_path), self.config["assets_dir"])
        else:
            self.assets_dir = self.config["assets_dir"]
        
        if not os.path.exists(self.assets_dir):
            try:
                os.makedirs(self.assets_dir)
                logger.info(f"에셋 디렉토리 생성: {self.assets_dir}")
            except OSError as e:
                logger.error(f"에셋 디렉토리 생성 실패 ({self.assets_dir}): {e}. 이미지 기반 자동화가 실패할 수 있습니다.")
                # assets_dir이 없으면 이미지 경로 설정 시 오류 발생하므로, 여기서 처리 필요
                # 예를 들어, 기본값으로 현재 디렉토리의 'assets'를 사용하도록 할 수 있음
                self.assets_dir = os.path.join(os.getcwd(), "assets") # Fallback
                if not os.path.exists(self.assets_dir):
                    os.makedirs(self.assets_dir, exist_ok=True)


        self.continue_button_image = os.path.join(self.assets_dir, self.config["continue_button_image"])
        # new_chat_button은 더 이상 사용하지 않음 (Projects를 통해 새 채팅 생성)
        
        # 필수 이미지 파일 확인
        self._check_required_images()
        
        self.window_active = False
        logger.info("Claude Desktop 자동화 초기화 완료")
    
    def _check_required_images(self):
        """필수 이미지 파일들이 있는지 확인"""
        required_images = [
            ("continue_button_image", self.config["continue_button_image"]),
            ("projects_button_image", self.config.get("projects_button_image", "projects_button.png")),
            ("max_length_message_image", self.config.get("max_length_message_image", "max_length_message.png"))
        ]
        
        missing_images = []
        for name, filename in required_images:
            image_path = os.path.join(self.assets_dir, filename)
            if not os.path.exists(image_path):
                missing_images.append(filename)
        
        if missing_images:
            logger.warning(f"다음 이미지 파일들이 없습니다: {', '.join(missing_images)}")
            logger.warning(f"assets 폴더에 이미지를 추가하거나 --setup 옵션을 사용하여 캡처하세요.")
            logger.warning(f"자세한 내용은 {os.path.join(self.assets_dir, 'README.md')}를 참조하세요.")
    
    def activate_window(self):
        try:
            windows = pyautogui.getWindowsWithTitle(self.config["window_title"])
            if windows:
                window = windows[0]
                if not window.isActive: # 이미 활성화된 경우 다시 활성화 시도하지 않음
                    window.activate()
                if not window.isMaximized: # 최대화되어 있지 않으면 최대화 (선택 사항)
                    window.maximize()
                time.sleep(1) 
                self.window_active = True
                logger.info(f"'{self.config['window_title']}' 창 활성화 성공")
                return True
            else:
                logger.error(f"'{self.config['window_title']}' 창을 찾을 수 없습니다.")
                return False
        except Exception as e:
            logger.error(f"창 활성화 중 오류 발생: {e}")
            return False
    
    def find_and_click_image(self, image_path, max_retries=None, confidence=None):
        if max_retries is None:
            max_retries = self.config["max_retries"]
        if confidence is None:
            confidence = self.config["confidence_threshold"]
        
        if not os.path.exists(image_path):
            logger.error(f"이미지 파일을 찾을 수 없습니다: {image_path}")
            logger.error(f"assets 폴더에 이미지를 추가하거나 --setup 옵션을 사용하여 캡처하세요.")
            return False
        
        for attempt in range(max_retries):
            try:
                # pyautogui.locateCenterOnScreen은 전체 화면에서 찾음.
                # 활성화된 창 내부에서만 찾으려면 추가적인 로직 (예: 창 영역 캡처 후 검색) 필요.
                # 여기서는 단순하게 전체 화면 검색 사용.
                location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
                if location:
                    pyautogui.click(location)
                    logger.info(f"이미지 클릭 성공: {image_path} at {location}")
                    return True
                else:
                    logger.warning(f"이미지를 화면에서 찾을 수 없습니다 ({attempt+1}/{max_retries}): {image_path}")
                    time.sleep(self.config["screenshot_delay"])
            except pyautogui.PyAutoGUIException as e: # pyautogui 관련 예외 명시
                logger.error(f"이미지 찾기/클릭 중 PyAutoGUI 오류 발생 ({image_path}): {e}")
                time.sleep(self.config["screenshot_delay"])
            except Exception as e: # 기타 예외
                logger.error(f"이미지 찾기/클릭 중 예기치 않은 오류 발생 ({image_path}): {e}")
                time.sleep(self.config["screenshot_delay"])
        
        logger.error(f"이미지 찾기 실패 (최대 재시도 횟수 초과): {image_path}")
        return False
    
    def capture_and_save_button(self, button_name_key, image_file_name, prompt_message):
        """
        화면의 특정 영역을 캡처하여 버튼 이미지로 저장합니다.
        
        Args:
            button_name_key (str): 설정에서 사용할 버튼 이름 키 (예: "continue_button_image")
            image_file_name (str): 저장할 이미지 파일 이름 (예: "continue_button.png")
            prompt_message (str): 사용자에게 안내할 메시지
        """
        try:
            logger.info(prompt_message)
            logger.info("캡처할 버튼 위에 마우스를 올리고 5초간 기다려주세요...")
            time.sleep(5)
            x, y = pyautogui.position()
            
            # 버튼 주변 영역 캡처 (사용자가 크기 조절 가능하도록 개선 여지 있음)
            # 예시: 가로 100px, 세로 50px 영역
            # 사용자가 직접 드래그하여 영역을 지정하게 하는 것이 더 정확할 수 있음
            logger.info("버튼 영역을 지정해주세요. 첫번째 클릭: 왼쪽 위, 두번째 클릭: 오른쪽 아래 (10초 내)")
            
            # 간단한 클릭 기반 영역 지정 (더 정교한 UI는 tkinter 등 사용)
            # 여기서는 고정 크기 캡처로 단순화 또는 pyautogui.prompt 활용
            # pyautogui.alert('버튼의 왼쪽 위 모서리를 클릭하고 Enter를 누르세요.')
            # left_top = pyautogui.position()
            # pyautogui.alert('버튼의 오른쪽 아래 모서리를 클릭하고 Enter를 누르세요.')
            # right_bottom = pyautogui.position()
            # region_width = right_bottom.x - left_top.x
            # region_height = right_bottom.y - left_top.y
            # region = (left_top.x, left_top.y, region_width, region_height)

            # 여기서는 마우스 위치 중심의 고정 크기로 캡처
            capture_width = 150 
            capture_height = 60
            region = (x - capture_width // 2, y - capture_height // 2, capture_width, capture_height)
            
            screenshot = pyautogui.screenshot(region=region)
            
            image_path = os.path.join(self.assets_dir, image_file_name)
            screenshot.save(image_path)
            logger.info(f"'{image_file_name}' 버튼 이미지 저장 완료: {image_path}")
            
            # 설정 파일에도 저장된 이미지 파일명 업데이트 (선택적)
            # self.config[button_name_key] = image_file_name
            # with open(self.config_file_path, 'w') as f:
            #     json.dump(self.config, f, indent=2)
            # logger.info(f"설정 파일 업데이트: {self.config_file_path}")
            return True
        
        except Exception as e:
            logger.error(f"버튼 캡처 중 오류 발생 ({image_file_name}): {e}")
            return False
    
    def input_text(self, text):
        if not self.window_active:
            if not self.activate_window():
                return False
        try:
            # 입력창을 특정하거나, 단순히 현재 활성화된 곳에 입력
            # Claude Desktop의 경우, 창 활성화 후 바로 입력 가능할 것으로 가정
            pyautogui.hotkey('ctrl', 'a') # 전체 선택
            time.sleep(0.1) # 약간의 딜레이
            pyautogui.press('delete') # 삭제
            time.sleep(0.1)
            pyautogui.write(text, interval=0.01) # 타이핑 간격 추가하여 안정성 향상
            logger.info(f"텍스트 입력 완료 (첫 50자): {text[:50]}...")
            return True
        except Exception as e:
            logger.error(f"텍스트 입력 중 오류 발생: {e}")
            return False
    
    def press_enter(self):
        if not self.window_active: # 엔터 전 창 활성화 확인
            if not self.activate_window():
                logger.warning("Enter 키 입력 전 창 활성화 실패.")
                # 실패로 처리할지, 그냥 진행할지 정책 필요
        try:
            pyautogui.press('enter')
            logger.info("Enter 키 입력 완료")
            return True
        except Exception as e:
            logger.error(f"Enter 키 입력 중 오류 발생: {e}")
            return False
    
    def click_continue_button(self):
        logger.info(f"'계속하기' 버튼 ({self.config['continue_button_image']}) 찾기 시도...")
        return self.find_and_click_image(self.continue_button_image)
    
    def check_max_length_message(self):
        """화면에 max length 메시지가 있는지 확인"""
        max_length_image = os.path.join(self.assets_dir, self.config.get("max_length_message_image", "max_length_message.png"))
        if os.path.exists(max_length_image):
            try:
                location = pyautogui.locateOnScreen(max_length_image, confidence=self.config["confidence_threshold"])
                if location:
                    logger.info("Max length 메시지 감지됨")
                    return True
            except Exception as e:
                logger.error(f"Max length 메시지 확인 중 오류: {e}")
        return False
    
    def click_projects_button(self):
        """Projects 버튼 클릭"""
        projects_button_image = os.path.join(self.assets_dir, self.config.get("projects_button_image", "projects_button.png"))
        logger.info(f"'Projects' 버튼 ({projects_button_image}) 찾기 시도...")
        return self.find_and_click_image(projects_button_image)
    
    def click_project_button(self, project_name):
        """특정 프로젝트 버튼 클릭"""
        project_button_image = os.path.join(self.assets_dir, f"{project_name}_button.png")
        if not os.path.exists(project_button_image):
            # 일반적인 프로젝트 버튼 이미지 사용
            project_button_image = os.path.join(self.assets_dir, self.config.get("project_button_image", "project_button.png"))
        
        logger.info(f"'{project_name}' 프로젝트 버튼 ({project_button_image}) 찾기 시도...")
        return self.find_and_click_image(project_button_image)
    
    def create_new_chat_via_projects(self, project_name):
        """Projects를 통해 새 채팅 생성"""
        logger.info(f"Projects를 통해 '{project_name}' 프로젝트에서 새 채팅을 생성합니다...")
        
        # 1. Projects 버튼 클릭
        if not self.click_projects_button():
            logger.error("Projects 버튼을 찾을 수 없습니다.")
            return False
        
        time.sleep(1)  # Projects 메뉴 로딩 대기
        
        # 2. 프로젝트 버튼 클릭
        if not self.click_project_button(project_name):
            logger.error(f"{project_name} 프로젝트 버튼을 찾을 수 없습니다.")
            return False
        
        time.sleep(2)  # 프로젝트 로딩 대기
        logger.info(f"'{project_name}' 프로젝트에서 새 채팅 준비 완료")
        return True
    
    def handle_max_length(self, project_name):
        """Max length 상황 처리 - 동일한 로직으로 새 채팅 생성"""
        return self.create_new_chat_via_projects(project_name)
    
    def click_new_chat_button(self):
        # Deprecated: 이제 Projects를 통해 새 채팅 생성
        logger.warning("click_new_chat_button은 더 이상 사용되지 않습니다. create_new_chat_via_projects를 사용하세요.")
        return False
    
    def setup_buttons(self):
        logger.info("버튼 이미지 설정을 시작합니다...")
        logger.info("TIP: 이미 캡처된 이미지가 있다면 이 단계를 건너뛸 수 있습니다.")
        
        if not self.activate_window():
            logger.error("Claude 창을 활성화할 수 없어 버튼 설정을 진행할 수 없습니다.")
            return

        # 각 버튼에 대해 기존 이미지 확인 후 캡처
        buttons_to_capture = [
            ("continue_button_image", self.config["continue_button_image"], "'계속하기(Continue)' 버튼"),
            ("projects_button_image", self.config.get("projects_button_image", "projects_button.png"), "'Projects' 버튼 (왼쪽 위)"),
            ("max_length_message_image", self.config.get("max_length_message_image", "max_length_message.png"), "'Max length' 메시지 (하단)")
        ]
        
        for config_key, filename, description in buttons_to_capture:
            image_path = os.path.join(self.assets_dir, filename)
            if os.path.exists(image_path):
                response = input(f"{filename}이 이미 존재합니다. 덮어쓰시겠습니까? (y/N): ").strip().lower()
                if response != 'y':
                    logger.info(f"{filename} 캡처를 건너뜁니다.")
                    continue
            
            self.capture_and_save_button(config_key, filename, description)
        
        # 프로젝트 버튼 (선택적)
        project_name = input("프로젝트 이름을 입력하세요 (선택사항, Enter로 건너뛰기): ").strip()
        if project_name:
            project_filename = f"{project_name}_button.png"
            project_image_path = os.path.join(self.assets_dir, project_filename)
            if os.path.exists(project_image_path):
                response = input(f"{project_filename}이 이미 존재합니다. 덮어쓰시겠습니까? (y/N): ").strip().lower()
                if response == 'y':
                    self.capture_and_save_button(
                        f"{project_name}_button_image",
                        project_filename,
                        f"'{project_name}' 프로젝트 버튼"
                    )
            else:
                self.capture_and_save_button(
                    f"{project_name}_button_image",
                    project_filename,
                    f"'{project_name}' 프로젝트 버튼"
                )
        
        logger.info("버튼 이미지 설정이 완료되었습니다.")
        logger.info(f"이미지들은 {self.assets_dir}에 저장되었습니다.")
    
    def run_automation(self, input_text_content, wait_for_continue=True, create_new_chat=False, project_name=None):
        if not self.activate_window():
            return False
        
        if create_new_chat:
            # 새 채팅은 항상 Projects를 통해 생성
            if not project_name:
                logger.error("새 채팅 생성 시 프로젝트 이름이 필요합니다.")
                return False
            
            # Max length 메시지 확인
            if self.check_max_length_message():
                logger.info("Max length 메시지 감지됨. Projects를 통해 새 채팅 시작...")
            else:
                logger.info("새 채팅을 생성합니다...")
            
            # Projects를 통해 새 채팅 생성
            if not self.create_new_chat_via_projects(project_name):
                logger.error("새 채팅 생성 실패")
                return False
            
        if not self.input_text(input_text_content):
            return False
        
        if not self.press_enter():
            return False
        
        if wait_for_continue:
            logger.info("'계속하기' 버튼 클릭 또는 응답 완료 대기 중...")
            # '계속하기' 버튼은 응답이 길 때 나타나므로, 이 버튼을 찾는 것은 응답이 길 경우에만 유효.
            # 짧은 응답 후에는 이 버튼이 없을 수 있음.
            # 따라서, 버튼을 찾되, 일정 시간 후에도 없으면 그냥 통과하는 로직이 필요할 수 있음.
            # 또는 Claude 응답 완료를 나타내는 다른 시각적 지표를 찾아야 함.
            
            # 여기서는 '계속하기' 버튼을 최대 N초 동안 주기적으로 확인
            max_wait_seconds = 60 
            check_interval = 3
            waited_time = 0
            continue_clicked = False
            while waited_time < max_wait_seconds:
                if self.click_continue_button():
                    logger.info("'계속하기' 버튼 클릭 성공")
                    continue_clicked = True
                    # '계속하기'를 여러 번 눌러야 할 수도 있으므로, 클릭 후에도 잠시 더 대기하며 확인
                    time.sleep(check_interval) # 추가 응답 시간
                    waited_time += check_interval
                    # continue # 계속 버튼이 또 나올 수 있으므로 루프 지속
                else:
                    # '계속하기' 버튼이 없다면, 응답이 완료되었거나 아직 생성 중일 수 있음.
                    # 여기서는 단순화를 위해 루프를 한번 더 돌거나 종료.
                    # 좀 더 정교하게는 "응답 완료" 상태를 파악해야 함.
                    logger.info(f"'계속하기' 버튼 없음. {max_wait_seconds - waited_time}초 더 대기...")
                    time.sleep(check_interval)
                    waited_time += check_interval
                    # 만약 continue_clicked가 한번이라도 true였다면, 
                    # 그리고 더 이상 continue 버튼이 안보인다면 완료로 간주하고 break 가능
                    if continue_clicked and not pyautogui.locateOnScreen(self.continue_button_image, confidence=self.config['confidence_threshold']):
                        logger.info("추가 '계속하기' 버튼 없음. 응답 완료로 간주.")
                        break
            
            if not continue_clicked and waited_time >= max_wait_seconds :
                logger.warning(f"'계속하기' 버튼을 시간 내({max_wait_seconds}초)에 찾거나 클릭하지 못했습니다. 응답이 짧거나 다른 상태일 수 있습니다.")
            elif continue_clicked:
                 logger.info("긴 응답 처리 완료 (계속하기 버튼 사용).")
            else:
                 logger.info("짧은 응답으로 간주 (계속하기 버튼 없음).")


        logger.info("자동화 작업 완료")
        return True

def main():
    parser = argparse.ArgumentParser(description='Claude Desktop GUI 자동화 도구')
    parser.add_argument('--config', type=str, default="claude_desktop_config.json", help='Claude 자동화 설정 파일 경로')
    parser.add_argument('--project-root', type=str, default=".", help='프로젝트 루트 경로 (assets 상대 경로 기준)')
    parser.add_argument('--project-name', type=str, help='Claude 프로젝트 이름')
    parser.add_argument('--setup', action='store_true', help='버튼 이미지 설정 모드')
    parser.add_argument('--input', type=str, help='입력할 텍스트 또는 텍스트 파일 경로')
    parser.add_argument('--wait-continue', action='store_true', help="'계속하기' 버튼 대기 및 클릭 (긴 응답 처리)")
    parser.add_argument('--new-chat', action='store_true', help='새 채팅 생성 후 프롬프트 입력')
    
    args = parser.parse_args()
    
    automation = ClaudeDesktopAutomation(config_path=args.config, project_root_path=args.project_root)
    
    if args.setup:
        automation.setup_buttons()
        return
    
    # setup 모드가 아닌 경우, 필수 이미지 확인
    required_images = [
        automation.continue_button_image,
        os.path.join(automation.assets_dir, automation.config.get("projects_button_image", "projects_button.png")),
        os.path.join(automation.assets_dir, automation.config.get("max_length_message_image", "max_length_message.png"))
    ]
    
    missing_images = [img for img in required_images if not os.path.exists(img)]
    if missing_images:
        logger.error("필수 이미지 파일이 없습니다.")
        logger.error("다음 중 하나를 수행하세요:")
        logger.error("1. assets 폴더에 필요한 이미지 파일 추가")
        logger.error("2. python claude_desktop_automation.py --setup 실행하여 이미지 캡처")
        return
    
    input_text_content = ""
    if args.input:
        if os.path.isfile(args.input):
            try:
                with open(args.input, 'r', encoding='utf-8') as f:
                    input_text_content = f.read()
                logger.info(f"파일에서 텍스트 로드: {args.input}")
            except Exception as e:
                logger.error(f"입력 파일 읽기 실패 ({args.input}): {e}")
                return
        else:
            input_text_content = args.input
    
    if not input_text_content:
        logger.error("입력 텍스트가 없습니다. --input 인자로 텍스트나 파일 경로를 제공하세요.")
        return
    
    automation.run_automation(
        input_text_content=input_text_content,
        wait_for_continue=args.wait_continue,
        create_new_chat=args.new_chat,
        project_name=args.project_name
    )

if __name__ == "__main__":
    main()