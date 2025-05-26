# 새 채팅 생성 로직 업데이트

## 변경 사항

기존의 `new_chat_button` 클릭 방식을 제거하고, 모든 새 채팅은 **Projects 메뉴를 통해서만** 생성하도록 변경했습니다.

## 새로운 로직

### 1. 새 채팅 생성 순서
1. **Projects 버튼 클릭** (왼쪽 상단)
2. **프로젝트명 버튼 클릭** (예: kido)
3. **프롬프트 입력**

### 2. 코드 변경 사항

#### claude_desktop_automation.py
- `click_new_chat_button()`: Deprecated 처리
- `create_new_chat_via_projects()`: 새로운 메서드 추가
- `run_automation()`: 새 채팅 생성 시 항상 Projects 사용

#### task_orchestrator_enhanced.py
- `project_name` 파라미터 자동 전달
- `config.json`의 `dev_project_name` 사용

## 사용 방법

### 1. 기본 사용
```python
# 프로젝트명 필수
automation.run_automation(
    input_text_content="프롬프트",
    create_new_chat=True,
    project_name="kido"  # 필수!
)
```

### 2. config.json 설정
```json
{
  "dev_project_name": "kido",  // 이 값이 자동으로 사용됨
  ...
}
```

### 3. 필요한 이미지 파일
- `assets/projects_button.png` - Projects 버튼
- `assets/kido_button.png` - 프로젝트별 버튼
- `assets/continue_button.png` - Continue 버튼
- `assets/max_length_message.png` - Max length 메시지 (선택)

### 4. 이미지 캡처
```bash
python claude_desktop_automation.py --setup
```
프로젝트 이름 입력 시 해당 프로젝트 버튼도 캡처됩니다.

## 주의사항

1. **new_chat_button.png는 더 이상 필요 없음**
2. **create_new_chat=True 시 project_name은 필수**
3. Max length 상황과 일반 새 채팅 모두 동일한 로직 사용
4. 프로젝트명 버튼 이미지가 없으면 실패함

## 장점

- 일관된 새 채팅 생성 방식
- Max length 상황 자동 처리
- 프로젝트 컨텍스트 유지
- 더 안정적인 자동화

## 문제 해결

### "프로젝트 버튼을 찾을 수 없습니다" 오류
1. `assets/{project_name}_button.png` 파일 확인
2. 필요시 `--setup`으로 재캡처
3. 프로젝트명이 정확한지 확인

### "프로젝트 이름이 필요합니다" 오류
1. `config.json`에 `dev_project_name` 설정
2. 또는 `project_name` 파라미터 직접 전달
