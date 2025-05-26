## 보고서: Integrated Automation Solution 고도화 방안

**문서 버전:** 1.0
**작성일:** 2025년 5월 26일

### 1. 서론

본 문서는 현재 운영 중인 `integrated_automation_solution`의 기능을 한층 강화하고, 보다 체계적이며 확장 가능한 자동화 시스템으로 발전시키기 위한 고도화 방안을 제안합니다. 현재 시스템은 Claude Desktop GUI 자동화 및 Task Master MCP(Message Control Protocol)를 통해 소프트웨어 개발 태스크의 상당 부분을 자동화하는 강력한 기반을 갖추고 있습니다.

본 고도화의 주요 목표는 다음과 같습니다:

*   **워크플로우 관리 효율성 증대:** 전문 워크플로우 엔진 도입을 통한 복잡한 태스크 흐름 관리 및 모니터링 강화.
*   **배포 및 운영 편의성 향상:** Docker Compose를 활용한 시스템의 백그라운드 실행 및 일관된 환경 제공.
*   **Claude 연동 지능화:** Claude Desktop과의 상호작용, 특히 대화 길이 제한 문제를 효과적으로 관리하여 장기 실행 안정성 확보.
*   **확장성 및 유지보수성 개선:** 모듈화된 구조와 명확한 API 인터페이스를 통해 향후 기능 추가 및 유지보수를 용이하게 함.

### 2. 워크플로우 엔진 도입 및 Docker Compose 통합

#### 2.1. 워크플로우 엔진 선정

현재 시스템의 Python 기반 구조, CLI 명령어 및 외부 API(MCP) 호출 중심의 작업을 고려할 때, 다음 네 가지 워크플로우 엔진을 비교 검토하였습니다.

| 엔진명           | 주요 특징                                                                 | 장점                                                                  | 단점                                                            | Docker Compose 친화성 |
| :--------------- | :------------------------------------------------------------------------ | :-------------------------------------------------------------------- | :-------------------------------------------------------------- | :------------------- |
| **n8n**          | 노드 기반 시각적 워크플로우 디자인, 다양한 기본 제공 노드, JavaScript/TypeScript 확장    | 직관적, 빠른 프로토타이핑, 다양한 SaaS 연동, 커스텀 노드(HTTP, Python 스크립트 실행) 용이 | 복잡한 Python 로직 직접 통합 시 Execute Command/HTTP 노드 의존, 상태 관리 외부 위임 필요 | 매우 좋음              |
| **Apache Airflow** | Python 코드로 DAG 정의, 스케줄링 및 모니터링 강력, 대규모 커뮤니티         | 강력한 확장성, 성숙도, 다양한 오퍼레이터                              | 다소 무겁고 초기 설정 복잡, 로컬 개발 환경 구성 번거로울 수 있음    | 좋음                 |
| **Prefect**      | Python 네이티브, 동적 워크플로우, 데이터플로우 중심, 현대적 UI             | Python 개발자 친화적, 유연한 워크플로우 정의, 로컬 실행 및 테스트 용이 | Airflow 대비 커뮤니티 규모 작음, Kubernetes 외 환경 배포 옵션 비교적 단순 | 좋음                 |
| **Argo Workflows** | Kubernetes 네이티브, 컨테이너 기반 워크플로우                             | Kubernetes 환경에 최적화, 병렬 처리 및 확장성 우수                   | Kubernetes 클러스터 필요, Python 외 언어 워크플로우 작성 가능     | Kubernetes 필요     |

**선정 기준 및 최종 추천:**

현재 시스템이 로컬 데스크톱 환경에서 Claude GUI 자동화를 포함하고 있으며, 점진적인 기능 확장과 사용자 편의성을 중시한다고 가정할 때, **n8n**을 추천합니다.

*   **추천 이유:**
    *   **시각적 워크플로우:** 복잡한 자동화 흐름을 시각적으로 설계하고 관리하기 용이합니다.
    *   **기존 스크립트 활용:** "Execute Command" 노드를 통해 기존 `task_orchestrator_enhanced.py` 또는 `task_master_wrapper.py` 스크립트들을 그대로 활용하거나, 기능을 분리하여 작은 Python 스크립트로 만들어 호출하기 용이합니다.
    *   **MCP 연동:** HTTP Request 노드를 사용하여 Task Master MCP 서버와 통신할 수 있습니다 (MCP 서버가 HTTP API를 제공한다고 가정).
    *   **다양한 통합:** Slack, Telegram 등 알림 시스템과의 통합이 기본 노드로 제공되어 `notification_manager.py`의 역할을 n8n으로 이전하거나 확장할 수 있습니다.
    *   **Docker Compose 지원:** 공식 Docker 이미지가 제공되어 `docker-compose.yml`에 쉽게 통합할 수 있습니다.
    *   **유연한 확장:** 초기에는 간단한 스크립트 호출 중심으로 사용하다가, 점차 n8n 네이티브 기능으로 워크플로우를 이전하거나 커스텀 노드를 개발하여 고도화할 수 있습니다.

#### 2.2. Docker Compose 설계 방안

`docker-compose up -d`를 통해 핵심 백엔드 서비스들을 백그라운드에서 실행하고, 필요한 경우 로컬 스크립트와 연동하는 구조를 제안합니다.

*   **필요 서비스 컨테이너 정의 (예시):**
    *   `n8n`: n8n 메인 애플리케이션 서버.
    *   `taskmaster-mcp` (선택적): 만약 Task Master MCP 서버를 별도 컨테이너로 실행할 수 있다면 포함합니다. (현재는 `.cursor/mcp.json` 설정을 통해 npx로 실행되는 것으로 보이며, 이를 컨테이너화할 수 있는지 검토 필요)
    *   `database` (선택적): n8n 설정 및 실행 데이터 저장용 PostgreSQL/MySQL 또는 간단하게 SQLite (n8n 기본). 태스크 진행 상황 저장 DB로도 활용 가능.
    *   `reverse-proxy` (선택적): Nginx 등으로 각 서비스에 대한 단일 진입점 및 HTTPS 제공.

