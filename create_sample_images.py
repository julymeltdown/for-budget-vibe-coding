"""
샘플 버튼 이미지를 생성하는 스크립트
실제 사용 시에는 Claude Desktop에서 캡처한 이미지로 교체해야 합니다.
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_button_image(text, width, height, filename):
    """간단한 버튼 이미지 생성"""
    # 흰 배경의 이미지 생성
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # 버튼 테두리 그리기
    draw.rectangle([0, 0, width-1, height-1], outline='black', width=2)
    
    # 텍스트 추가 (기본 폰트 사용)
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()
    
    # 텍스트 중앙 정렬
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    draw.text((x, y), text, fill='black', font=font)
    
    # 저장
    assets_dir = 'assets'
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
    
    filepath = os.path.join(assets_dir, filename)
    img.save(filepath)
    print(f"생성됨: {filepath}")

def main():
    print("샘플 버튼 이미지를 생성합니다...")
    print("주의: 이는 참고용 샘플입니다. 실제 사용 시 Claude Desktop에서 캡처한 이미지로 교체하세요.")
    
    # 샘플 이미지 생성
    buttons = [
        ("Continue", 150, 60, "continue_button.png"),
        ("Projects", 100, 40, "projects_button.png"),
        ("Claude hit the maximum length...", 600, 50, "max_length_message.png"),
        ("kido", 200, 50, "kido_button.png"),
        ("My Project", 200, 50, "project_button.png")
    ]
    
    for text, width, height, filename in buttons:
        create_button_image(text, width, height, filename)
    
    print("\n샘플 이미지 생성 완료!")
    print("실제 사용을 위해서는 Claude Desktop에서 직접 캡처하세요:")
    print("1. Win + Shift + S 사용")
    print("2. 또는 python claude_desktop_automation.py --setup")

if __name__ == "__main__":
    # PIL/Pillow 설치 확인
    try:
        from PIL import Image, ImageDraw, ImageFont
        main()
    except ImportError:
        print("PIL/Pillow가 설치되어 있지 않습니다.")
        print("설치하려면: pip install Pillow")
        print("\n또는 수동으로 이미지를 캡처하세요:")
        print("- Win + Shift + S 사용")
        print("- assets 폴더에 PNG 파일로 저장")