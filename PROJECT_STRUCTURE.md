# 프로젝트 구조

## 디렉토리 구조
```
integrated_automation_solution/
│
├── assets/                      # 버튼 이미지 파일
│   ├── README.md               # 이미지 가이드
│   ├── CAPTURE_GUIDE.md        # 캡처 방법 상세 가이드
│   ├── continue_button.png     # Continue 버튼 (수동 추가 필요)
│   ├── projects_button.png     # Projects 버튼 (수동 추가 필요)
│   ├── max_length_message.png  # Max length 메시지 (수동 추가 필요)
│   └── {project}_button.png    # 프로젝트별 버튼 (수동 추가 필요)
│
├── logs/                       # 실행 로그
│   ├── automation_orchestrator.log
│   ├── claude_automation.log
│   └── test_history.json
│
├── config.json                 # 메인 설정 (개발 프로젝트 경로 포함)
├── claude_desktop_config.json  # Claude Desktop 자동화 설정
├── notification_config.json    # 알림 설정 (Slack 등)
├── tasks.json                  # 태스크 정의 및 상태
│
├── task_orchestrator.py        # 메인 오케스트레이터
├── claude_desktop_automation.py # Claude Desktop GUI 자동화
├── code_analyzer.py            # 코드 품질 분석
├── notification_manager.py     # 알림 관리
│
├── create_sample_images.py     # 샘플 이미지 생성 (선택사항)
├── UPDATE_SUMMARY.md          # 사용 가이드
└── PROJECT_STRUCTURE.md       # 이 파일

## 개발 프로젝트 구조 (예: kido)
```
C:\Users\lhs\Desktop\dev\kido/
│
├── tasks/                      # Task 정의 파일
│   ├── task_1.txt
│   ├── subtask_1_1.txt
│   ├── subtask_1_2.txt
│   └── task_2.txt
│
├── src/                       # 소스 코드
│   └── main/
│       └── java/
│
├── test/                      # 테스트 코드
│   └── java/
│
├── build.gradle               # Gradle 설정
└── gradlew.bat               # Gradle 래퍼

## 설정 파일 관계
1. **config.json**: 전체 시스템 설정
   - dev_project_path: 개발 프로젝트 경로
   - dev_project_name: Claude 프로젝트 이름
   - 테스트, Git, 알림 설정

2. **claude_desktop_config.json**: GUI 자동화 설정
   - 버튼 이미지 파일명
   - 재시도 횟수, 신뢰도 임계값

3. **notification_config.json**: 알림 채널 설정
   - Slack webhook URL
   - 알림 옵션

## 데이터 흐름
1. task_orchestrator.py가 tasks.json 읽기
2. 개발 프로젝트의 task 파일 경로 생성
3. Claude에 파일 경로 전달
4. Claude가 JetBrains MCP로 파일 읽고 구현
5. 개발 프로젝트에서 테스트 실행
6. 개발 프로젝트에서 Git 커밋