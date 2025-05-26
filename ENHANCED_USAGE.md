# Enhanced Task Orchestrator 사용 가이드

## 주요 개선사항

### 1. 계속하기 버튼 처리 개선
- 초기 30초 대기 후 15초마다 확인 (이전: 3초마다)
- 계속하기 버튼 클릭 후에만 5초 간격으로 빠르게 확인
- 최대 5분까지 대기 (실제 Claude 응답 패턴에 맞춤)
- 불필요한 로그 감소

### 2. 동적 타임아웃 시스템 (신규)
- 작업 복잡도에 따라 대기 시간 자동 조정 (5분~30분)
- 화면 활동 감지로 작업 진행 중 타임아웃 연장
- 점진적 체크 인터벌로 효율성 향상

### 3. Task Master MCP 실제 활용
- Mock 데이터 대신 실제 Task Master MCP 도구 호출
- 구체적인 MCP 도구 사용 지침 포함
- 프로젝트 경로와 tasks 디렉토리 명시
- 복잡도 점수 기반 타임아웃 조정

### 4. 자동화된 태스크 처리
- Task Master의 next_task 기능을 활용한 연속 처리
- 태스크 완료 후 자동으로 다음 태스크 진행
- 최대 처리 태스크 수 설정 가능
- 연속 실패 시 재시도 메커니즘

## 필수 설치 패키지

```bash
pip install pyautogui pillow pyscreeze
```

## 설정 확인사항

1. **config.json** 확인:
   - `dev_project_path`: 개발 프로젝트 경로
   - `dev_project_name`: Claude 프로젝트 이름
   - `max_tasks_per_run`: 한 번에 처리할 최대 태스크 수 (기본값: 10)

2. **claude_desktop_config.json** 확인:
   - `dynamic_timeout_enabled`: 동적 타임아웃 활성화 (기본값: true)
   - `max_wait_for_complex_tasks_s`: 복잡한 작업 최대 대기 시간 (기본값: 1800초)
   - `activity_detection_enabled`: 화면 활동 감지 활성화 (기본값: true)
   - `progressive_interval_enabled`: 점진적 체크 간격 활성화 (기본값: true)

3. **Claude Desktop 설정**:
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

### 복잡도 분석 후 실행
```bash
# 1. 복잡도 분석 실행
python task_master_wrapper.py analyze-complexity

# 2. 복잡도 보고서 확인
python task_master_wrapper.py complexity-report

# 3. 자동 실행 (복잡도 점수 자동 적용)
python task_orchestrator_enhanced.py
```

### 수동으로 복잡도 지정
```bash
# 특정 복잡도로 단일 프롬프트 실행
python claude_desktop_automation.py --task-complexity 9 --input "complex_task.txt" --project-name myproject
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
- 복잡한 작업의 경우 최대 30분까지 대기 (복잡도에 따라 자동 조정)

### 20분 이상 걸리는 작업 타임아웃
- 작업 복잡도 점수가 올바르게 설정되었는지 확인
- `claude_desktop_config.json`에서 `max_wait_for_complex_tasks_s` 값 증가
- 활동 감지가 활성화되어 있는지 확인 (`activity_detection_enabled: true`)

### 활동 감지 오류
- PIL과 numpy가 설치되어 있는지 확인: `pip install pillow numpy`
- `activity_detection_threshold` 값 조정 (기본값: 0.02)

### Task Master MCP 연결 실패
- Claude Desktop에서 MCP 설정 확인
- 프로젝트 경로가 올바른지 확인
- Task Master가 해당 프로젝트에서 초기화되었는지 확인

## 로그 파일

- `logs/automation_orchestrator.log`: 메인 실행 로그
  - 태스크 처리 진행 상황
  - 복잡도 점수 및 타임아웃 설정
  - 연속 실패 및 재시도 정보
  
- `logs/claude_automation.log`: Claude Desktop 자동화 로그
  - 동적 타임아웃 정보
  - 활동 감지 상태
  - 진행률 표시 (% 및 남은 시간)
  
- `logs/orchestrator_progress.json`: 진행 상황 저장
  - 현재 태스크 및 복잡도
  - 완료/실패 태스크 목록
  
- `logs/task_progress_state.json`: Task Master 상태 저장
- `scripts/task-complexity-report.json`: 태스크 복잡도 분석 보고서
