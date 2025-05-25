import pyautogui
import time
import os
import logging
import argparse
import json
from PIL import Image, ImageGrab
import cv2
import numpy as np

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("claude_automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("claude_automation")

class ClaudeDesktopAutomation:
    def __init__(self, config_path=None):
        """
        Claude Desktop GUI 자동화 클래스 초기화
        
        Args:
            config_path (str, optional): 설정 파일 경로. 기본값은 None.
        """
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
                logger.info(f"설정 파일 로드 완료: {config_path}")
            except Exception as e:
                logger.error(f"설정 파일 로드 실패: {e}")
        
        # 에셋 디렉토리 확인 및 생성
        self.assets_dir = self.config["assets_dir"]
        if not os.path.exists(self.assets_dir):
            os.makedirs(self.assets_dir)
            logger.info(f"에셋 디렉토리 생성: {self.assets_dir}")
        
        # 이미지 파일 경로
        self.continue_button_image = os.path.join(self.assets_dir, self.config["continue_button_image"])
        self.new_chat_button_image = os.path.join(self.assets_dir, self.config["new_chat_button_image"])
        
        # 창 활성화 여부 확인
        self.window_active = False
        
        logger.info("Claude Desktop 자동화 초기화 완료")
    
    def activate_window(self):
        """Claude Desktop 창을 활성화합니다."""
        try:
            # 창 제목으로 창 찾기
            window = pyautogui.getWindowsWithTitle(self.config["window_title"])
            if window:
                window[0].activate()
                time.sleep(1)  # 창이 활성화될 때까지 대기
                self.window_active = True
                logger.info("Claude Desktop 창 활성화 성공")
                return True
            else:
                logger.error(f"Claude Desktop 창을 찾을 수 없습니다. 창 제목: {self.config['window_title']}")
                return False
        except Exception as e:
            logger.error(f"창 활성화 중 오류 발생: {e}")
            return False
    
    def find_and_click_image(self, image_path, max_retries=None, confidence=None):
        """
        화면에서 이미지를 찾아 클릭합니다.
        
        Args:
            image_path (str): 찾을 이미지 파일 경로
            max_retries (int, optional): 최대 재시도 횟수
            confidence (float, optional): 이미지 인식 신뢰도 (0.0 ~ 1.0)
            
        Returns:
            bool: 성공 여부
        """
        if max_retries is None:
            max_retries = self.config["max_retries"]
        
        if confidence is None:
            confidence = self.config["confidence_threshold"]
        
        if not os.path.exists(image_path):
            logger.error(f"이미지 파일을 찾을 수 없습니다: {image_path}")
            return False
        
        for attempt in range(max_retries):
            try:
                location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
                if location:
                    pyautogui.click(location)
                    logger.info(f"이미지 클릭 성공: {image_path}")
                    return True
                else:
                    logger.warning(f"이미지를 찾을 수 없습니다 ({attempt+1}/{max_retries}): {image_path}")
                    time.sleep(self.config["screenshot_delay"])
            except Exception as e:
                logger.error(f"이미지 찾기 중 오류 발생: {e}")
                time.sleep(self.config["screenshot_delay"])
        
        logger.error(f"이미지 찾기 실패 (최대 재시도 횟수 초과): {image_path}")
        return False
    
    def find_text_on_screen(self, text, max_retries=None):
        """
        화면에서 텍스트를 찾습니다. (OCR 기능 필요)
        
        Args:
            text (str): 찾을 텍스트
            max_retries (int, optional): 최대 재시도 횟수
            
        Returns:
            tuple or None: 텍스트 위치 (x, y) 또는 None
        """
        # 참고: 이 기능은 pytesseract 등의 OCR 라이브러리가 필요합니다.
        # 현재 구현에서는 간단히 이미지 기반 검색으로 대체합니다.
        logger.warning("텍스트 기반 검색은 현재 구현되지 않았습니다. 이미지 기반 검색을 사용하세요.")
        return None
    
    def capture_and_save_button(self, button_name, region=None):
        """
        화면의 특정 영역을 캡처하여 버튼 이미지로 저장합니다.
        
        Args:
            button_name (str): 버튼 이름 (continue 또는 new_chat)
            region (tuple, optional): 캡처할 영역 (left, top, width, height)
            
        Returns:
            bool: 성공 여부
        """
        try:
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                # 사용자에게 버튼 위치 지정 요청
                logger.info(f"{button_name} 버튼 위치를 지정해주세요. 5초 후 마우스 위치를 캡처합니다...")
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
            logger.info(f"{button_name} 버튼 이미지 저장 완료: {image_path}")
            return True
        
        except Exception as e:
            logger.error(f"버튼 캡처 중 오류 발생: {e}")
            return False
    
    def input_text(self, text):
        """
        Claude Desktop 입력창에 텍스트를 입력합니다.
        
        Args:
            text (str): 입력할 텍스트
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 창이 활성화되어 있는지 확인
            if not self.window_active:
                if not self.activate_window():
                    return False
            
            # 텍스트 입력 (Ctrl+A로 기존 텍스트 선택 후 삭제)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(self.config["input_delay"])
            pyautogui.write(text)
            logger.info(f"텍스트 입력 완료: {text[:50]}..." if len(text) > 50 else f"텍스트 입력 완료: {text}")
            return True
        
        except Exception as e:
            logger.error(f"텍스트 입력 중 오류 발생: {e}")
            return False
    
    def press_enter(self):
        """Enter 키를 누릅니다."""
        try:
            pyautogui.press('enter')
            logger.info("Enter 키 입력 완료")
            return True
        except Exception as e:
            logger.error(f"Enter 키 입력 중 오류 발생: {e}")
            return False
    
    def click_continue_button(self):
        """'계속하기' 버튼을 클릭합니다."""
        logger.info("'계속하기' 버튼 찾기 시도...")
        return self.find_and_click_image(self.continue_button_image)
    
    def click_new_chat_button(self):
        """'새 채팅' 버튼을 클릭합니다."""
        logger.info("'새 채팅' 버튼 찾기 시도...")
        return self.find_and_click_image(self.new_chat_button_image)
    
    def setup_buttons(self):
        """버튼 이미지를 설정합니다."""
        logger.info("버튼 이미지 설정을 시작합니다...")
        
        # 계속하기 버튼 캡처
        logger.info("'계속하기' 버튼 위치를 지정해주세요.")
        self.capture_and_save_button("continue")
        
        # 새 채팅 버튼 캡처
        logger.info("'새 채팅' 버튼 위치를 지정해주세요.")
        self.capture_and_save_button("new_chat")
        
        logger.info("버튼 이미지 설정이 완료되었습니다.")
    
    def run_automation(self, input_text, wait_for_continue=True, create_new_chat=False):
        """
        자동화 작업을 실행합니다.
        
        Args:
            input_text (str): 입력할 텍스트
            wait_for_continue (bool): '계속하기' 버튼을 기다릴지 여부
            create_new_chat (bool): 새 채팅을 생성할지 여부
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 창 활성화
            if not self.activate_window():
                return False
            
            # 새 채팅 생성 (필요한 경우)
            if create_new_chat:
                if not self.click_new_chat_button():
                    logger.warning("새 채팅 생성 실패, 계속 진행합니다.")
                time.sleep(1)
            
            # 텍스트 입력
            if not self.input_text(input_text):
                return False
            
            # Enter 키 입력
            if not self.press_enter():
                return False
            
            # '계속하기' 버튼 대기 (필요한 경우)
            if wait_for_continue:
                logger.info("'계속하기' 버튼 대기 중...")
                max_wait_time = 60  # 최대 60초 대기
                wait_interval = 5   # 5초마다 확인
                
                for _ in range(max_wait_time // wait_interval):
                    time.sleep(wait_interval)
                    if self.click_continue_button():
                        logger.info("'계속하기' 버튼 클릭 성공")
                        break
                else:
                    logger.warning("'계속하기' 버튼을 찾을 수 없습니다. 시간 초과.")
            
            logger.info("자동화 작업 완료")
            return True
        
        except Exception as e:
            logger.error(f"자동화 작업 중 오류 발생: {e}")
            return False


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='Claude Desktop GUI 자동화 도구')
    parser.add_argument('--config', type=str, help='설정 파일 경로')
    parser.add_argument('--setup', action='store_true', help='버튼 이미지 설정 모드')
    parser.add_argument('--input', type=str, help='입력할 텍스트 또는 텍스트 파일 경로')
    parser.add_argument('--wait-continue', action='store_true', help='계속하기 버튼 대기')
    parser.add_argument('--new-chat', action='store_true', help='새 채팅 생성')
    
    args = parser.parse_args()
    
    # 자동화 객체 생성
    automation = ClaudeDesktopAutomation(args.config)
    
    # 버튼 이미지 설정 모드
    if args.setup:
        automation.setup_buttons()
        return
    
    # 입력 텍스트 준비
    input_text = ""
    if args.input:
        if os.path.isfile(args.input):
            try:
                with open(args.input, 'r', encoding='utf-8') as f:
                    input_text = f.read()
            except Exception as e:
                logger.error(f"파일 읽기 실패: {e}")
                return
        else:
            input_text = args.input
    
    if not input_text:
        logger.error("입력 텍스트가 없습니다.")
        return
    
    # 자동화 실행
    automation.run_automation(
        input_text=input_text,
        wait_for_continue=args.wait_continue,
        create_new_chat=args.new_chat
    )


if __name__ == "__main__":
    main()
