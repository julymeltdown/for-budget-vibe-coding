# Claude Desktop 개발 자동화 시스템

Claude Desktop GUI와 Task Master MCP를 통합하여 소프트웨어 개발을 자동화하는 시스템입니다.

## 목차
- [개요](#개요)
- [주요 기능](#주요-기능)
- [설치](#설치)
- [초기 설정](#초기-설정)
- [사용법](#사용법)
- [설정 파일](#설정-파일)
- [문제 해결](#문제-해결)

## 개요

이 시스템은 Claude Desktop을 통해 개발 태스크를 자동으로 처리하고, 테스트 실행, 코드 품질 검사, Git 커밋까지 자동화합니다. Task Master MCP와 통합되어 있어 개발 진행 상황을 지속적으로 추적하고 관리할 수 있습니다.

### 시스템 구성
```
integrated_automation_solution/
├── task_orchestrator_enhanced.py    # 메인 자동화 실행
├── task_master_wrapper.py          # 태스크 관리 CLI
├── claude_desktop_automation.py    # GUI 자동화
├── task_master_mcp_client.py      # Task Master MCP 클라이언트
├── code_analyzer.py               # 코드 품질 분석
├── notification_manager.py        # 알림 시스템
├── config.json                   # 메인 설정
├── tasks.json                    # 태스크 정의
└── assets/                       # GUI 버튼 이미지
```

## 주요 기능

### 1. 자동화된 개발 워크플로우
- Claude Desktop GUI를 통한 코드 생성
- JetBrains MCP를 활용한 파일 읽기/쓰기
- 자동 테스트 실행 및 실패 시 수정
- 코드 품질 검사 (mock 감지, 주석 코드 감지)
- 성공 시 자동 Git 커밋

### 2. Task Master MCP 통합
- 현재 개발 진행 상황 자동 확인
- 태스크 및 서브태스크 관리
- 완료된 태스크 자동 건너뛰기

### 3. 진행 상황 추적
- 모든 작업 내역 영구 저장
- 프로그램 재시작 시 이전 상태 복원
- 상세한 실행 이력 관리

### 4. 유연한 실행 옵션
- 전체 태스크 실행
- 특정 태스크/서브태스크만 실행
- 진행 상황만 확인

## 설치

### 1. 요구사항
- Python 3.11 이상
- Claude Desktop 설치
- JetBrains IDE + MCP 플러그인 (개발 프로젝트용)

### 2. 의존성 설치
```bash
# 가상환경 생성 (권장)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# 패키지 설치
pip install -r requirements.txt
```

## 초기 설정

### 1. config.json 설정
```json
{
  "dev_project_path": "C:\\Users\\lhs\\Desktop\\dev\\kido",
  "dev_project_name": "kido",
  "src_dir": "src/main/java",
  "test_dir": "src/test/java",
  "task_definition_file": "tasks.json",
  "check_quality_after_tests": true,
  "auto_commit_after_subtask": true,
  "git_enabled": true,
  "project_type": "gradle"
}
```

### 2. Claude Desktop 버튼 이미지 캡처
```bash
python claude_desktop_automation.py --setup
```

다음 버튼들을 순서대로 캡처합니다:
1. **Continue 버튼**: Claude가 긴 응답을 생성할 때 나타나는 버튼
2. **Projects 버튼**: 왼쪽 상단의 Projects 메뉴 버튼
3. **Max length 메시지**: 대화가 너무 길 때 나타나는 메시지
4. **프로젝트 버튼**: 프로젝트명 입력 시 해당 프로젝트 버튼 (예: kido)

### 3. tasks.json 작성
```json
{
  "tasks": [
    {
      "id": "1",
      "name": "사용자 인증 시스템",
      "description": "JWT 기반 인증 구현",
      "status": "pending",
      "subtasks": [
        {
          "id": "1",
          "name": "User 엔티티 구현",
          "description": "사용자 정보 저장 모델",
          "status": "pending"
        }
      ]
    }
  ]
}
```

### 4. 개발 프로젝트 태스크 파일 준비
개발 프로젝트의 `tasks` 폴더에 태스크별 상세 설명 파일 생성:
```
C:\Users\lhs\Desktop\dev\kido\tasks\
├── task_1.txt          # Task 1의 상세 요구사항
├── subtask_1_1.txt     # Subtask 1-1의 구현 내용
└── subtask_1_2.txt     # Subtask 1-2의 구현 내용
```

## 사용법

### 1. 전체 태스크 자동 실행
```bash
python task_orchestrator_enhanced.py
```

실행 흐름:
1. Task Master MCP를 통해 현재 진행 상황 확인
2. 미완료 태스크부터 순차적으로 처리
3. 각 태스크마다:
   - Claude Desktop에서 새 채팅 생성 (Projects → 프로젝트명)
   - JetBrains MCP로 태스크 파일 읽기
   - 코드 구현
   - 테스트 실행
   - 성공 시 Git 커밋

### 2. 진행 상황 확인
```bash
# 현재 진행 상황만 확인
python task_orchestrator_enhanced.py --check-progress

# 태스크 목록 및 상태 보기
python task_master_wrapper.py status
```

### 3. 특정 태스크 실행
```bash
# 특정 태스크만 실행
python task_orchestrator_enhanced.py --task 1

# 특정 서브태스크만 실행
python task_orchestrator_enhanced.py --task 1 --subtask 2
```

### 4. 태스크 관리 명령어
```bash
# 태스크 목록 보기
python task_master_wrapper.py list

# 상세 정보 포함
python task_master_wrapper.py list --details

# 대기중인 태스크만 보기
python task_master_wrapper.py list --status pending

# 태스크 상태 초기화
python task_master_wrapper.py reset --task 1
```

## 설정 파일

### config.json (메인 설정)
| 설정 | 설명 | 예시 |
|------|------|------|
| `dev_project_path` | 개발 프로젝트 경로 | `"C:\\dev\\myproject"` |
| `dev_project_name` | Claude 프로젝트명 | `"myproject"` |
| `project_type` | 프로젝트 타입 | `"gradle"`, `"maven"`, `"python"` |
| `check_quality_after_tests` | 테스트 후 코드 품질 검사 | `true` |
| `auto_commit_after_subtask` | 서브태스크 완료 시 자동 커밋 | `true` |
| `git_enabled` | Git 기능 활성화 | `true` |

### claude_desktop_config.json (GUI 설정)
```json
{
  "window_title": "Claude",
  "confidence_threshold": 0.7,  // 이미지 매칭 신뢰도 (0.5~1.0)
  "max_retries": 3,            // 이미지 찾기 재시도 횟수
  "assets_dir": "assets"       // 버튼 이미지 폴더
}
```

### notification_config.json (알림 설정)
```json
{
  "enabled": true,
  "slack": {
    "enabled": true,
    "webhook_url": "https://hooks.slack.com/services/...",
    "channel": "#dev-automation"
  }
}
```

## 진행 상황 파일

### logs/orchestrator_progress.json
```json
{
  "current_task": {"id": "1", "started_at": "2024-12-19T10:00:00"},
  "current_subtask": {"id": "2", "started_at": "2024-12-19T10:30:00"},
  "completed_tasks": [
    {"id": "1", "subtask_id": "1", "completed_at": "2024-12-19T10:25:00"}
  ],
  "failed_tasks": [],
  "task_history": [...]
}
```

### logs/task_progress_state.json
Task Master MCP에서 받은 진행 상황 정보 저장

## 문제 해결

### 1. "Projects 버튼을 찾을 수 없습니다"
- `assets/projects_button.png` 파일 확인
- 화면 해상도 변경 시 `--setup`으로 재캡처
- `confidence_threshold` 값 낮추기 (기본 0.7 → 0.6)

### 2. "프로젝트 버튼을 찾을 수 없습니다"
- `assets/{project_name}_button.png` 파일 확인
- 프로젝트명이 config.json의 `dev_project_name`과 일치하는지 확인

### 3. "테스트 실패"
- 개발 프로젝트의 테스트 명령어 확인
- Gradle: `gradlew.bat test` (Windows)
- Maven: `mvn test`
- Python: `pytest`

### 4. "Task Master MCP 응답 없음"
- JetBrains IDE에서 MCP 플러그인 활성화 확인
- .cursor/mcp.json에 Task Master 설정 확인

### 5. 진행 상황 초기화
```bash
# 특정 태스크 초기화
python task_master_wrapper.py reset --task 1

# 전체 초기화
python task_master_wrapper.py reset
```

## 로그 확인

```bash
# 메인 실행 로그
tail -f logs/automation_orchestrator.log

# Claude 자동화 로그
tail -f logs/claude_automation.log

# 테스트 실행 이력
cat logs/test_history.json
```

## 팁

1. **버튼 이미지 백업**: `assets` 폴더를 백업해두면 재설정 시 편리
2. **부분 실행**: 특정 태스크만 실행하여 디버깅
3. **수동 개입**: 필요시 Claude Desktop에서 직접 수정 후 계속 진행
4. **진행 상황 편집**: JSON 파일을 직접 편집하여 상태 조정 가능

## 주의사항

- Claude Desktop이 항상 실행 중이어야 함
- 화면 해상도 변경 시 버튼 이미지 재캡처 필요
- 긴 태스크는 Claude의 대화 길이 제한에 걸릴 수 있음
- Git 커밋 전 변경사항 확인 권장

## 지원

문제 발생 시:
1. 로그 파일 확인
2. 설정 파일 검증 (`python validate_setup.py`)
3. 버튼 이미지 재설정
4. 진행 상황 초기화
