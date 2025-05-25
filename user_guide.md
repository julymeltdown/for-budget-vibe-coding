# 통합 자동화 솔루션 사용자 가이드

## 목차
1. [소개](#1-소개)
2. [설치 및 설정](#2-설치-및-설정)
3. [주요 기능 및 사용법](#3-주요-기능-및-사용법)
4. [태스크 정의 작성 방법](#4-태스크-정의-작성-방법)
5. [실전 활용 시나리오](#5-실전-활용-시나리오)
6. [문제 해결 가이드](#6-문제-해결-가이드)
7. [FAQ](#7-faq)
8. [부록](#8-부록)

## 1. 소개

### 1.1 통합 자동화 솔루션이란?

통합 자동화 솔루션은 프로젝트 MVP 개발을 자동화하기 위한 종합 시스템입니다. 이 솔루션은 다음과 같은 주요 구성 요소로 이루어져 있습니다:

- **Claude Desktop GUI 자동화**: 질문 입력, 계속하기 버튼 클릭, 새 채팅 생성 등 자동화
- **테스트 자동화**: 유닛 테스트 실행 및 결과 모니터링, 실패 시 자동 수정 시도
- **코드 품질 감시**: 인공지능의 임시처리(주석, mock 등) 감지 및 품질 분석
- **태스크 오케스트레이션**: 테스트 통과 시 다음 태스크 자동 실행
- **알림 시스템**: 실패 시 슬랙/텔레그램 알림 발송

이 솔루션은 백엔드(Java SpringBoot/Golang Echo)와 프론트엔드(Next.js/React+Vite) 개발을 지원하며, 헥사고날 아키텍처와 JWT 인증 구현을 검증합니다.

### 1.2 주요 특징

- **최소 GUI 자동화**: Claude Desktop의 입력 제한, Continue 버튼, 컨텍스트 윈도우 초과 등의 상황에서만 GUI 자동화 활용
- **테스트 중심 개발**: 유닛 테스트가 모두 성공할 때까지 수정을 반복
- **코드 품질 보장**: 임시처리 감지 및 헥사고날 아키텍처 검증
- **Git 통합**: 서브태스크별 자동 커밋 및 태스크 완료 시 AI 코드 리뷰
- **알림 시스템**: 오류 발생 시 즉시 알림

## 2. 설치 및 설정

### 2.1 시스템 요구사항

- **운영체제**: Windows 10/11, macOS, Linux (Ubuntu 20.04 이상 권장)
- **Python**: 3.9 이상
- **GUI 환경**: X11 디스플레이 서버 (Linux의 경우)
- **필수 소프트웨어**:
  - Claude Desktop
  - Git
  - 백엔드: Java 17+ 또는 Go 1.18+
  - 프론트엔드: Node.js 16+

### 2.2 설치 방법

```bash
# 1. 저장소 클론
git clone https://github.com/your-username/integrated-automation.git
cd integrated-automation

# 2. 가상 환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 필요 패키지 설치
pip install -r requirements.txt
```

### 2.3 초기 설정

#### 2.3.1 설정 파일 생성

`config.json` 파일을 프로젝트 루트 디렉토리에 생성합니다:

```json
{
  "project_dir": "/path/to/your/project",
  "src_dir": "/path/to/your/project/src",
  "test_dir": "/path/to/your/project/tests",
  "task_definition_file": "tasks.json",
  "max_subtask_failures": 5,
  "check_quality_after_tests": true,
  "auto_commit_after_subtask": true,
  "git_enabled": true,
  "git_repo": "/path/to/your/project",
  "claude_desktop": {
    "enabled": true,
    "config_path": "claude_desktop_config.json"
  },
  "notification": {
    "enabled": true,
    "config_path": "notification_config.json"
  }
}
```

#### 2.3.2 Claude Desktop 설정

`claude_desktop_config.json` 파일을 생성합니다:

```json
{
  "window_title": "Claude",
  "input_delay": 0.5,
  "screenshot_delay": 1.0,
  "max_retries": 3,
  "confidence_threshold": 0.7,
  "continue_button_text": "Continue",
  "new_chat_button_text": "New chat",
  "assets_dir": "assets",
  "continue_button_image": "continue_button.png",
  "new_chat_button_image": "new_chat_button.png"
}
```

#### 2.3.3 알림 설정

`notification_config.json` 파일을 생성합니다:

```json
{
  "enabled": true,
  "slack": {
    "enabled": true,
    "webhook_url": "https://hooks.slack.com/services/YOUR_WEBHOOK_URL",
    "channel": "#automation",
    "username": "Automation Bot"
  },
  "telegram": {
    "enabled": true,
    "bot_token": "YOUR_BOT_TOKEN",
    "chat_id": "YOUR_CHAT_ID"
  },
  "notification_cooldown": 300
}
```

#### 2.3.4 버튼 이미지 설정

GUI 자동화를 위해 버튼 이미지를 설정합니다:

```bash
python gui_test_automation.py --setup
```

이 명령을 실행하면 Claude Desktop의 '계속하기' 버튼과 '새 채팅' 버튼을 캡처하여 저장합니다. 화면에 표시되는 지시에 따라 각 버튼의 위치를 지정해주세요.

## 3. 주요 기능 및 사용법

### 3.1 태스크 오케스트레이션

태스크 오케스트레이터는 전체 자동화 프로세스를 관리합니다:

```bash
# 모든 태스크 실행
python task_orchestrator.py --config config.json

# 특정 태스크만 실행
python task_orchestrator.py --config config.json --task task-1

# 특정 서브태스크만 실행
python task_orchestrator.py --config config.json --task task-1 --subtask subtask-1-1
```

### 3.2 Claude Desktop 자동화

Claude Desktop 자동화는 다음 기능을 제공합니다:

```bash
# 초기 설정 (버튼 이미지 캡처)
python gui_test_automation.py --setup

# 프롬프트 전송
python gui_test_automation.py --prompt "여기에 프롬프트 내용을 입력하세요"

# 테스트 실행
python gui_test_automation.py --test --task-id task-1 --subtask-id subtask-1-1
```

### 3.3 코드 품질 분석

코드 분석기는 다음 기능을 제공합니다:

```bash
# 코드 분석 실행
python code_analyzer.py /path/to/your/src

# 특정 디렉토리 분석
python code_analyzer.py /path/to/specific/directory
```

### 3.4 알림 시스템

알림 관리자는 다음 기능을 제공합니다:

```bash
# 테스트 알림 전송
python notification_manager.py
```

## 4. 태스크 정의 작성 방법

### 4.1 태스크 정의 파일 구조

태스크 정의 파일(`tasks.json`)은 다음과 같은 구조를 가집니다:

```json
[
  {
    "id": "task-1",
    "name": "사용자 인증 기능 구현",
    "description": "JWT 기반 사용자 인증 시스템 구현",
    "status": "pending",
    "auth": true,
    "subtasks": [
      {
        "id": "subtask-1-1",
        "name": "사용자 도메인 모델 구현",
        "description": "사용자 도메인 모델 및 리포지토리 인터페이스 구현",
        "status": "pending",
        "requirements": [
          "사용자 엔티티 정의",
          "리포지토리 인터페이스 정의"
        ],
        "test_requirements": [
          "도메인 모델 단위 테스트"
        ]
      },
      {
        "id": "subtask-1-2",
        "name": "JWT 서비스 구현",
        "description": "액세스 토큰 및 리프레시 토큰 생성/검증 서비스 구현",
        "status": "pending",
        "requirements": [
          "토큰 생성 기능",
          "토큰 검증 기능",
          "리프레시 토큰 처리"
        ],
        "test_requirements": [
          "토큰 생성/검증 단위 테스트"
        ],
        "critical": true
      }
    ]
  }
]
```

### 4.2 태스크 속성 설명

- **id**: 태스크의 고유 식별자
- **name**: 태스크의 이름
- **description**: 태스크에 대한 상세 설명
- **status**: 태스크의 상태 (pending, in_progress, completed, failed)
- **auth**: JWT 인증 구현 여부 (true/false)
- **subtasks**: 서브태스크 목록

### 4.3 서브태스크 속성 설명

- **id**: 서브태스크의 고유 식별자
- **name**: 서브태스크의 이름
- **description**: 서브태스크에 대한 상세 설명
- **status**: 서브태스크의 상태 (pending, in_progress, completed, failed)
- **requirements**: 서브태스크의 요구사항 목록
- **test_requirements**: 서브태스크의 테스트 요구사항 목록
- **critical**: 중요 서브태스크 여부 (실패 시 태스크 중단)

### 4.4 태스크 정의 작성 팁

1. **구체적인 설명**: 태스크와 서브태스크의 설명을 최대한 구체적으로 작성하세요.
2. **명확한 요구사항**: 각 서브태스크의 요구사항을 명확하게 정의하세요.
3. **테스트 요구사항**: 테스트 요구사항을 상세히 작성하여 품질을 보장하세요.
4. **의존성 고려**: 서브태스크 간의 의존성을 고려하여 순서를 정하세요.
5. **중요 서브태스크 표시**: 중요한 서브태스크는 `critical` 속성을 `true`로 설정하세요.

## 5. 실전 활용 시나리오

### 5.1 백엔드 API 개발 자동화

#### 5.1.1 태스크 정의 예시

```json
{
  "id": "backend-api",
  "name": "RESTful API 개발",
  "description": "사용자 관리 및 인증을 위한 RESTful API 개발",
  "status": "pending",
  "auth": true,
  "subtasks": [
    {
      "id": "backend-api-1",
      "name": "사용자 도메인 모델 구현",
      "description": "사용자 도메인 모델 및 리포지토리 인터페이스 구현",
      "status": "pending",
      "requirements": [
        "사용자 엔티티 정의 (id, username, email, password)",
        "리포지토리 인터페이스 정의 (findById, findByUsername, save, delete)"
      ],
      "test_requirements": [
        "도메인 모델 유효성 검사 테스트",
        "리포지토리 인터페이스 테스트"
      ]
    },
    {
      "id": "backend-api-2",
      "name": "JWT 인증 서비스 구현",
      "description": "JWT 기반 인증 서비스 구현",
      "status": "pending",
      "requirements": [
        "액세스 토큰 생성 및 검증",
        "리프레시 토큰 생성 및 검증",
        "토큰 만료 처리"
      ],
      "test_requirements": [
        "토큰 생성 테스트",
        "토큰 검증 테스트",
        "만료된 토큰 처리 테스트"
      ],
      "critical": true
    },
    {
      "id": "backend-api-3",
      "name": "사용자 API 엔드포인트 구현",
      "description": "사용자 관리를 위한 API 엔드포인트 구현",
      "status": "pending",
      "requirements": [
        "사용자 등록 (POST /api/users)",
        "사용자 로그인 (POST /api/auth/login)",
        "사용자 정보 조회 (GET /api/users/{id})",
        "사용자 정보 수정 (PUT /api/users/{id})",
        "사용자 삭제 (DELETE /api/users/{id})"
      ],
      "test_requirements": [
        "각 엔드포인트에 대한 통합 테스트",
        "인증 및 권한 검사 테스트"
      ]
    }
  ]
}
```

#### 5.1.2 실행 방법

```bash
# 백엔드 API 태스크 실행
python task_orchestrator.py --config config.json --task backend-api
```

### 5.2 프론트엔드 개발 자동화

#### 5.2.1 태스크 정의 예시

```json
{
  "id": "frontend-app",
  "name": "React 프론트엔드 개발",
  "description": "사용자 인터페이스 및 API 연동 구현",
  "status": "pending",
  "subtasks": [
    {
      "id": "frontend-app-1",
      "name": "컴포넌트 구조 설계",
      "description": "React 컴포넌트 구조 설계 및 기본 레이아웃 구현",
      "status": "pending",
      "requirements": [
        "페이지 레이아웃 컴포넌트 구현",
        "네비게이션 컴포넌트 구현",
        "라우팅 설정"
      ],
      "test_requirements": [
        "컴포넌트 렌더링 테스트",
        "라우팅 테스트"
      ]
    },
    {
      "id": "frontend-app-2",
      "name": "인증 기능 구현",
      "description": "로그인, 회원가입, 로그아웃 기능 구현",
      "status": "pending",
      "requirements": [
        "로그인 폼 구현",
        "회원가입 폼 구현",
        "JWT 토큰 저장 및 관리",
        "인증 상태 관리"
      ],
      "test_requirements": [
        "폼 유효성 검사 테스트",
        "인증 상태 관리 테스트",
        "API 연동 테스트"
      ],
      "critical": true
    },
    {
      "id": "frontend-app-3",
      "name": "사용자 프로필 페이지 구현",
      "description": "사용자 프로필 조회 및 수정 기능 구현",
      "status": "pending",
      "requirements": [
        "프로필 정보 표시",
        "프로필 수정 폼 구현",
        "API 연동"
      ],
      "test_requirements": [
        "컴포넌트 렌더링 테스트",
        "폼 유효성 검사 테스트",
        "API 연동 테스트"
      ]
    }
  ]
}
```

#### 5.2.2 실행 방법

```bash
# 프론트엔드 태스크 실행
python task_orchestrator.py --config config.json --task frontend-app
```

### 5.3 통합 테스트 자동화

#### 5.3.1 태스크 정의 예시

```json
{
  "id": "integration-tests",
  "name": "통합 테스트 구현",
  "description": "백엔드 API와 프론트엔드 통합 테스트 구현",
  "status": "pending",
  "subtasks": [
    {
      "id": "integration-tests-1",
      "name": "API 통합 테스트 구현",
      "description": "백엔드 API 통합 테스트 구현",
      "status": "pending",
      "requirements": [
        "사용자 등록 및 로그인 테스트",
        "인증된 API 요청 테스트",
        "오류 처리 테스트"
      ],
      "test_requirements": [
        "테스트 케이스 성공 여부 확인"
      ]
    },
    {
      "id": "integration-tests-2",
      "name": "E2E 테스트 구현",
      "description": "프론트엔드 E2E 테스트 구현",
      "status": "pending",
      "requirements": [
        "사용자 등록 및 로그인 시나리오",
        "프로필 조회 및 수정 시나리오",
        "오류 처리 시나리오"
      ],
      "test_requirements": [
        "테스트 케이스 성공 여부 확인"
      ]
    }
  ]
}
```

#### 5.3.2 실행 방법

```bash
# 통합 테스트 태스크 실행
python task_orchestrator.py --config config.json --task integration-tests
```

## 6. 문제 해결 가이드

### 6.1 GUI 자동화 문제

#### 6.1.1 버튼 인식 실패

**증상**: '계속하기' 버튼이나 '새 채팅' 버튼을 인식하지 못함

**해결 방법**:
1. 버튼 이미지를 다시 캡처: `python gui_test_automation.py --setup`
2. 신뢰도 임계값 조정: `claude_desktop_config.json`의 `confidence_threshold` 값을 낮춤 (예: 0.7 → 0.6)
3. 화면 해상도 및 테마 확인: Claude Desktop의 테마가 변경되면 버튼 모양이 달라질 수 있음

#### 6.1.2 텍스트 입력 문제

**증상**: 텍스트가 입력되지 않거나 일부만 입력됨

**해결 방법**:
1. 입력 지연 시간 조정: `claude_desktop_config.json`의 `input_delay` 값을 높임 (예: 0.5 → 1.0)
2. Claude Desktop 창이 활성화되어 있는지 확인
3. 키보드 레이아웃 확인: 영어 키보드 레이아웃으로 설정되어 있는지 확인

### 6.2 테스트 자동화 문제

#### 6.2.1 테스트 실패 반복

**증상**: 동일한 테스트가 계속 실패함

**해결 방법**:
1. 테스트 로그 확인: 실패 원인 분석
2. 최대 재시도 횟수 조정: `config.json`의 `max_subtask_failures` 값을 높임
3. 테스트 요구사항 검토: 테스트 요구사항이 명확한지 확인

#### 6.2.2 테스트 환경 문제

**증상**: 테스트 환경 설정 오류

**해결 방법**:
1. 필요한 패키지 설치 확인: `pip install -r requirements.txt`
2. 테스트 디렉토리 경로 확인: `config.json`의 `test_dir` 값이 올바른지 확인
3. 테스트 명령 확인: `TestRunner` 클래스의 `test_command` 및 `test_args` 설정 확인

### 6.3 알림 시스템 문제

#### 6.3.1 알림 전송 실패

**증상**: Slack 또는 Telegram 알림이 전송되지 않음

**해결 방법**:
1. 웹훅 URL 또는 봇 토큰 확인: `notification_config.json` 설정 확인
2. 네트워크 연결 확인: 인터넷 연결 상태 확인
3. 알림 쿨다운 확인: `notification_cooldown` 값이 너무 높지 않은지 확인

#### 6.3.2 중복 알림

**증상**: 동일한 알림이 여러 번 전송됨

**해결 방법**:
1. 알림 쿨다운 조정: `notification_config.json`의 `notification_cooldown` 값을 높임
2. 알림 키 확인: 알림 키 생성 로직 검토

### 6.4 오케스트레이션 문제

#### 6.4.1 태스크 정의 로드 실패

**증상**: 태스크 정의 파일을 로드하지 못함

**해결 방법**:
1. 파일 경로 확인: `config.json`의 `task_definition_file` 값이 올바른지 확인
2. JSON 형식 확인: 태스크 정의 파일이 유효한 JSON 형식인지 확인
3. 파일 권한 확인: 파일 읽기 권한이 있는지 확인

#### 6.4.2 Git 커밋 실패

**증상**: Git 커밋이 실패함

**해결 방법**:
1. Git 설정 확인: Git이 설치되어 있고 저장소가 초기화되어 있는지 확인
2. Git 사용자 설정 확인: Git 사용자 이름과 이메일이 설정되어 있는지 확인
3. 저장소 경로 확인: `config.json`의 `git_repo` 값이 올바른지 확인

## 7. FAQ

### 7.1 일반적인 질문

#### Q: 이 솔루션은 어떤 프로젝트에 적합한가요?
A: 이 솔루션은 헥사고날 아키텍처를 기반으로 하는 백엔드(Java SpringBoot/Golang Echo) 및 프론트엔드(Next.js/React+Vite) 프로젝트에 적합합니다. 특히 MVP 개발 단계에서 반복적인 작업을 자동화하고 코드 품질을 유지하는 데 도움이 됩니다.

#### Q: 다른 AI 모델과 함께 사용할 수 있나요?
A: 현재는 Claude Desktop에 최적화되어 있지만, 코드를 수정하여 다른 AI 모델(예: ChatGPT)과 함께 사용할 수 있습니다. GUI 자동화 부분을 해당 모델의 인터페이스에 맞게 조정해야 합니다.

#### Q: 얼마나 많은 리소스가 필요한가요?
A: 기본적인 사용에는 일반적인 개발 PC 사양으로 충분합니다. GUI 자동화를 위해 그래픽 환경이 필요하며, 대규모 프로젝트의 경우 더 많은 메모리와 CPU 리소스가 필요할 수 있습니다.

### 7.2 설정 관련 질문

#### Q: Claude Desktop이 없어도 사용할 수 있나요?
A: Claude Desktop 자동화 기능을 비활성화하고 JetBrains MCP만 사용할 수 있습니다. `config.json`에서 `claude_desktop.enabled`를 `false`로 설정하세요.

#### Q: 알림 시스템을 설정하는 방법은 무엇인가요?
A: Slack의 경우 Incoming Webhook URL을, Telegram의 경우 봇 토큰과 채팅 ID를 `notification_config.json`에 설정해야 합니다. 자세한 방법은 [2.3.3 알림 설정](#233-알림-설정) 섹션을 참조하세요.

#### Q: 여러 프로젝트에서 사용할 수 있나요?
A: 네, 각 프로젝트마다 별도의 설정 파일을 만들고 `--config` 옵션으로 지정하여 사용할 수 있습니다.

### 7.3 사용 관련 질문

#### Q: 테스트가 계속 실패하면 어떻게 되나요?
A: 설정된 최대 재시도 횟수(`max_subtask_failures`)를 초과하면 해당 서브태스크는 실패로 표시되고, 알림이 발송됩니다. 중요 서브태스크(`critical: true`)가 실패하면 전체 태스크가 중단됩니다.

#### Q: 코드 품질 문제가 감지되면 어떻게 되나요?
A: 모의(mock) 처리나 주석 처리된 코드가 감지되면 알림이 발송됩니다. 설정에 따라 태스크를 계속 진행하거나 중단할 수 있습니다.

#### Q: 자동 커밋을 비활성화할 수 있나요?
A: 네, `config.json`에서 `auto_commit_after_subtask`를 `false`로 설정하거나 `git_enabled`를 `false`로 설정하여 Git 기능 전체를 비활성화할 수 있습니다.

## 8. 부록

### 8.1 설정 파일 참조

#### 8.1.1 config.json

| 속성 | 설명 | 기본값 |
|------|------|--------|
| project_dir | 프로젝트 디렉토리 경로 | "." |
| src_dir | 소스 코드 디렉토리 경로 | "src" |
| test_dir | 테스트 디렉토리 경로 | "tests" |
| task_definition_file | 태스크 정의 파일 경로 | "tasks.json" |
| max_subtask_failures | 최대 서브태스크 실패 횟수 | 5 |
| check_quality_after_tests | 테스트 후 코드 품질 검사 여부 | true |
| auto_commit_after_subtask | 서브태스크 완료 후 자동 커밋 여부 | true |
| git_enabled | Git 기능 활성화 여부 | true |
| git_repo | Git 저장소 경로 | "." |
| claude_desktop.enabled | Claude Desktop 자동화 활성화 여부 | true |
| claude_desktop.config_path | Claude Desktop 설정 파일 경로 | "claude_desktop_config.json" |
| notification.enabled | 알림 시스템 활성화 여부 | true |
| notification.config_path | 알림 설정 파일 경로 | "notification_config.json" |

#### 8.1.2 claude_desktop_config.json

| 속성 | 설명 | 기본값 |
|------|------|--------|
| window_title | Claude Desktop 창 제목 | "Claude" |
| input_delay | 입력 지연 시간(초) | 0.5 |
| screenshot_delay | 스크린샷 지연 시간(초) | 1.0 |
| max_retries | 최대 재시도 횟수 | 3 |
| confidence_threshold | 이미지 인식 신뢰도 임계값 | 0.7 |
| continue_button_text | '계속하기' 버튼 텍스트 | "Continue" |
| new_chat_button_text | '새 채팅' 버튼 텍스트 | "New chat" |
| assets_dir | 에셋 디렉토리 경로 | "assets" |
| continue_button_image | '계속하기' 버튼 이미지 파일명 | "continue_button.png" |
| new_chat_button_image | '새 채팅' 버튼 이미지 파일명 | "new_chat_button.png" |

#### 8.1.3 notification_config.json

| 속성 | 설명 | 기본값 |
|------|------|--------|
| enabled | 알림 시스템 활성화 여부 | true |
| slack.enabled | Slack 알림 활성화 여부 | false |
| slack.webhook_url | Slack Webhook URL | "" |
| slack.channel | Slack 채널명 | "" |
| slack.username | Slack 봇 사용자명 | "Automation Bot" |
| telegram.enabled | Telegram 알림 활성화 여부 | false |
| telegram.bot_token | Telegram 봇 토큰 | "" |
| telegram.chat_id | Telegram 채팅 ID | "" |
| notification_cooldown | 알림 쿨다운 시간(초) | 300 |

### 8.2 명령어 참조

| 명령어 | 설명 |
|--------|------|
| `python task_orchestrator.py --config config.json` | 모든 태스크 실행 |
| `python task_orchestrator.py --config config.json --task task-id` | 특정 태스크 실행 |
| `python task_orchestrator.py --config config.json --task task-id --subtask subtask-id` | 특정 서브태스크 실행 |
| `python gui_test_automation.py --setup` | GUI 자동화 초기 설정 |
| `python gui_test_automation.py --prompt "프롬프트 내용"` | Claude Desktop에 프롬프트 전송 |
| `python gui_test_automation.py --test --task-id task-id --subtask-id subtask-id` | 테스트 실행 |
| `python code_analyzer.py /path/to/src` | 코드 분석 실행 |
| `python notification_manager.py` | 테스트 알림 전송 |

### 8.3 디렉토리 구조

```
integrated-automation/
├── assets/                      # 이미지 에셋 디렉토리
│   ├── continue_button.png      # '계속하기' 버튼 이미지
│   └── new_chat_button.png      # '새 채팅' 버튼 이미지
├── venv/                        # 가상 환경 (자동 생성)
├── automation.log               # 로그 파일 (자동 생성)
├── code_analyzer.py             # 코드 분석기
├── config.json                  # 메인 설정 파일
├── claude_desktop_config.json   # Claude Desktop 설정 파일
├── gui_test_automation.py       # GUI 자동화 모듈
├── notification_config.json     # 알림 설정 파일
├── notification_manager.py      # 알림 관리자
├── requirements.txt             # 필요 패키지 목록
├── task_orchestrator.py         # 태스크 오케스트레이터
└── tasks.json                   # 태스크 정의 파일
```

### 8.4 추가 리소스

- [PyAutoGUI 문서](https://pyautogui.readthedocs.io/)
- [Pytest 문서](https://docs.pytest.org/)
- [Slack API 문서](https://api.slack.com/messaging/webhooks)
- [Telegram Bot API 문서](https://core.telegram.org/bots/api)
- [Git 명령어 참조](https://git-scm.com/docs)