*   **`docker-compose.yml` 구조 예시 (n8n 중심):**

    ```yaml
    version: '3.8'

    services:
      n8n:
        image: n8nio/n8n
        container_name: n8n_automation
        restart: unless-stopped
        ports:
          - "5678:5678" # n8n 기본 포트
        environment:
          - GENERIC_TIMEZONE=Asia/Seoul # 사용자 환경에 맞게 설정
          # 필요한 API 키들은 n8n 내부 Credential Manager를 사용하거나,
          # Docker secrets 또는 .env 파일 마운트를 통해 안전하게 전달
          - N8N_ENCRYPTION_KEY=your_secret_encryption_key # n8n 보안키 (필수)
          # - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY} # .env 파일에서 가져오기
        volumes:
          - n8n_data:/home/node/.n8n
          # 필요한 경우 로컬 스크립트나 설정 파일 접근을 위한 볼륨 마운트
          - ./config.json:/app/config.json:ro
          - ./tasks.json:/app/tasks.json
          - ./logs:/app/logs # n8n 워크플로우에서 로그 파일 접근용
          - ./scripts:/app/scripts # n8n에서 로컬 스크립트 실행 시
        # user: "node" # 권한 문제 발생 시 주석 해제 또는 조정

    volumes:
      n8n_data: # n8n 데이터 영속화
    ```

*   **데이터 영속성 및 네트워크:**
    *   `volumes`를 사용하여 n8n의 설정 및 워크플로우 데이터를 영속화합니다.
    *   필요시 컨테이너 간 통신을 위한 Docker 네트워크를 정의합니다.

*   **백그라운드 실행 구성 (`docker-compose up -d`):**
    *   위와 같이 `docker-compose.yml` 파일이 구성되면, 해당 디렉토리에서 `docker-compose up -d` 명령으로 n8n (및 기타 서비스)이 백그라운드에서 실행됩니다.
    *   **주의:** `claude_desktop_automation.py`와 같이 실제 GUI를 제어하는 스크립트는 Docker 컨테이너 내부에서 직접 실행하기 매우 어렵습니다. (X server, display 환경 부재 등). 따라서, GUI 자동화는 계속 사용자의 로컬 데스크톱 환경에서 실행하고, n8n은 이 스크립트를 **트리거**하거나 (예: n8n의 "Execute Command" 노드로 로컬 Python 스크립트 실행) 또는 API를 통해 **결과를 받는 형태**로 연동해야 합니다. 혹은, GUI 자동화 부분은 현재 방식을 유지하고, n8n은 MCP 호출, 파일 처리, 알림 등 GUI와 직접 관련 없는 부분의 오케스트레이션을 담당할 수 있습니다.

#### 2.3. 기대 효과

*   워크플로우의 시각화 및 중앙 집중 관리.
*   다양한 서비스와의 쉬운 통합 및 확장.
*   오류 추적 및 재시도 로직의 표준화.
*   백엔드 서비스의 안정적인 백그라운드 실행.

### 3. Claude Desktop 연동 강화: 대화 길이 제한 문제 해결

#### 3.1. 현황 분석 및 문제점

현재 `claude_desktop_automation.py`는 `max_length_message.png` 이미지 감지를 통해 대화 길이 제한에 대응하려 하고 있으며, `projects_button.png`을 클릭하여 새 채팅을 생성하는 로직이 일부 구현되어 있습니다. 그러나 이 방식은 다음과 같은 개선점이 있습니다:

*   **사후 대응적:** 실제 길이 제한 메시지가 나타난 후에야 대응하므로, 이미 컨텍스트 손실이 발생했을 수 있습니다.
*   **정확도 한계:** 이미지 기반 감지는 UI 변경에 취약하며, 항상 정확하게 메시지를 감지하지 못할 수 있습니다.
*   **컨텍스트 단절:** 새 채팅으로 전환 시 이전 대화의 주요 컨텍스트를 효과적으로 전달하는 명시적인 메커니즘이 부족합니다.

#### 3.2. 개선 목표

*   Claude와의 상호작용 안정성 및 신뢰도 향상.
*   대화 길이 제한에 의한 작업 중단 최소화.
*   여러 대화에 걸쳐 일관된 컨텍스트 유지.

#### 3.3. 구체적인 로직 강화 방안

**`claude_desktop_automation.py` 내 `ClaudeDesktopAutomation` 클래스 개선 중심으로 제안**

1.  **선제적/능동적 새 대화 생성 로직 도입:**
    *   **토큰 카운터 (Approximation):**
        *   `input_text` 메소드 호출 시 입력되는 텍스트의 길이(또는 대략적인 토큰 수)를 누적하여 추적합니다.
        *   Claude 모델별 컨텍스트 윈도우 크기의 70-80%에 도달하면 (정확한 토큰 한계는 Anthropic 문서 참조 필요) 선제적으로 새 대화 생성을 트리거합니다.
        *   이를 위해 `self.current_conversation_tokens`와 같은 인스턴스 변수를 추가하여 관리합니다.
    *   **상호작용 횟수 기반:**
        *   하나의 작업(예: 단일 서브태스크 구현) 내에서 Claude와의 메시지 교환 횟수가 일정 기준(예: 10-15회)을 초과하면 새 대화를 고려합니다.
    *   **`run_automation` 메소드 수정:**
        *   `input_text`를 호출하기 *전에* 위 조건들을 확인하여, `create_new_chat=True` (또는 이에 상응하는 내부 플래그)로 설정하고 `create_new_chat_via_projects`를 호출하도록 합니다.

