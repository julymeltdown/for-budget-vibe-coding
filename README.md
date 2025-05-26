# AI 자동화 프로젝트 통합 솔루션

AI(Claude)를 활용하여 소프트웨어 개발 과정을 자동화하는 통합 솔루션입니다.

## 주요 기능

- **태스크 기반 개발**: tasks.json에 정의된 작업을 순차적으로 처리
- **Claude Desktop 자동화**: GUI 자동화를 통한 코드 생성
- **자동 테스트 실행**: 생성된 코드의 테스트 실행 및 실패 시 자동 수정
- **다양한 프로젝트 타입 지원**: Gradle, Maven, Go, Python 등
- **코드 품질 검사**: 임시 코드, 주석 처리된 코드 등 감지
- **Git 통합**: 성공적인 작업 완료 시 자동 커밋
- **알림 시스템**: Slack/Telegram을 통한 진행 상황 알림

## 설치

### 1. 의존성 설치

```bash
# Python 3.11 이상 권장 (3.12도 지원)
python -m venv venv

# Windows
.\venv\Scripts\activate
# Unix/Linux/Mac
source venv/bin/activate

# pip 업그레이드
python -m pip install --upgrade pip setuptools wheel

# 패키지 설치
pip install -r requirements.txt
```

### 2. 버튼 이미지 설정 (최초 1회)

Claude Desktop이 실행된 상태에서:

```bash
python claude_desktop_automation.py --setup
```

## 사용법

### Task Master 명령어 사용 (권장)

```bash
# Windows
task-master.bat list              # 태스크 목록 보기
task-master.bat status            # 프로젝트 진행 상황
task-master.bat run               # 모든 태스크 실행
task-master.bat run --task task-1  # 특정 태스크만 실행

# Unix/Linux/Mac (실행 권한 필요: chmod +x task-master.sh)
./task-master.sh list
./task-master.sh status
./task-master.sh run
```

### 직접 실행

```bash
# 태스크 목록 및 상태 확인
python task_master_wrapper.py list
python task_master_wrapper.py list --details
python task_master_wrapper.py status

# 태스크 실행
python task_orchestrator.py
python task_orchestrator.py --task task-1
python task_orchestrator.py --task task-1 --subtask subtask-1-1

# 태스크 상태 초기화
python task_master_wrapper.py reset
python task_master_wrapper.py reset --task task-1
```

## 프로젝트 설정

### config.json

프로젝트 타입에 따라 적절한 설정을 사용하세요:

#### Gradle 프로젝트 (Java/Kotlin)

```json
{
  "project_type": "gradle",
  "src_dir": "src/main/java",
  "test_dir": "src/test/java",
  "test_runner_config": {
    "gradle": {
      "test_command": "./gradlew",
      "test_command_windows": "gradlew.bat",
      "test_args": ["test", "--info"]
    }
  }
}
```

#### Maven 프로젝트 (Java)

```json
{
  "project_type": "maven",
  "src_dir": "src/main/java",
  "test_dir": "src/test/java"
}
```

#### Go 프로젝트

```json
{
  "project_type": "golang",
  "src_dir": ".",
  "test_dir": ""
}
```

#### Python 프로젝트

```json
{
  "project_type": "python",
  "src_dir": "src",
  "test_dir": "tests"
}
```

### tasks.json

```json
{
  "tasks": [
    {
      "id": "task-1",
      "name": "사용자 인증 시스템",
      "description": "JWT 기반 인증 구현",
      "subtasks": [
        {
          "id": "subtask-1-1",
          "name": "User 엔티티 구현",
          "requirements": ["User 클래스 생성", "JPA 어노테이션 추가"],
          "test_requirements": ["User 생성 테스트", "Validation 테스트"]
        }
      ]
    }
  ]
}
```

## 프로젝트별 주의사항

### Gradle 프로젝트

1. `gradlew` (Unix) 또는 `gradlew.bat` (Windows)가 프로젝트 루트에 있어야 합니다.
2. 실행 권한 확인: `chmod +x gradlew` (Unix/Linux/Mac)

### Maven 프로젝트

1. Maven이 시스템에 설치되어 있고 PATH에 등록되어 있어야 합니다.
2. Windows: `mvn.cmd`, Unix: `mvn`

### Go 프로젝트

1. Go가 시스템에 설치되어 있어야 합니다.
2. `go.mod` 파일이 프로젝트 루트에 있어야 합니다.

## 문제 해결

### "테스트 명령을 찾을 수 없습니다" 오류

1. `config.json`의 `project_type`이 올바른지 확인
2. Gradle: `gradlew` 또는 `gradlew.bat` 파일 존재 확인
3. Maven: `mvn` 명령어가 PATH에 있는지 확인
4. 수동으로 테스트 명령어 지정:
   ```json
   "test_runner_config": {
     "custom": {
       "test_command": "your-test-command",
       "test_args": ["arg1", "arg2"]
     }
   }
   ```

### Claude Desktop 자동화 실패

1. Claude Desktop이 실행 중인지 확인
2. `--setup`으로 버튼 이미지 재설정
3. `assets/` 디렉토리에 버튼 이미지가 있는지 확인

### pip 설치 오류

Python 3.12 사용 시 numpy 호환성 문제가 있을 수 있습니다. requirements.txt의 버전을 확인하세요.

## 로그 확인

```bash
# 오케스트레이터 로그
tail -f logs/automation_orchestrator.log

# Claude 자동화 로그
tail -f logs/claude_automation.log

# 테스트 이력
cat logs/test_history.json
```