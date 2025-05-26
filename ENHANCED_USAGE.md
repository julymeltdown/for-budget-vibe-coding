# Enhanced Task Orchestrator 사용 가이드

## 주요 개선사항

### 1. 계속하기 버튼 처리 개선
- 초기 30초 대기 후 15초마다 확인 (이전: 3초마다)
- 계속하기 버튼 클릭 후에만 5초 간격으로 빠르게 확인
- 최대 5분까지 대기 (실제 Claude 응답 패턴에 맞춤)
- 불필요한 로그 감소

### 2. Task Master MCP 실제 활용
- Mock 데이터 대신 실제 Task Master MCP 도구 호출
- 구체적인 MCP 도구 사용 지침 포함
- 프로젝트 경로와 tasks 디렉토리 명시

### 3. 자동화된 태스크 처리
- Task Master의 next_task 기능을 활용한 연속 처리
- 태스크 완료 후 자동으로 다음 태스크 진행
- 최대 처리 태스크 수 설정 가능

## 필수 설치 패키지

```bash
pip install pyautogui pillow pyscreeze
```

## 설정 확인사항

1. **config.json** 확인:
   - `dev_project_path`: 개발 프로젝트 경로
   - `dev_project_name`: Claude 프로젝트 이름
   - `max_tasks_per_run`: 한 번에 처리할 최대 태스크 수 (기본값: 10)

2. **Claude Desktop 설정**:
   - Task Master MCP가 활성화되어 있어야 함
   - JetBrains MCP가 활성화되어 있어야 함
   - 해당 프로젝트가 Claude Projects에 등록되어 있어야 함

## 실행 방법

### 전체 자동 실행
```bash
python task_orchestrator_enhanced.py
```

### 진행 상황만 확인
```bash
python task_orchestrator_enhanced.py --check-progress
```

### 특정 태스크만 실행
```bash
python task_orchestrator_enhanced.py --task 1 --subtask 2
```

## 프롬프트 구조

### 1. 진행 상황 확인 프롬프트
- Task Master MCP 도구들을 순차적으로 호출
- initialize_project → get_tasks → next_task → complexity_report
- 구조화된 결과 요약 요청

### 2. 태스크 구현 프롬프트
- Task Master MCP와 JetBrains MCP 통합 사용
- 단계별 구현 가이드라인 제공
- 테스트 실행 및 상태 업데이트 포함

## 문제 해결

### PyAutoGUI 오류
```
ModuleNotFoundError: No module named 'pyscreeze'
```
해결: `pip install pillow pyscreeze`

### 계속하기 버튼을 찾을 수 없음
- Claude 응답이 짧은 경우 정상적인 동작
- 5분 동안 버튼이 나타나지 않으면 자동으로 다음 단계 진행

### Task Master MCP 연결 실패
- Claude Desktop에서 MCP 설정 확인
- 프로젝트 경로가 올바른지 확인
- Task Master가 해당 프로젝트에서 초기화되었는지 확인

## 로그 파일

- `logs/automation_orchestrator.log`: 메인 실행 로그
- `logs/claude_automation.log`: Claude Desktop 자동화 로그
- `logs/orchestrator_progress.json`: 진행 상황 저장
- `logs/task_progress_state.json`: Task Master 상태 저장