2.  **컨텍스트 요약 및 전달 메커니즘:**
    *   **새 대화 생성 시점의 컨텍스트 자동 요약:**
        *   새 대화가 필요한 시점에, 현재까지의 주요 작업 내용, 마지막 단계, 중요한 변수/결과 등을 요약합니다. 이 요약은 Orchestrator 레벨에서 관리되거나, Claude에게 현재 대화 내용을 기반으로 요약을 요청할 수도 있습니다.
        *   예: "Continuing Task X, Subtask Y. Previous step: Implemented function Z. Current focus: Testing function Z."
    *   **`input_text` 시 요약 정보 주입:**
        *   `claude_desktop_automation.py`의 `input_text` 메소드가 요약된 컨텍스트 문자열을 추가 인자로 받아, 실제 사용자 프롬프트 앞에 붙여서 입력하도록 수정합니다.
        *   `task_orchestrator_enhanced.py`에서 이 요약 정보를 관리하고 전달합니다.

3.  **상태 저장 및 복원 연계 (`orchestrator_progress.json` 활용):**
    *   **`orchestrator_progress.json`에 대화 관련 정보 추가:**
        *   현재 Claude 대화의 식별자(UI에서 특정할 수 있는 정보가 있다면, 예: 탭 이름이나 순서) 또는 마지막 성공 프롬프트/응답 내용을 기록합니다.
        *   시스템 재시작 시 이 정보를 바탕으로 컨텍스트 복원을 시도할 수 있습니다.
    *   **컨텍스트 복원 프롬프트 생성:**
        *   시스템이 재시작되거나 새 대화로 전환될 때, 저장된 상태 정보를 바탕으로 Claude에게 이전 작업 상황을 알려주는 복원 프롬프트를 자동으로 생성하여 전달합니다.

4.  **점진적 프롬프팅 및 상호작용 관리:**
    *   **긴 프롬프트 분할 전송:**
        *   매우 긴 초기 프롬프트나 코드 블록은 여러 개의 작은 조각으로 나누어 순차적으로 전송하고, 각 조각마다 Claude의 확인("understood", "continue" 등)을 유도합니다.
        *   이때 `click_continue_button` 로직이 단순히 'Continue' 버튼을 누르는 것 외에, Claude의 짧은 응답(예: '네, 계속하세요.')을 인지하고 다음 조각을 보내는 역할도 할 수 있도록 확장합니다.
    *   **명확한 작업 완료 신호 확인:**
        *   Claude가 작업 완료를 명시적으로 알리는 특정 문구(예: "Implementation complete.", "Tests passed.")를 프롬프트에 요청하고, GUI에서 해당 텍스트를 감지하여 작업 완료를 판정하는 로직을 추가합니다 (OCR 또는 화면 텍스트 읽기 기능 필요). `pyautogui`만으로는 한계가 있으므로, `pytesseract` 와 같은 OCR 라이브러리 도입을 고려할 수 있습니다.

#### 3.4. `claude_desktop_automation.py` 수정 방향 (핵심 변경점 요약)

*   `ClaudeDesktopAutomation` 클래스에 `self.current_conversation_context_summary` 와 같은 변수 추가.
*   `input_text(self, text, context_summary=None)`: `context_summary`를 받아 `text` 앞에 추가.
*   `run_automation(...)`: `create_new_chat` 로직을 토큰 카운터/상호작용 횟수 기반으로 강화. 새 대화 생성 시 Orchestrator로부터 컨텍스트 요약 정보를 받아 `self.current_conversation_context_summary` 업데이트.
*   `click_projects_button`, `click_project_button` 등의 안정성 향상 (UI 요소 변경에 대한 대응력 강화, 예를 들어 이미지 유사도 임계값 조정, 대체 이미지 사용 등).
*   `handle_max_length` 메소드는 이제 더 명확한 컨텍스트 전달 로직을 포함해야 하며, Orchestrator와 긴밀하게 연동하여 컨텍스트를 받고 새 대화를 준비합니다.
*   `wait_for_continue` 로직 개선: `initial_wait`, `max_wait_seconds` 등의 대기 시간 로직은 현재도 잘 구성되어 있으나, 여기에 더해 OCR을 통한 화면 텍스트 분석(예: "작업 완료", "다음 단계는 무엇인가요?")을 통해 단순 시간 초과가 아닌 능동적인 완료 판단을 시도할 수 있습니다.

#### 3.5. 기대 효과

*   장시간 실행되는 자동화 작업의 안정성 향상.
*   컨텍스트 유실 최소화로 인한 작업 품질 증대.
*   Claude Desktop UI 변경에 대한 대응력 강화.

### 4. 사용자 인터페이스/대시보드 API 요구사항 (개요)

사용자 인터페이스/대시보드 개발을 위해 다음과 같은 기능을 제공하는 RESTful API 엔드포인트들이 필요합니다. API 응답은 JSON 형식을 기본으로 합니다.

#### 4.1. 대시보드 목표 및 주요 기능

*   전체 자동화 프로세스의 현재 상태 실시간 모니터링.
*   개별 태스크 및 서브태스크의 진행 상황 추적.
*   오류 발생 시 빠른 원인 파악 및 재시작/개입 지원.
*   과거 실행 이력 및 통계 조회.

#### 4.2. 필요한 데이터 엔드포인트 (예시)

워크플로우 엔진(예: n8n) 또는 별도의 Python Flask/FastAPI 애플리케이션을 통해 제공될 수 있습니다. `orchestrator_progress.json` 과 `tasks.json` (또는 Task Master MCP가 제공하는 데이터)이 주요 데이터 소스가 됩니다.

*   **태스크 관리:**
    *   `GET /api/tasks`: 전체 태스크 목록 반환 (상태, ID, 이름, 설명, 서브태스크 요약 등).
        *   Query Parameters: `status` (pending, in-progress, completed, failed), `priority`
    *   `GET /api/tasks/{task_id}`: 특정 태스크의 상세 정보 반환 (서브태스크 목록 포함).
    *   `GET /api/tasks/{task_id}/subtasks/{subtask_id}`: 특정 서브태스크 상세 정보 반환.
    *   `POST /api/tasks`: 새 태스크 생성 (Task Master의 `add_task` 기능 연동).
    *   `PUT /api/tasks/{task_id}/status`: 태스크 상태 변경.
    *   `POST /api/tasks/{task_id}/expand`: 태스크 확장 (Task Master의 `expand_task` 연동).
