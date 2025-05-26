# 빠른 시작 가이드 (Quick Start)

5분 안에 자동화 시스템을 실행하는 방법입니다.

## 1. 필수 준비사항 확인
- [ ] Python 3.11+ 설치
- [ ] Claude Desktop 실행 중
- [ ] 개발 프로젝트 준비 (예: `C:\Users\lhs\Desktop\dev\kido`)

## 2. 설치 (1분)
```bash
# 프로젝트 폴더로 이동
cd C:\Users\lhs\Downloads\integrated_automation_solution

# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

## 3. 최소 설정 (2분)

### 3.1 config.json 수정
```json
{
  "dev_project_path": "C:\\Users\\lhs\\Desktop\\dev\\kido",  // 개발 프로젝트 경로
  "dev_project_name": "kido",  // Claude 프로젝트명
  "project_type": "gradle"      // gradle, maven, python 중 선택
}
```

### 3.2 Claude 버튼 캡처
```bash
python claude_desktop_automation.py --setup
```
- Continue 버튼에 마우스 올리고 5초 대기
- Projects 버튼에 마우스 올리고 5초 대기
- 프로젝트명 입력: `kido`
- 프로젝트 버튼에 마우스 올리고 5초 대기

## 4. 첫 실행 (2분)

### 간단한 테스트 태스크로 시작
```bash
# 진행 상황 확인
python task_orchestrator_enhanced.py --check-progress

# 첫 번째 태스크 실행
python task_orchestrator_enhanced.py --task 1
```

## 5. 결과 확인
- Claude Desktop에서 자동으로 코드 생성
- 테스트 실행 결과 확인
- `logs/` 폴더에서 로그 확인

---

## 🚀 전체 자동 실행
설정이 완료되면:
```bash
python task_orchestrator_enhanced.py
```

## 🛠️ 문제 발생 시
1. Claude Desktop 재시작
2. 버튼 이미지 재캡처: `python claude_desktop_automation.py --setup`
3. 로그 확인: `logs/automation_orchestrator.log`

## 📋 자주 사용하는 명령어
```bash
# 태스크 목록 보기
python task_master_wrapper.py list

# 진행 상황 보기
python task_master_wrapper.py status

# 특정 태스크 초기화
python task_master_wrapper.py reset --task 1
```
