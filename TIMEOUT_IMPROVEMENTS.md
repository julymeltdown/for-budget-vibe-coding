# 타임아웃 개선사항

## 주요 개선 내용

### 1. 동적 타임아웃 시스템
- 작업 복잡도에 따라 타임아웃을 자동 조정
- 복잡도 점수 1-10 기반으로 5분~30분 사이 조정
- Task Master의 복잡도 분석 보고서 활용

### 2. 활동 감지 시스템
- 화면 변화를 감지하여 Claude가 여전히 작업 중인지 확인
- PIL/numpy를 사용한 스크린샷 비교
- 2% 이상의 픽셀 변화 시 활동으로 인식
- 활동 감지 시 타임아웃을 5분씩 연장 (최대 2배까지)

### 3. 점진적 체크 인터벌
- 시간이 지날수록 체크 간격을 점진적으로 증가
  - 0-5분: 기본 간격 (15초)
  - 5-15분: 1.5배 간격 (22.5초)
  - 15-30분: 2배 간격 (30초)
  - 30분 이상: 3배 간격 (45초, 최대 60초)

### 4. 작업 실패 시 재시도 메커니즘
- 연속 실패 카운터 추가
- 최대 3번까지 재시도 허용
- 실패 시 10초 대기 후 재시도

## 설정 옵션

### claude_desktop_config.json
```json
{
  // 동적 타임아웃 설정
  "dynamic_timeout_enabled": true,          // 동적 타임아웃 활성화
  "max_wait_for_complex_tasks_s": 1800,     // 복잡한 작업 최대 대기 시간 (30분)
  
  // 활동 감지 설정
  "activity_detection_enabled": true,       // 활동 감지 활성화
  "activity_timeout_extension_s": 300,      // 활동 감지 시 연장 시간 (5분)
  "activity_detection_threshold": 0.02,     // 활동 감지 임계값 (2%)
  
  // 점진적 인터벌 설정
  "progressive_interval_enabled": true,     // 점진적 인터벌 활성화
  "max_check_interval_s": 60,              // 최대 체크 간격 (60초)
  
  // 기존 타임아웃 설정
  "response_initial_wait_s": 30,           // 초기 대기 시간
  "response_max_wait_s": 300,              // 기본 최대 대기 시간
  "response_check_interval_normal_s": 15,   // 기본 체크 간격
  "response_check_interval_after_continue_s": 5  // Continue 버튼 후 체크 간격
}
```

## 사용 방법

### 1. 활동 감지를 위한 추가 패키지 설치 (선택사항)
```bash
pip install pillow numpy
```
- 설치하지 않아도 작동하지만, 활동 감지 기능이 비활성화됩니다.

### 2. 특정 작업의 복잡도 설정
```bash
# 명령줄에서 직접 복잡도 지정
python claude_desktop_automation.py --task-complexity 8 --input "complex_task.txt" --project-name myproject

# Task Orchestrator는 자동으로 복잡도 점수를 가져옴
python task_orchestrator_enhanced.py
```

### 3. Task Master 복잡도 분석 활용
```bash
# 복잡도 분석 실행
python task_master_wrapper.py analyze-complexity

# 분석 보고서 확인
python task_master_wrapper.py complexity-report
```

## 복잡도 점수 가이드

- **1-3점**: 간단한 작업 (5분 타임아웃)
  - 간단한 함수 구현
  - 기본적인 테스트 작성
  - 설정 파일 수정

- **4-7점**: 중간 복잡도 (5-30분 사이 선형 보간)
  - 여러 클래스 구현
  - 통합 테스트 작성
  - 리팩토링 작업

- **8-10점**: 복잡한 작업 (30분 타임아웃)
  - 대규모 아키텍처 변경
  - 복잡한 알고리즘 구현
  - 전체 모듈 재작성

## 문제 해결

### 타임아웃이 여전히 부족한 경우
1. `max_wait_for_complex_tasks_s` 값을 더 크게 설정 (예: 2700 = 45분)
2. `activity_timeout_extension_s` 값을 증가 (예: 600 = 10분)

### 활동 감지가 제대로 작동하지 않는 경우
1. `activity_detection_threshold` 값 조정 (낮추면 더 민감해짐)
2. PIL/numpy가 설치되어 있는지 확인

### 너무 자주 체크하는 경우
1. `max_check_interval_s` 값 증가 (예: 120 = 2분)
2. `progressive_interval_enabled`를 true로 설정 확인

## 로그 확인

개선된 로그 메시지:
```
2024-01-01 10:00:00 - Dynamic timeout set to 1800s based on task complexity: 9/10
2024-01-01 10:05:00 - Activity detected - Claude is still working
2024-01-01 10:10:00 - Progress: 600s / 1800s (33.3%) - Last activity: 10s ago
2024-01-01 10:25:00 - Activity detected - extending timeout to 2100s
```

## 성능 개선 효과

- **기존**: 5분 고정 타임아웃, 일정한 체크 간격
- **개선**: 
  - 복잡한 작업에 대해 최대 60분까지 대기 가능
  - 불필요한 체크 감소 (점진적 인터벌)
  - 실제 작업 중일 때만 대기 시간 연장
  - 20분 이상 걸리는 MCP 작업도 안정적으로 처리