*   **진행 상황 및 이력:**
    *   `GET /api/progress/current`: 현재 진행 중인 태스크/서브태스크 및 전체 진행률.
    *   `GET /api/progress/history`: 과거 실행 이력 (성공/실패, 시간 등).
    *   `GET /api/progress/stats`: 전체/일별/주별 태스크 완료 수, 평균 처리 시간 등 통계.
*   **로그 및 테스트 결과:**
    *   `GET /api/logs/orchestrator`: `automation_orchestrator.log` 내용 (실시간 스트리밍 또는 페이징).
    *   `GET /api/logs/claude`: `claude_automation.log` 내용.
    *   `GET /api/tests/history`: `test_history.json` 내용.
    *   `GET /api/tests/latest`: 최근 테스트 실행 결과.
*   **시스템 제어 (선택적, 보안 주의):**
    *   `POST /api/orchestrator/start`: 전체 자동화 시작.
    *   `POST /api/orchestrator/stop`: 현재 작업 중지.
    *   `POST /api/orchestrator/resume`: 중단된 작업 재개.
    *   `POST /api/orchestrator/retry_task/{task_id}`: 실패한 태스크 재시도.

#### 4.3. 데이터 형식 및 인증

*   **데이터 형식:** 모든 API 응답은 JSON을 사용합니다.
*   **인증 방식:** 초기에는 API 키 기반 인증 또는 간단한 토큰 기반 인증을 고려할 수 있습니다. 운영 환경에서는 OAuth2 등 보다 강력한 인증 메커니즘을 도입해야 합니다.

### 5. 결론 및 향후 과제

본 보고서에서 제안된 개선 방안들은 `integrated_automation_solution`을 한 단계 더 발전시켜, 보다 강력하고 지능적인 자동화 시스템으로 만들 것입니다. 워크플로우 엔진(n8n 추천) 도입과 Docker Compose를 통한 배포는 시스템 운영의 효율성과 확장성을 크게 향상시킬 것입니다. 또한, Claude Desktop 연동 로직 강화는 장시간 실행되는 자동화 작업의 안정성을 확보하는 데 핵심적인 역할을 할 것입니다.

**향후 과제:**

*   선정된 워크플로우 엔진(n8n)의 PoC(Proof of Concept) 개발 및 기존 스크립트와의 연동 테스트.
*   `claude_desktop_automation.py`의 대화 관리 로직 실제 코드 구현 및 테스트.
*   GUI 자동화 부분의 Docker 환경 실행 제약사항 해결 방안 심층 연구 (또는 n8n과의 연동 방식 명확화).
*   제안된 대시보드 API 명세 구체화 및 구현.
*   지속적인 모니터링 및 성능 최적화.

위 개선 사항들을 통해 더욱 강력하고 안정적인 AI 기반 개발 자동화 솔루션을 구축할 수 있을 것으로 기대됩니다.



## 코드 레벨 개발 계획 보고서: Integrated Automation Solution 고도화

**문서 버전:** 1.1
**작성일:** 2025년 5월 26일
**작성자:** AI Assistant

### 1. 서론

본 문서는 "Integrated Automation Solution 고도화 방안" 보고서 1.0 버전에 이어, 제안된 개선 사항들에 대한 구체적인 코드 레벨의 개발 계획을 제시합니다. 각 고도화 항목에 대해 필요한 코드 수정 방향, 신규 개발 요소, 그리고 예제 코드를 포함하여 실질적인 구현 가이드라인을 제공하는 것을 목표로 합니다.

### 2. 워크플로우 엔진 도입 (n8n) 및 Docker Compose 통합

#### 2.1. 목표

*   n8n을 중앙 워크플로우 오케스트레이션 도구로 활용합니다.
*   기존 Python 스크립트들(`task_orchestrator_enhanced.py`, `claude_desktop_automation.py` 등)을 n8n 워크플로우의 작업 단위로 통합합니다.
*   Docker Compose를 통해 n8n 및 관련 지원 서비스(필요시)를 백그라운드로 실행하여 운영 편의성을 증대시킵니다.

#### 2.2. n8n 워크플로우 설계 방향

n8n은 전체 자동화 흐름(예: Task Master MCP와 통신, 태스크 상태 관리, Claude Desktop 자동화 트리거, 알림 등)을 시각적으로 관리합니다.

*   **기존 Python 스크립트 연동:**
    *   **Execute Command 노드 활용:** n8n의 "Execute Command" 노드를 사용하여 로컬에 있는 Python 스크립트(`task_orchestrator_enhanced.py`의 특정 함수를 실행하는 래퍼 스크립트 또는 `task_master_wrapper.py`)를 실행하고 결과를 받아옵니다.
    *   **HTTP Request 노드 활용:** `claude_desktop_automation.py`와 같이 GUI를 직접 제어하는 부분은 로컬에서 Flask/FastAPI 등으로 간단한 API 서버를 띄우고, n8n이 HTTP 요청을 보내 GUI 자동화를 트리거하고 결과를 받는 방식으로 구성할 수 있습니다. (이는 Docker 환경에서 GUI 직접 제어가 어려운 문제를 우회하는 방법입니다.)

