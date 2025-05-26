from claude_desktop_automation import ClaudeDesktopAutomation
import logging

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)

print("Claude Desktop 테스트 시작...")

# ClaudeDesktopAutomation 초기화
automation = ClaudeDesktopAutomation()

# 1. 창 활성화 테스트
print("\n1. 창 활성화 테스트...")
if automation.activate_window():
    print("✓ Claude Desktop 창 활성화 성공!")
else:
    print("✗ Claude Desktop 창을 찾을 수 없습니다.")
    print("\n해결 방법:")
    print("1. Claude Desktop이 실행 중인지 확인하세요")
    print("2. python check_windows.py를 실행하여 정확한 창 제목을 확인하세요")
    print("3. claude_desktop_config.json의 'window_title'을 업데이트하세요")
    
# 2. 프로젝트 버튼 이미지 확인
print("\n2. 필수 이미지 파일 확인...")
import os

required_images = [
    "continue_button.png",
    "projects_button.png", 
    "max_length_message.png",
    "usage_limit_message.png"
]

missing_images = []
for img in required_images:
    img_path = os.path.join(automation.assets_dir, img)
    if os.path.exists(img_path):
        print(f"✓ {img} 존재")
    else:
        print(f"✗ {img} 없음")
        missing_images.append(img)

if missing_images:
    print(f"\n누락된 이미지: {', '.join(missing_images)}")
    print("python claude_desktop_automation.py --setup 을 실행하여 이미지를 캡처하세요")
