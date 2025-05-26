# Claude Desktop 버튼 이미지 캡처 가이드

## 빠른 캡처 방법 (Windows)

### 1. Continue 버튼 캡처
1. Claude에서 긴 텍스트를 입력하여 Continue 버튼이 나타나게 함
2. Win + Shift + S 누르기
3. Continue 버튼만 정확히 선택
4. `continue_button.png`로 저장

### 2. Projects 버튼 캡처  
1. Claude Desktop 열기
2. Win + Shift + S 누르기
3. 왼쪽 상단의 "Projects" 텍스트 영역 선택
4. `projects_button.png`로 저장

### 3. Max Length 메시지 캡처
1. 긴 대화를 진행하여 max length 메시지가 나타나게 함
2. Win + Shift + S 누르기
3. 하단의 "Claude hit the maximum length..." 메시지 영역 선택
4. `max_length_message.png`로 저장

### 4. Usage Limit 메시지 캡처
1. 사용량 한도에 도달했을 때 나타나는 메시지 확인
2. Win + Shift + S 누르기
3. "try again in 2 hours" 등의 메시지가 포함된 영역 선택
4. `usage_limit_message.png`로 저장

### 5. 프로젝트 버튼 캡처 (예: kido)
1. Projects 클릭
2. Win + Shift + S 누르기
3. 프로젝트 이름이 있는 버튼 영역 선택
4. `kido_button.png`로 저장 (프로젝트 이름에 맞게)

## 캡처 시 주의사항

1. **배경 제외**: 버튼의 텍스트와 테두리만 포함
2. **여백 최소화**: 클릭 영역만 정확히 캡처
3. **고정 배율**: Windows 디스플레이 설정 100% 확인
4. **PNG 형식**: 투명도 지원을 위해 PNG 사용

## 이미지 크기 참고
- Continue 버튼: 약 150x60 픽셀
- Projects 버튼: 약 100x40 픽셀  
- Max length 메시지: 약 600x50 픽셀
- Usage limit 메시지: 약 400x80 픽셀
- 프로젝트 버튼: 약 200x50 픽셀

## 자동 캡처 사용
이미지를 수동으로 캡처하기 어려운 경우:
```bash
python claude_desktop_automation.py --setup
```

하지만 수동 캡처가 더 정확한 결과를 얻을 수 있습니다.