*   **n8n 워크플로우 예시 (개념적):**

    1.  **Trigger (시작점):** 스케줄러, Webhook, 수동 실행 등.
    2.  **TaskMaster MCP: Initialize/Get State:**
        *   "Execute Command" 노드: `python task_master_wrapper.py status` (또는 MCP 직접 호출 스크립트) 실행.
        *   또는 "HTTP Request" 노드: (만약 TaskMaster MCP가 HTTP API를 제공한다면) 다음 태스크 정보 요청.
    3.  **Loop (태스크 반복 처리):**
        *   **Get Task Details:** "Execute Command" 노드: `python task_master_wrapper.py show --task {task_id}`.
        *   **Prepare Claude Prompt:** "Function" 노드 (JavaScript/Python): 태스크 정보 기반으로 Claude 프롬프트 생성.
        *   **Trigger Claude Desktop Automation:**
            *   "HTTP Request" 노드: 로컬에서 실행 중인 `claude_desktop_automation` API 서버의 엔드포인트(예: `/run-automation`) 호출. (프롬프트, 프로젝트명 등 전달)
            *   **주의:** `claude_desktop_automation` API 서버는 로컬 데스크톱 환경에서 실행되어야 GUI 제어가 가능합니다.
        *   **Wait for Completion/Poll Status:** "Wait" 노드, "HTTP Request" 노드 (GUI 자동화 결과 폴링).
        *   **Run Tests:** "Execute Command" 노드: `python task_orchestrator.py --run-tests --task {task_id}` (또는 `TestRunner` 직접 호출).
        *   **Update TaskMaster MCP:** "Execute Command" 노드: `python task_master_wrapper.py set-status --id {task_id} --status done`.
    4.  **Notification:** "Slack" 또는 "Telegram" 노드: 작업 완료/실패 알림.

#### 2.3. Docker Compose 구성 (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n
    container_name: n8n_automation_orchestrator
    restart: unless-stopped
    ports:
      - "5678:5678" # n8n 웹 인터페이스 포트
    environment:
      - GENERIC_TIMEZONE=Asia/Seoul # 사용자 환경에 맞게 타임존 설정
      - N8N_ENCRYPTION_KEY= # 필수: 강력한 암호화 키 입력
      # ANTHROPIC_API_KEY, PERPLEXITY_API_KEY 등 API 키는 n8n의 Credentials 기능을 사용하거나,
      # Docker secrets 또는 아래와 같이 .env 파일을 통해 주입. (보안상 n8n Credentials 권장)
      # - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY} 
    volumes:
      - ./n8n_data:/home/node/.n8n # n8n 데이터 (워크플로우, 인증정보 등) 영속화
      # 로컬 프로젝트 디렉토리를 n8n 컨테이너 내부로 마운트 (Execute Command 노드에서 로컬 스크립트 실행 시)
      # 주의: 경로를 실제 프로젝트 경로에 맞게 수정해야 함.
      - ./shared_workspace:/mnt/workspace # Python 스크립트, 설정파일, 로그 공유
    # user: "node" # 권한 문제 발생 시 사용자 지정
    # Docker 네트워크 설정 (필요시 다른 서비스와의 통신용)
    # networks:
    #  - automation_net

  # (선택적) Task Master MCP 서버 컨테이너화 (가능하다면)
  # taskmaster_mcp:
  #   build:
  #     context: ./path_to_taskmaster_mcp_dockerfile # TaskMaster MCP Dockerfile 경로
  #   container_name: taskmaster_mcp_server
  #   restart: unless-stopped
  #   volumes:
  #     - ./config.json:/app/config.json:ro # TaskMaster MCP가 참조할 설정
  #     - ./tasks.json:/app/tasks.json
  #     - ./logs:/app/logs
  #   # networks:
  #   #   - automation_net

  # (선택적) GUI 자동화 API 서버 (Docker 외부에서 실행 권장)
  # gui_automation_api: # Docker로 실행 불가. 로컬에서 별도 실행 후 n8n에서 HTTP로 호출.
  #   # 이 서비스는 docker-compose로 관리되지 않고, 호스트 머신에서 직접 실행.
  #   # 예: python claude_desktop_api_server.py

volumes:
  n8n_data:

