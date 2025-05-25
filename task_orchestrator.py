import os
import sys
import logging
import argparse
import json
import time
from pathlib import Path
import subprocess
import threading
import queue

# 자체 모듈 임포트
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from gui_test_automation import ClaudeDesktopAutomation, TestRunner
from code_analyzer import CodeAnalyzer
from notification_manager import NotificationManager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("automation_orchestrator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("orchestrator")

class TaskOrchestrator:
    def __init__(self, config_path=None):
        """태스크 오케스트레이터 클래스 초기화"""
        # 기본 설정
        self.default_config = {
            "project_dir": ".",
            "src_dir": "src",
            "test_dir": "tests",
            "task_definition_file": "tasks.json",
            "max_subtask_failures": 5,
            "check_quality_after_tests": True,
            "auto_commit_after_subtask": True,
            "git_enabled": True,
            "git_repo": ".",
            "claude_desktop": {
                "enabled": True,
                "config_path": "claude_desktop_config.json"
            },
            "notification": {
                "enabled": True,
                "config_path": "notification_config.json"
            }
        }
        
        # 설정 파일 로드
        self.config = self.default_config.copy()
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    self.config.update(user_config)
                logging.info(f"설정 파일 로드 완료: {config_path}")
            except Exception as e:
                logging.error(f"설정 파일 로드 실패: {e}")
        
        # 태스크 정의 로드
        self.tasks = self._load_tasks()
        
        # 컴포넌트 초기화
        self.claude = ClaudeDesktopAutomation(
            self.config["claude_desktop"].get("config_path") if self.config["claude_desktop"]["enabled"] else None
        )
        
        self.test_runner = TestRunner()
        
        self.code_analyzer = CodeAnalyzer()
        
        self.notification = NotificationManager(
            self.config["notification"].get("config_path") if self.config["notification"]["enabled"] else None
        )
        
        # 현재 상태
        self.current_task = None
        self.current_subtask = None
        
        logging.info("태스크 오케스트레이터 초기화 완료")
    
    def _load_tasks(self):
        """태스크 정의 파일을 로드합니다."""
        task_file = os.path.join(self.config["project_dir"], self.config["task_definition_file"])
        
        if not os.path.exists(task_file):
            logging.warning(f"태스크 정의 파일을 찾을 수 없습니다: {task_file}")
            return []
        
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                tasks = json.load(f)
            
            logging.info(f"태스크 정의 로드 완료: {len(tasks)} 태스크")
            return tasks
        
        except Exception as e:
            logging.error(f"태스크 정의 로드 실패: {e}")
            return []
    
    def _save_tasks(self):
        """태스크 정의 파일을 저장합니다."""
        task_file = os.path.join(self.config["project_dir"], self.config["task_definition_file"])
        
        try:
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(self.tasks, f, indent=2)
            
            logging.info(f"태스크 정의 저장 완료: {task_file}")
            return True
        
        except Exception as e:
            logging.error(f"태스크 정의 저장 실패: {e}")
            return False
    
    def git_commit(self, message):
        """Git 커밋을 수행합니다."""
        if not self.config["git_enabled"]:
            logging.info("Git 기능 비활성화됨")
            return True
        
        try:
            # Git 상태 확인
            status_cmd = ["git", "status", "--porcelain"]
            status_result = subprocess.run(
                status_cmd,
                cwd=self.config["git_repo"],
                capture_output=True,
                text=True
            )
            
            # 변경사항이 없으면 커밋하지 않음
            if not status_result.stdout.strip():
                logging.info("커밋할 변경사항이 없습니다.")
                return True
            
            # 변경된 파일 추가
            add_cmd = ["git", "add", "."]
            add_result = subprocess.run(
                add_cmd,
                cwd=self.config["git_repo"],
                capture_output=True,
                text=True
            )
            
            if add_result.returncode != 0:
                logging.error(f"Git add 실패: {add_result.stderr}")
                return False
            
            # 커밋
            commit_cmd = ["git", "commit", "-m", message]
            commit_result = subprocess.run(
                commit_cmd,
                cwd=self.config["git_repo"],
                capture_output=True,
                text=True
            )
            
            if commit_result.returncode != 0:
                logging.error(f"Git commit 실패: {commit_result.stderr}")
                return False
            
            logging.info(f"Git 커밋 성공: {message}")
            return True
        
        except Exception as e:
            logging.error(f"Git 커밋 중 오류 발생: {e}")
            return False
    
    def run_claude_prompt(self, prompt, wait_for_continue=True, create_new_chat=False):
        """Claude Desktop에 프롬프트를 전송합니다."""
        if not self.config["claude_desktop"]["enabled"]:
            logging.info("Claude Desktop 기능 비활성화됨")
            return True
        
        try:
            result = self.claude.run_automation(prompt, wait_for_continue, create_new_chat)
            
            if result:
                logging.info("Claude Desktop 프롬프트 전송 성공")
            else:
                logging.error("Claude Desktop 프롬프트 전송 실패")
            
            return result
        
        except Exception as e:
            logging.error(f"Claude Desktop 프롬프트 전송 중 오류 발생: {e}")
            return False
    
    def generate_subtask_prompt(self, task, subtask):
        """서브태스크 프롬프트를 생성합니다."""
        prompt = f"# 태스크: {task['name']}\n\n"
        prompt += f"## 서브태스크: {subtask['name']}\n\n"
        
        # 태스크 설명
        if "description" in task:
            prompt += f"### 태스크 설명\n{task['description']}\n\n"
        
        # 서브태스크 설명
        if "description" in subtask:
            prompt += f"### 서브태스크 설명\n{subtask['description']}\n\n"
        
        # 요구사항
        if "requirements" in subtask:
            prompt += "### 요구사항\n"
            for req in subtask["requirements"]:
                prompt += f"- {req}\n"
            prompt += "\n"
        
        # 제약사항
        if "constraints" in subtask:
            prompt += "### 제약사항\n"
            for constraint in subtask["constraints"]:
                prompt += f"- {constraint}\n"
            prompt += "\n"
        
        # 테스트 요구사항
        if "test_requirements" in subtask:
            prompt += "### 테스트 요구사항\n"
            for test_req in subtask["test_requirements"]:
                prompt += f"- {test_req}\n"
            prompt += "\n"
        
        # 헥사고날 아키텍처 요구사항
        prompt += "### 아키텍처 요구사항\n"
        prompt += "- 헥사고날 아키텍처 패턴을 따라야 합니다.\n"
        prompt += "- 도메인 로직은 외부 의존성으로부터 격리되어야 합니다.\n"
        prompt += "- 포트와 어댑터를 명확히 구분해야 합니다.\n\n"
        
        # JWT 인증 요구사항 (필요한 경우)
        if "auth" in task and task["auth"]:
            prompt += "### 인증 요구사항\n"
            prompt += "- JWT 기반 인증을 구현해야 합니다.\n"
            prompt += "- Access Token과 Refresh Token을 모두 지원해야 합니다.\n"
            prompt += "- 토큰 만료 처리 로직을 구현해야 합니다.\n\n"
        
        # 코드 품질 요구사항
        prompt += "### 코드 품질 요구사항\n"
        prompt += "- 모든 코드는 테스트 가능해야 합니다.\n"
        prompt += "- 모의(mock) 처리나 주석 처리된 코드를 남기지 마세요.\n"
        prompt += "- 모든 테스트는 실제로 통과해야 합니다.\n\n"
        
        # 최종 지시사항
        prompt += "### 지시사항\n"
        prompt += "1. 요구사항에 맞는 코드를 작성하세요.\n"
        prompt += "2. 모든 테스트가 통과하는지 확인하세요.\n"
        prompt += "3. 헥사고날 아키텍처와 코드 품질 요구사항을 준수하세요.\n"
        prompt += "4. 임시 처리(모의 처리, 주석 처리된 코드)를 남기지 마세요.\n"
        
        return prompt
    
    def generate_code_review_prompt(self, task):
        """코드 리뷰 프롬프트를 생성합니다."""
        prompt = f"# 코드 리뷰 요청: {task['name']}\n\n"
        
        # 태스크 설명
        if "description" in task:
            prompt += f"## 태스크 설명\n{task['description']}\n\n"
        
        # 코드 리뷰 지시사항
        prompt += "## 코드 리뷰 지시사항\n"
        prompt += "다음 측면에서 코드를 검토해 주세요:\n\n"
        
        prompt += "1. **아키텍처 준수**\n"
        prompt += "   - 헥사고날 아키텍처 패턴을 올바르게 따르고 있는지\n"
        prompt += "   - 도메인 로직이 외부 의존성으로부터 격리되어 있는지\n"
        prompt += "   - 포트와 어댑터가 명확히 구분되어 있는지\n\n"
        
        prompt += "2. **코드 품질**\n"
        prompt += "   - 코드가 깔끔하고 가독성이 좋은지\n"
        prompt += "   - 적절한 추상화와 모듈화가 이루어졌는지\n"
        prompt += "   - 불필요한 복잡성이 없는지\n\n"
        
        prompt += "3. **테스트 품질**\n"
        prompt += "   - 테스트 커버리지가 충분한지\n"
        prompt += "   - 테스트가 의미 있는 시나리오를 검증하는지\n"
        prompt += "   - 테스트가 독립적이고 신뢰할 수 있는지\n\n"
        
        if "auth" in task and task["auth"]:
            prompt += "4. **인증 구현**\n"
            prompt += "   - JWT 기반 인증이 올바르게 구현되었는지\n"
            prompt += "   - Access Token과 Refresh Token이 모두 지원되는지\n"
            prompt += "   - 토큰 만료 처리 로직이 적절한지\n\n"
        
        prompt += "5. **개선 제안**\n"
        prompt += "   - 코드 개선을 위한 구체적인 제안\n"
        prompt += "   - 잠재적인 문제점이나 버그\n"
        prompt += "   - 성능 최적화 가능성\n\n"
        
        prompt += "코드 리뷰 결과를 다음 형식으로 제공해 주세요:\n\n"
        prompt += "- 전반적인 평가 (1-5점)\n"
        prompt += "- 주요 장점\n"
        prompt += "- 주요 개선 사항\n"
        prompt += "- 세부 피드백 (파일별 또는 컴포넌트별)\n"
        
        return prompt
    
    def process_subtask(self, task_id, subtask_id):
        """서브태스크를 처리합니다."""
        # 태스크 및 서브태스크 찾기
        task = next((t for t in self.tasks if t["id"] == task_id), None)
        if not task:
            logging.error(f"태스크를 찾을 수 없습니다: {task_id}")
            return False
        
        subtask = next((s for s in task["subtasks"] if s["id"] == subtask_id), None)
        if not subtask:
            logging.error(f"서브태스크를 찾을 수 없습니다: {subtask_id}")
            return False
        
        # 현재 상태 업데이트
        self.current_task = task
        self.current_subtask = subtask
        
        logging.info(f"서브태스크 처리 시작: {task['name']} - {subtask['name']}")
        
        # 프롬프트 생성 및 Claude Desktop 실행
        prompt = self.generate_subtask_prompt(task, subtask)
        
        if not self.run_claude_prompt(prompt, wait_for_continue=True, create_new_chat=True):
            logging.error("Claude Desktop 프롬프트 전송 실패")
            
            # 알림 전송
            self.notification.notify_subtask_failure(
                task_id, task["name"], subtask_id, subtask["name"], 1,
                "Claude Desktop 프롬프트 전송 실패"
            )
            
            return False
        
        # 테스트 실행 및 결과 확인
        max_attempts = self.config["max_subtask_failures"]
        success = False
        
        for attempt in range(max_attempts):
            logging.info(f"테스트 시도 {attempt+1}/{max_attempts}")
            
            # 테스트 실행
            test_result = self.test_runner.run_tests(task_id, subtask_id)
            
            # 테스트 성공 시
            if test_result["success"]:
                logging.info(f"테스트 성공 (시도 {attempt+1}/{max_attempts})")
                success = True
                
                # 코드 품질 검사 (설정된 경우)
                if self.config["check_quality_after_tests"]:
                    quality_result = self.code_analyzer.analyze_code_quality(self.config["src_dir"])
                    
                    # 모의 처리 또는 주석 처리된 코드 감지 시 알림
                    if quality_result["overall_quality"]["has_mocks"] or quality_result["overall_quality"]["has_commented_code"]:
                        self.notification.notify_mock_detection(quality_result["mock_analysis"])
                
                # Git 커밋 (설정된 경우)
                if self.config["auto_commit_after_subtask"]:
                    commit_message = f"Complete subtask: {subtask['name']} ({subtask_id})"
                    self.git_commit(commit_message)
                
                break
            
            # 테스트 실패 시
            else:
                logging.error(f"테스트 실패 (시도 {attempt+1}/{max_attempts})")
                
                # 마지막 시도가 아니면 Claude에 수정 요청
                if attempt < max_attempts - 1:
                    # 실패 알림 (마지막 시도 전에만)
                    if attempt == max_attempts - 2:
                        self.notification.notify_test_failure(task_id, subtask_id, test_result)
                    
                    # 수정 요청 프롬프트
                    fix_prompt = f"테스트가 실패했습니다. 다음 오류를 수정해 주세요:\n\n```\n{test_result['output']}\n```\n\n"
                    fix_prompt += "코드를 수정하고 모든 테스트가 통과하는지 확인해 주세요."
                    
                    if not self.run_claude_prompt(fix_prompt, wait_for_continue=True, create_new_chat=False):
                        logging.error("Claude Desktop 수정 요청 전송 실패")
                        break
                
                # 최대 시도 횟수 초과 시 알림
                elif attempt == max_attempts - 1:
                    self.notification.notify_subtask_failure(
                        task_id, task["name"], subtask_id, subtask["name"], max_attempts,
                        f"최대 시도 횟수 초과 ({max_attempts}회)"
                    )
        
        # 서브태스크 상태 업데이트
        subtask["status"] = "completed" if success else "failed"
        subtask["completed_at"] = time.time()
        self._save_tasks()
        
        return success
    
    def process_task(self, task_id):
        """태스크를 처리합니다."""
        # 태스크 찾기
        task = next((t for t in self.tasks if t["id"] == task_id), None)
        if not task:
            logging.error(f"태스크를 찾을 수 없습니다: {task_id}")
            return False
        
        logging.info(f"태스크 처리 시작: {task['name']}")
        
        # 태스크 상태 업데이트
        task["status"] = "in_progress"
        task["started_at"] = time.time()
        self._save_tasks()
        
        # 각 서브태스크 처리
        all_success = True
        
        for subtask in task["subtasks"]:
            # 이미 완료된 서브태스크는 건너뜀
            if subtask["status"] == "completed":
                logging.info(f"서브태스크 건너뜀 (이미 완료됨): {subtask['name']}")
                continue
            
            # 서브태스크 처리
            subtask_success = self.process_subtask(task_id, subtask["id"])
            
            if not subtask_success:
                all_success = False
                
                # 실패 시 중단 여부 확인
                if subtask.get("critical", False):
                    logging.error(f"중요 서브태스크 실패로 태스크 중단: {subtask['name']}")
                    break
        
        # 태스크 상태 업데이트
        task["status"] = "completed" if all_success else "failed"
        task["completed_at"] = time.time()
        self._save_tasks()
        
        # 태스크 완료 시 코드 리뷰 수행
        if all_success:
            logging.info(f"태스크 완료: {task['name']}")
            
            # 코드 리뷰 프롬프트 생성 및 Claude Desktop 실행
            review_prompt = self.generate_code_review_prompt(task)
            
            if not self.run_claude_prompt(review_prompt, wait_for_continue=True, create_new_chat=True):
                logging.error("Claude Desktop 코드 리뷰 요청 전송 실패")
            
            # 알림 전송
            self.notification.notify_task_completion(task_id, task["name"])
            
            # Git 커밋
            if self.config["git_enabled"]:
                commit_message = f"Complete task: {task['name']} ({task_id})"
                self.git_commit(commit_message)
        
        else:
            logging.error(f"태스크 실패: {task['name']}")
        
        return all_success
    
    def run(self, task_id=None):
        """오케스트레이터를 실행합니다."""
        if not self.tasks:
            logging.error("처리할 태스크가 없습니다.")
            return False
        
        # 특정 태스크만 처리
        if task_id:
            return self.process_task(task_id)
        
        # 모든 태스크 처리
        all_success = True
        
        for task in self.tasks:
            # 이미 완료된 태스크는 건너뜀
            if task["status"] == "completed":
                logging.info(f"태스크 건너뜀 (이미 완료됨): {task['name']}")
                continue
            
            # 태스크 처리
            task_success = self.process_task(task["id"])
            
            if not task_success:
                all_success = False
        
        return all_success


# 메인 함수
def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='통합 자동화 오케스트레이터')
    parser.add_argument('--config', type=str, help='설정 파일 경로')
    parser.add_argument('--task', type=str, help='처리할 태스크 ID')
    parser.add_argument('--subtask', type=str, help='처리할 서브태스크 ID')
    
    args = parser.parse_args()
    
    # 오케스트레이터 생성
    orchestrator = TaskOrchestrator(args.config)
    
    # 특정 서브태스크만 처리
    if args.task and args.subtask:
        orchestrator.process_subtask(args.task, args.subtask)
    
    # 특정 태스크만 처리
    elif args.task:
        orchestrator.process_task(args.task)
    
    # 모든 태스크 처리
    else:
        orchestrator.run()


if __name__ == "__main__":
    main()
