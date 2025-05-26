# 프로젝트 실행 가이드

## 사전 요구사항
- Docker Desktop 설치 및 실행
- Python 3.x 설치
- n8n 워크플로우 파일 준비

## 실행 단계

### 1. 가상환경 설정 및 의존성 설치
```bash
cd /Users/lhs/Downloads/for-budget-vibe-coding
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install flask flask-cors
```

### 2. 필요한 디렉토리 생성
```bash
mkdir -p logs n8n_data shared_workspace
```

### 3. tasks.json 파일 확인
- `tasks.json` 파일이 존재하는지 확인
- 없으면 샘플 태스크로 생성

### 4. API 서버 시작

#### Dashboard API (포트 5002)
```bash
source venv/bin/activate
python dashboard_api.py --port 5002 &
```

#### Claude Desktop API (포트 5001)
```bash
source venv/bin/activate
python claude_desktop_api_server.py --port 5001 &
```

### 5. n8n 시작
```bash
docker-compose up -d
```

### 6. n8n 워크플로우 설정
1. 브라우저에서 http://localhost:5678 접속
2. `n8n_workflows/claude_automation_workflow.json` 파일 임포트
3. 워크플로우 실행

## 서비스 URL
- n8n: http://localhost:5678
- Claude API: http://localhost:5001
- Dashboard API: http://localhost:5002

## 종료 방법
```bash
# Docker 컨테이너 중지
docker-compose down

# Python 프로세스 종료
pkill -f "dashboard_api.py"
pkill -f "claude_desktop_api_server.py"
```

## 문제 해결
- 포트 충돌 시: 사용 중인 포트 확인 (`lsof -i :포트번호`)
- API 연결 실패: 모든 서비스가 실행 중인지 확인
- tasks.json 오류: 파일이 올바른 JSON 형식인지 확인