# networks:
#   automation_net:
#     driver: bridge
```

*   **실행:** `docker-compose up -d` 명령으로 `n8n` 서비스가 백그라운드에서 실행됩니다.
*   **GUI 자동화 연동:**
    *   `claude_desktop_automation.py`를 Flask/FastAPI를 사용하여 간단한 로컬 API 서버로 래핑합니다. (아래 4.3절 API 예시 참조)
    *   이 API 서버는 사용자의 데스크톱 환경(Docker 외부)에서 실행됩니다.
    *   n8n의 HTTP Request 노드가 Docker 컨테이너에서 이 로컬 API 서버로 요청을 보냅니다. 이를 위해 Docker 컨테이너가 호스트의 IP 및 포트에 접근할 수 있어야 합니다 (예: Docker 실행 시 `host.docker.internal` (Windows/Mac) 또는 특정 IP 사용).

### 3. Claude 대화 길이 제한 문제 해결: 코드 수정 방안

#### 3.1. `claude_desktop_automation.py` (`ClaudeDesktopAutomation` 클래스) 수정

*   **토큰 카운터 및 컨텍스트 관리 변수 추가:**

    ```python
    class ClaudeDesktopAutomation:
        def __init__(self, config_path="claude_desktop_config.json", project_root_path="."):
            # ... 기존 초기화 코드 ...
            self.config = self.default_config.copy()
            # ... (self.config 업데이트 로직) ...

            # 새롭게 추가될 속성들
            self.current_conversation_tokens = 0
            # 예시: Claude 3 Sonnet의 대략적인 컨텍스트 윈도우 고려 (실제 값은 모델 및 Anthropic 문서 확인)
            # claude-3-opus-20240229: 200K, claude-3-sonnet-20240229: 200K, claude-3-haiku-20240307: 200K
            # claude-3-5-sonnet-20240620: 200K
            # Claude-3.7-Sonnet-20250219는 120K로 .taskmasterconfig에 설정됨. 안전 마진을 두고 설정.
            self.max_tokens_per_conversation = self.config.get("max_tokens_per_conversation", 90000) # 약 90K (안전 계수 적용)
            self.current_conversation_summary = "" # 현재 대화의 요약본 (Orchestrator로부터 받음)
            
            # ... 기존 assets_dir 및 이미지 경로 설정 ...
    ```

*   **간단한 토큰 수 추정 함수 (예시):**

    ```python
    def _approximate_token_count(self, text: str) -> int:
        """간단하게 텍스트의 토큰 수를 추정합니다. (단어 수 기반 또는 글자 수 기반)"""
        # 매우 단순한 예: 영어 단어 평균 4글자, 한국어는 더 적을 수 있음.
        # 실제로는 보다 정교한 토크나이저 (예: tiktoken 라이브러리 일부 모델에 적용 가능) 사용 고려.
        # 여기서는 글자 수 기반으로 매우 러프하게 계산 (1 토큰 ~= 4 글자 가정)
        return len(text) // 4 
    ```

*   **`run_automation` 메소드 수정:**

    ```python
    def run_automation(self, input_text_content, wait_for_continue=True, create_new_chat=False, project_name=None, conversation_summary_for_new_chat=""):
        """
        ... (기존 독스트링) ...
        Args:
            ...
            conversation_summary_for_new_chat (str, optional): 새 대화 시작 시 주입할 이전 대화 요약.
        """
        logger.info(f"Claude 자동화 실행 요청. 새 채팅: {create_new_chat}, 프로젝트: {project_name}")
        
        # 입력될 프롬프트의 토큰 수 추정
        estimated_input_tokens = self._approximate_token_count(input_text_content)
        if conversation_summary_for_new_chat and create_new_chat: # 새 채팅이고 요약이 있으면 요약 토큰도 추가
            estimated_input_tokens += self._approximate_token_count(conversation_summary_for_new_chat)

        # 선제적 새 대화 생성 로직
        if self.current_conversation_tokens + estimated_input_tokens >= self.max_tokens_per_conversation:
            logger.warning(f"예상 토큰 수 ({self.current_conversation_tokens + estimated_input_tokens})가 임계값({self.max_tokens_per_conversation})을 초과하여 새 대화를 강제합니다.")
            create_new_chat = True # 새 대화 강제

        if not self.activate_window():
            return False
        
        if create_new_chat:
            if not project_name:
                logger.error("새 채팅을 생성하려면 프로젝트 이름이 필요합니다.")
                return False
            
            logger.info("새 채팅 생성 중...")
            if not self.create_new_chat_via_projects(project_name, context_summary=conversation_summary_for_new_chat): # 요약 전달
                logger.error("새 채팅 생성 실패")
                return False
            self.current_conversation_tokens = 0 # 새 대화이므로 토큰 카운터 리셋
            if conversation_summary_for_new_chat:
                self.current_conversation_tokens += self._approximate_token_count(conversation_summary_for_new_chat)
        
        # 이미지 기반 max length 메시지 확인 로직은 유지 (폴백 또는 추가 검증용)
        if self.check_max_length_message():
             logger.info("Max length 메시지가 감지되었습니다. Projects를 통해 새 채팅을 시작합니다...")
             if not project_name:
                 logger.error("새 채팅을 생성하려면 프로젝트 이름이 필요합니다.")
                 return False
             if not self.handle_max_length(project_name): # handle_max_length도 요약 전달 기능 필요
                 logger.error("Max length 상황 처리 실패 (새 채팅 생성 실패)")
                 return False
             self.current_conversation_tokens = 0 # 새 대화이므로 토큰 카운터 리셋


        if not self.input_text(input_text_content): # 이 메소드 내부에서 current_conversation_tokens 업데이트
            return False
        
        # ... (기존 press_enter 및 wait_for_continue 로직) ...
        
        # 응답을 받는다면, 응답의 토큰 수도 누적해야 하지만, 현재는 응답을 직접 가져오지 않으므로 생략.
        # 만약 OCR 등으로 응답 텍스트를 가져올 수 있다면 응답 토큰 수도 current_conversation_tokens에 추가.

        logger.info("자동화 태스크 완료")
        return True
    ```

*   **`create_new_chat_via_projects` 메소드 수정 (컨텍스트 요약 주입):**

    ```python
    def create_new_chat_via_projects(self, project_name, context_summary=None): # context_summary 인자 추가
        """Create new chat through Projects, optionally inputting a context summary."""
        logger.info(f"'{project_name}' 프로젝트에서 Projects를 통해 새 채팅을 생성합니다...")
        
        if not self.click_projects_button():
            logger.error("Projects 버튼을 찾을 수 없습니다.")
            return False
        
        time.sleep(self.config.get("short_delay", 1)) # 설정 파일에서 딜레이 값 가져오도록 수정 권장
        
        if not self.click_project_button(project_name): # click_project_button 내부에서 적절한 딜레이 필요
            logger.error(f"'{project_name}' 프로젝트 버튼을 찾을 수 없습니다.")
            return False
        
        time.sleep(self.config.get("medium_delay", 2)) # 프로젝트 로딩 대기
        
        self.current_conversation_tokens = 0 # 새 채팅 시작 시 토큰 초기화
        self.current_conversation_summary = context_summary if context_summary else ""

        if self.current_conversation_summary:
            logger.info("새 채팅에 이전 대화 요약을 입력합니다...")
            if self.input_text(f"Continuing based on previous context:\n{self.current_conversation_summary}\n\nPlease acknowledge or ask if you need more details before I proceed with the main task."):
                # 요약 입력 후 간단한 확인 과정 (예: 엔터) 필요시 추가
                self.press_enter()
                time.sleep(self.config.get("medium_delay", 5)) # Claude가 요약을 처리할 시간
                logger.info("컨텍스트 요약이 새 채팅에 입력되었습니다.")
            else:
                logger.warning("컨텍스트 요약 입력에 실패했습니다.")
                # 실패 시에도 일단 진행은 하되, 로그를 남겨서 문제 파악
        
        logger.info(f"'{project_name}' 프로젝트에서 새 채팅이 준비되었습니다.")
        return True
    ```

*   **`input_text` 메소드 내 토큰 업데이트:**

    ```python
    def input_text(self, text):
        if not self.window_active:
            if not self.activate_window():
                return False
        try:
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1) 
            pyautogui.press('delete')
            time.sleep(0.1)
            pyautogui.write(text, interval=0.01)
            
            # 입력된 텍스트의 토큰 수를 누적
            self.current_conversation_tokens += self._approximate_token_count(text)
            logger.info(f"텍스트 입력 완료 (첫 50자): {text[:50]}... (누적 토큰: ~{self.current_conversation_tokens})")
            return True
        except Exception as e:
            logger.error(f"텍스트 입력 중 오류: {e}")
            return False
    ```

#### 3.2. `task_orchestrator_enhanced.py` (`EnhancedTaskOrchestrator` 클래스) 수정

*   **컨텍스트 요약 생성 및 전달 로직 추가:**

    ```python
    class EnhancedTaskOrchestrator:
        def __init__(self, config_path: str = "config.json"):
            # ... 기존 초기화 ...
            self.current_global_context_summary = "Project setup: Using Python, Task Master MCP for task management." # 초기 요약
            self.max_summary_length = 500 # 요약의 최대 길이 (문자 수 기준)

        def _update_and_get_context_summary(self, new_info: str = "") -> str:
            """현재까지의 주요 진행 상황 및 새로운 정보를 바탕으로 컨텍스트 요약을 업데이트하고 반환합니다."""
            if new_info:
                self.current_global_context_summary += f"\nLatest update: {new_info}"

            # 요약이 너무 길어지면 앞부분을 자르거나, LLM을 통해 다시 요약하는 로직 추가 가능
            if len(self.current_global_context_summary) > self.max_summary_length:
                # 간단한 길이 제한 예시 (끝에서부터 max_summary_length 만큼만 유지)
                self.current_global_context_summary = self.current_global_context_summary[-self.max_summary_length:]
                # 더 좋은 방법: LLM을 호출하여 self.current_global_context_summary를 다시 요약
                # 예: self.current_global_context_summary = self.claude.summarize_text(self.current_global_context_summary)
                logger.info("컨텍스트 요약이 최대 길이에 도달하여 축약되었습니다.")
            
            return self.current_global_context_summary

        def process_task_with_mcp(self, task_id: str, subtask_id: Optional[str] = None):
            # ... 기존 로직 ...
            logger.info(f"태스크 처리 시작: task_id={task_id}, subtask_id={subtask_id}")
            # ... (progress_state 업데이트) ...

            task_file_path_str = self.task_master_client.get_task_file_path_str(task_id, subtask_id) # 새로운 헬퍼 메소드 가정
            
            # 현재 태스크에 대한 정보로 컨텍스트 요약 업데이트
            task_info_for_summary = f"Currently working on Task ID: {task_id}"
            if subtask_id:
                task_info_for_summary += f", Subtask ID: {subtask_id}"
            if task_file_path_str:
                 task_info_for_summary += f". Details in file: {task_file_path_str}"

            current_summary = self._update_and_get_context_summary(task_info_for_summary)

            # Claude에게 전달할 메인 프롬프트
            prompt = self.task_master_client.create_task_prompt(task_id, subtask_id) 
            # create_task_prompt 내부에서 파일 내용을 읽어오는 등의 MCP 명령어가 포함될 수 있음.
            # 또는 Orchestrator가 파일 내용을 읽어 prompt에 포함시킬 수도 있음.

            logger.info("Claude Desktop에 태스크 구현 요청 전송 중...")
            project_name = self.config.get("dev_project_name", "default")

            # run_automation 호출 시 요약 전달
            # claude_desktop_automation.py의 run_automation에서 create_new_chat이 True로 설정될 때 이 요약이 사용됨.
            # 또는, 이 요약을 prompt 시작 부분에 명시적으로 추가할 수도 있음.
            # 여기서는 run_automation이 내부적으로 새 채팅 생성 시 요약을 사용한다고 가정.
            success = self.claude.run_automation(
                prompt, 
                wait_for_continue=True, 
                create_new_chat=True, # 긴 태스크이므로 새 채팅에서 시작하는 것을 기본으로 고려
                project_name=project_name,
                conversation_summary_for_new_chat=current_summary # 새 채팅 시 주입될 요약
            )

            if success:
                logger.info("태스크 구현 요청 성공적으로 전송됨")
                # ... (기존 성공 처리 로직) ...
                # 작업 완료 후, Claude의 주요 응답이나 결과를 바탕으로 self.current_global_context_summary 업데이트
                # 예: completion_details = self.claude.get_last_response_summary() # 가상 함수
                # self._update_and_get_context_summary(f"Task {task_id} (Subtask {subtask_id}) completed. Key outcomes: {completion_details}")
            else:
                # ... (기존 실패 처리 로직) ...
            
            # ...
    ```

    **`task_master_mcp_client.py`에 `get_task_file_path_str` 헬퍼 메소드 추가 (예시):**
    ```python
    class TaskMasterMCPClient:
        # ...
        def get_task_file_path_str(self, task_id: str, subtask_id: Optional[str] = None) -> Optional[str]:
            """Task/subtask 파일의 상대 경로 문자열을 반환합니다."""
            task_file_path = self.get_task_file_path(task_id, subtask_id) # 기존 메소드 활용
            if task_file_path and self.dev_project_path:
                try:
                    # dev_project_path 기준으로 상대 경로 생성
                    relative_path = task_file_path.relative_to(Path(self.dev_project_path))
                    return str(relative_path)
                except ValueError:
                    # task_file_path가 dev_project_path의 하위 경로가 아닌 경우 (예외 처리)
                    logger.warning(f"Task file {task_file_path} is not within dev_project_path {self.dev_project_path}")
                    return str(task_file_path) # 절대 경로 반환 또는 None
            return None
    ```

### 4. 사용자 인터페이스/대시보드 API 개발 (Flask 예시)

다음은 Flask를 사용하여 일부 API 엔드포인트를 구현하는 간단한 예시입니다. 실제 운영 환경에서는 인증, 에러 처리, 데이터베이스 연동 등이 더 정교하게 구현되어야 합니다. 이 API 서버는 로컬에서 실행되거나, n8n과는 별개의 컨테이너로 Docker Compose에 포함될 수 있습니다.

`dashboard_api.py`:

```python
from flask import Flask, jsonify, request
import json
import os
from pathlib import Path

