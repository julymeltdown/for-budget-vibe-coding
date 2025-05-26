# 빠른 시작 가이드

## 1. 설치 (5분)

```bash
# 1. 가상환경 생성 및 활성화
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# 2. 패키지 설치
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

## 2. Gradle 프로젝트 설정 (2분)

```bash
# 1. config.json을 Gradle용으로 복사
copy config_gradle_example.json config.json  # Windows
# cp config_gradle_example.json config.json  # Mac/Linux

# 2. 프로젝트 경로 확인 (필요시 수정)
# config.json 열어서 project_dir이 올바른지 확인
```

## 3. Claude Desktop 설정 (3분)

```bash
# 1. Claude Desktop 실행

# 2. 버튼 이미지 캡처
python claude_desktop_automation.py --setup
# '계속하기' 버튼과 '새 채팅' 버튼을 각각 캡처
```

## 4. 태스크 실행

```bash
# 프로젝트 상태 확인
task-master.bat status  # Windows
# ./task-master.sh status  # Mac/Linux

# 태스크 목록 보기
task-master.bat list

# 태스크 실행
task-master.bat run
```

## 일반적인 문제 해결

### gradlew를 찾을 수 없음
```bash
# Windows에서 gradlew.bat이 있는지 확인
dir gradlew.bat

# 없다면 gradle wrapper 생성
gradle wrapper
```

### Claude Desktop 자동화 실패
- Claude Desktop이 실행 중인지 확인
- 화면 해상도가 변경되지 않았는지 확인
- `python claude_desktop_automation.py --setup` 재실행

### 테스트 실패 시
```bash
# 로그 확인
type logs\automation_orchestrator.log  # Windows
# cat logs/automation_orchestrator.log  # Mac/Linux

# 특정 태스크만 재실행
task-master.bat run --task task-1
```