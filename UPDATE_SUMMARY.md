# 자동화 시스템 사용 가이드

## 빠른 시작

### 1. 초기 설정

#### 1.1 config.json 설정
```json
{
  "dev_project_path": "C:\\Users\\lhs\\Desktop\\dev\\kido",
  "dev_project_name": "kido",
  "task_files_dir": "tasks"
}
```

#### 1.2 버튼 이미지 준비
다음 중 하나 선택:

**옵션 A: 수동 캡처 (권장)**
1. Claude Desktop 열기
2. Win + Shift + S로 각 버튼 캡처
3. assets 폴더에 저장:
   - `continue_button.png`
   - `projects_button.png`
   - `max_length_message.png`
   - `kido_button.png` (프로젝트명)

**옵션 B: 자동 캡처**
```bash
python claude_desktop_automation.py --setup
```

자세한 캡처 방법은 `assets/CAPTURE_GUIDE.md` 참조

### 2. Task 파일 준비
개발 프로젝트의 tasks 폴더에 파일 생성:
```
C:\Users\lhs\Desktop\dev\kido\tasks\
├── task_1.txt          # Task 1의 내용
├── subtask_1_1.txt     # Task 1의 Subtask 1 내용
├── subtask_1_2.txt     # Task 1의 Subtask 2 내용
└── task_2.txt          # Task 2의 내용
```

### 3. 실행
```bash
# 전체 실행
python task_orchestrator.py

# 특정 태스크만
python task_orchestrator.py --task 1

# 특정 서브태스크만
python task_orchestrator.py --task 1 --subtask 1
```

## 주요 특징

### 자동 처리 흐름
1. Task 파일 경로를 Claude에 전달
2. Claude가 JetBrains MCP로 파일 읽기
3. 코드 구현
4. 테스트 실행
5. Git 커밋

### Max Length 처리
- 자동으로 Max length 메시지 감지
- Projects → 프로젝트 버튼 클릭으로 새 채팅 시작
- 대화 연속성 유지

### 이미지 관리
- 한 번 캡처한 이미지 재사용
- 환경별 이미지 파일 분리 (.gitignore)
- UI 변경 시에만 재캡처 필요

## 문제 해결

### "이미지 파일을 찾을 수 없습니다" 오류
1. assets 폴더 확인
2. 필요한 PNG 파일이 있는지 확인
3. 없으면 수동 캡처 또는 --setup 실행

### "Projects 버튼을 찾을 수 없습니다" 오류
1. Max length 상황에서 UI 확인
2. Projects 버튼 위치 재캡처
3. confidence_threshold 조정 (기본: 0.7)

### "Task 파일을 찾을 수 없습니다" 오류
1. dev_project_path 설정 확인
2. task 파일 경로 및 이름 확인
3. 파일 접근 권한 확인

## 고급 설정

### confidence_threshold 조정
```json
{
  "confidence_threshold": 0.6  // 낮추면 더 관대하게 매칭
}
```

### 재시도 횟수 조정
```json
{
  "max_retries": 5,  // 이미지 찾기 재시도
  "max_subtask_retries": 3  // 테스트 실패 시 재시도
}
```

### 디버그 모드
```python
# task_orchestrator.py 상단
logging.basicConfig(level=logging.DEBUG)
```