app = Flask(__name__)

# 설정값 (실제 환경에서는 config 파일 또는 환경변수에서 로드)
PROJECT_ROOT = Path(__file__).resolve().parent # API 파일이 프로젝트 루트에 있다고 가정
TASKS_FILE = PROJECT_ROOT / "tasks.json"
ORCHESTRATOR_PROGRESS_FILE = PROJECT_ROOT / "logs" / "orchestrator_progress.json"
TEST_HISTORY_FILE = PROJECT_ROOT / "logs" / "test_history.json"

# --- Helper Functions ---
def read_json_file(file_path, default_data=None):
    if not file_path.exists():
        return default_data if default_data is not None else {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        app.logger.error(f"Error reading {file_path}: {e}")
        return default_data if default_data is not None else {}

# --- API Endpoints ---

@app.route('/api/tasks', methods=['GET'])
def get_tasks_api():
    status_filter = request.args.get('status')
    tasks_data = read_json_file(TASKS_FILE, {"tasks": []})
    
    tasks_list = tasks_data.get("tasks", [])
    
    if status_filter:
        tasks_list = [task for task in tasks_list if task.get("status") == status_filter]
        
    return jsonify(tasks_list)

@app.route('/api/tasks/<string:task_id>', methods=['GET'])
def get_task_detail_api(task_id):
    tasks_data = read_json_file(TASKS_FILE, {"tasks": []})
    for task in tasks_data.get("tasks", []):
        if str(task.get("id")) == task_id:
            return jsonify(task)
        for subtask in task.get("subtasks", []):
            if f"{task.get('id')}.{subtask.get('id')}" == task_id:
                # 부모 태스크 정보와 함께 서브태스크 반환 (선택적)
                return jsonify({**subtask, "parent_task_id": task.get("id")})
    return jsonify({"error": "Task not found"}), 404

@app.route('/api/progress/current', methods=['GET'])
def get_current_progress_api():
    progress_data = read_json_file(ORCHESTRATOR_PROGRESS_FILE)
    return jsonify(progress_data)

@app.route('/api/tests/history', methods=['GET'])
def get_test_history_api():
    test_history = read_json_file(TEST_HISTORY_FILE)
    return jsonify(test_history)

# --- (선택적) 시스템 제어 API ---
# 아래 API는 실제 구현 시 TaskOrchestratorEnhanced 등과 연동하여
# 프로세스 제어 또는 n8n 워크플로우 트리거 로직이 필요합니다.
# 보안에 매우 유의해야 합니다.

# @app.route('/api/orchestrator/start', methods=['POST'])
# def start_orchestrator_api():
#     # TODO: n8n 워크플로우를 트리거하거나, 로컬 orchestrator 스크립트 실행
#     # 예: subprocess.Popen(["python", "task_orchestrator_enhanced.py"])
#     app.logger.info("Orchestrator start requested via API")
#     return jsonify({"message": "Orchestrator start initiated (simulated)"}), 202


if __name__ == '__main__':
    # 개발용으로 간단히 실행. 운영 시에는 Gunicorn 등 WSGI 서버 사용.
    app.run(debug=True, host='0.0.0.0', port=5001)
```

**API 서버 실행 (로컬 데스크톱에서):**

```bash
python dashboard_api.py
```

n8n은 이후 `http://<호스트IP>:5001/api/tasks` 와 같이 이 API 서버에 접근하여 대시보드 데이터를 가져오거나, 시스템 제어 요청을 보낼 수 있습니다.

### 5. 통합 실행 방안

1.  **GUI 자동화 API 서버 실행:** 사용자의 로컬 데스크톱에서 `python dashboard_api.py` (GUI 자동화 기능을 포함하도록 확장된 버전) 또는 `python claude_desktop_api_server.py` (별도 래퍼)를 실행합니다.
2.  **Docker Compose 실행:** `integrated_automation_solution` 프로젝트 루트에서 `docker-compose up -d`를 실행하여 n8n (및 기타 백엔드 서비스)을 백그라운드로 시작합니다.
3.  **n8n 워크플로우 설정:**
    *   n8n 웹 인터페이스(`http://localhost:5678`)에 접속합니다.
    *   새 워크플로우를 생성합니다.
    *   "Execute Command" 노드를 사용하여 로컬 머신의 `task_master_wrapper.py` 또는 Orchestrator의 작은 기능 단위 스크립트들을 호출하도록 설정합니다.
        *   이때 n8n 컨테이너가 로컬 파일 시스템에 접근하려면 Docker 볼륨 마운트가 올바르게 설정되어 있어야 하고, 스크립트가 있는 경로를 정확히 지정해야 합니다.
    *   "HTTP Request" 노드를 사용하여 1번에서 실행한 GUI 자동화 API 서버의 엔드포인트를 호출합니다.
        *   호스트 머신에서 실행 중인 API 서버에 접근하기 위해 `host.docker.internal:<포트번호>` (Docker Desktop for Windows/Mac) 또는 호스트의 IP 주소를 사용해야 할 수 있습니다.
4.  **워크플로우 실행 및 모니터링:** n8n 대시보드를 통해 워크플로우를 실행하고 진행 상황을 모니터링합니다.

### 6. 결론

본 코드 레벨 개발 계획은 제안된 고도화 방안을 구체화하기 위한 초기 단계입니다. 각 모듈의 실제 구현 시에는 더욱 상세한 설계와 테스트가 수반되어야 합니다. 특히 n8n과 로컬 GUI 자동화 스크립트 간의 연동 방식(로컬 API 서버 구축 또는 다른 IPC 메커니즘)은 시스템의 안정성과 유연성에 큰 영향을 미치므로 신중한 설계가 필요합니다. Docker Compose를 통해 n8n과 같은 백엔드 지원 도구들을 관리하고, Claude Desktop 자동화는 사용자 세션에서 직접 실행되는 형태로 분리하는 것이 현실적인 접근 방식일 수 있습니다.