import pyautogui
import time

print("현재 열려있는 모든 창 목록:")
print("="*50)

# 모든 창 목록 가져오기
all_windows = pyautogui.getAllWindows()
for i, window in enumerate(all_windows):
    if window.title:  # 빈 제목이 아닌 경우만
        print(f"{i+1}. '{window.title}'")
        
print("\n특정 단어가 포함된 창 찾기:")
print("="*50)

# Claude 관련 창 찾기
search_terms = ['Claude', 'claude', 'CLAUDE', '클로드']
for term in search_terms:
    windows = pyautogui.getWindowsWithTitle(term)
    if windows:
        print(f"'{term}' 포함된 창 발견:")
        for window in windows:
            print(f"  - '{window.title}'")

print("\n팁: Claude Desktop의 정확한 창 제목을 위의 목록에서 찾아")
print("claude_desktop_config.json의 'window_title' 값을 업데이트하세요.")
