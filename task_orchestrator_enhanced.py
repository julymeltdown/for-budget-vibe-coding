"""
개선된 Task Orchestrator
Task Master MCP 통합 및 진행 상황 추적 기능이 추가된 버전
"""

import os
import sys
import logging
import argparse
import json
import time
import subprocess
import re
import platform
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# 모듈 임포트
from claude_desktop_automation import ClaudeDesktopAutomation
from code_analyzer import CodeAnalyzer
from notification_manager import NotificationManager
from task_master_mcp_client import TaskMasterMCPClient

# 로그 디렉토리 생성
LOGS_DIR = "logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# 로깅 설정
log_file_path = os.path.join(LOGS_DIR, "automation_orchestrator.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("orchestrator_enhanced")


class EnhancedTaskOrchestrator:
    """개선된 태스크 오케스트레이터"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.project_root = os.path.abspath(self.config.get("project_dir", "."))
        
        # 컴포넌트 초기화
        self.claude = ClaudeDesktopAutomation(self.config.get("claude_desktop", {}).get("config_path"))
        self.code_analyzer = CodeAnalyzer()
        self.notification = NotificationManager(self.config.get("notification", {}).get("config_path"))
        self.task_master_client = TaskMasterMCPClient(self.project_root)
        
        # 진행 상황 추적
        self.progress_state = {
            "initialized_at": datetime.now().isoformat(),
            "current_task": None,
            "current_subtask": None,
            "completed_tasks": [],
            "failed_tasks": [],
            "task_history": []
        }
        
        # Task Master MCP 확인 플래그
        self.task_master_checked = False
        
        logger.info("Enhanced Task Orchestrator 초기화 완료")
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """설정 파일 로드"""
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            logger.warning(f"설정 파일을 찾을 수 없습니다: {config_path}")
            return {}
            
    def check_task_master_progress(self):
        """Task Master MCP를 통해 현재 개발 진행 상황 확인"""
        if self.task_master_checked:
            logger.info("Task Master 진행 상황은 이미 확인되었습니다.")
            return
            
        logger.info("Task Master MCP를 통해 개발 진행 상황을 확인합니다...")
        
        # Task Master MCP 확인 프롬프트 생성
        prompt = self.task_master_client.create_mcp_prompt()
        
        # Claude에 프롬프트 전송
        logger.info("Claude Desktop에 Task Master MCP 확인 요청을 전송합니다...")
        project_name = self.config.get("dev_project_name", "default")
        if self.claude.run_automation(prompt, wait_for_continue=True, create_new_chat=True, project_name=project_name):
            logger.info("Task Master MCP 확인 요청 전송 완료")
            
            # 응답 대기 (실제로는 Claude의 응답을 파싱해야 하지만, 현재는 시뮬레이션)
            time.sleep(5)  # Claude가 응답할 시간을 줌
            
            # TODO: 실제로는 Claude의 응답을 캡처하고 파싱해야 함
            # 현재는 예시 데이터로 시뮬레이션
            mock_response = {
                "current_task": {"id": "1", "name": "샘플 태스크", "status": "in_progress"},
                "current_subtask": {"id": "1", "name": "샘플 서브태스크 1", "status": "pending"},
                "completed_tasks": [],
                "pending_tasks": [{"id": "1", "name": "샘플 태스크"}],
                "progress_percentage": 0
            }
            
            # 진행 상황 저장
            self.task_master_client.save_progress_state(mock_response)
            
            # 내부 상태 업데이트
            self.update_progress_from_task_master(mock_response)
            
            self.task_master_checked = True
            logger.info("Task Master MCP 진행 상황 확인 완료")
        else:
            logger.error("Task Master MCP 확인 요청 실패")
            
    def update_progress_from_task_master(self, progress_data: Dict[str, Any]):
        """Task Master에서 받은 진행 상황으로 내부 상태 업데이트"""
        if progress_data:
            if progress_data.get("current_task"):
                self.progress_state["current_task"] = progress_data["current_task"]
            if progress_data.get("current_subtask"):
                self.progress_state["current_subtask"] = progress_data["current_subtask"]
            if progress_data.get("completed_tasks"):
                self.progress_state["completed_tasks"] = progress_data["completed_tasks"]
                
            # 진행 상황 저장
            self.save_progress_state()
            
    def save_progress_state(self):
        """현재 진행 상황을 파일로 저장"""
        progress_file = Path(self.project_root) / "logs" / "orchestrator_progress.json"
        progress_file.parent.mkdir(exist_ok=True)
        
        try:
            # 타임스탬프 추가
            self.progress_state["last_updated"] = datetime.now().isoformat()
            
            with open(progress_file, 'w') as f:
                json.dump(self.progress_state, f, indent=2)
                
            logger.info(f"진행 상황 저장 완료: {progress_file}")
        except Exception as e:
            logger.error(f"진행 상황 저장 실패: {e}")
            
    def load_progress_state(self):
        """저장된 진행 상황 로드"""
        progress_file = Path(self.project_root) / "logs" / "orchestrator_progress.json"
        
        if progress_file.exists():
            try:
                with open(progress_file, 'r') as f:
                    loaded_state = json.load(f)
                    self.progress_state.update(loaded_state)
                    logger.info("이전 진행 상황을 로드했습니다.")
            except Exception as e:
                logger.error(f"진행 상황 로드 실패: {e}")
                
    def process_task_with_mcp(self, task_id: str, subtask_id: Optional[str] = None):
        """Task Master MCP를 활용하여 태스크 처리"""
        logger.info(f"태스크 처리 시작: task_id={task_id}, subtask_id={subtask_id}")
        
        # 진행 상황 업데이트
        self.progress_state["current_task"] = {"id": task_id, "started_at": datetime.now().isoformat()}
        if subtask_id:
            self.progress_state["current_subtask"] = {"id": subtask_id, "started_at": datetime.now().isoformat()}
        self.save_progress_state()
        
        # Task Master MCP를 통한 태스크 구현 프롬프트 생성
        prompt = self.task_master_client.create_task_prompt(task_id, subtask_id)
        
        # Claude에 프롬프트 전송
        logger.info("Claude Desktop에 태스크 구현 요청을 전송합니다...")
        project_name = self.config.get("dev_project_name", "default")
        if self.claude.run_automation(prompt, wait_for_continue=True, project_name=project_name):
            logger.info("태스크 구현 요청 전송 완료")
            
            # 구현 완료 대기
            time.sleep(10)  # 실제로는 더 정교한 대기 로직 필요
            
            # 테스트 실행 (개발 프로젝트에서)
            if self.run_tests_in_dev_project():
                logger.info("테스트 성공!")
                
                # 코드 품질 검사
                if self.config.get("check_quality_after_tests", True):
                    self.check_code_quality()
                    
                # Git 커밋
                if self.config.get("auto_commit_after_subtask", True):
                    self.commit_changes(task_id, subtask_id)
                    
                # 진행 상황 업데이트
                task_info = {"id": task_id, "completed_at": datetime.now().isoformat()}
                if subtask_id:
                    task_info["subtask_id"] = subtask_id
                self.progress_state["completed_tasks"].append(task_info)
                self.progress_state["task_history"].append({
                    "action": "completed",
                    "task": task_info,
                    "timestamp": datetime.now().isoformat()
                })
                self.save_progress_state()
                
                # 완료 알림
                self.notification.notify_task_completion(task_id, f"Task {task_id}" + (f" Subtask {subtask_id}" if subtask_id else ""))
                
                return True
            else:
                logger.error("테스트 실패!")
                
                # 실패 기록
                task_info = {"id": task_id, "failed_at": datetime.now().isoformat(), "reason": "test_failure"}
                if subtask_id:
                    task_info["subtask_id"] = subtask_id
                self.progress_state["failed_tasks"].append(task_info)
                self.progress_state["task_history"].append({
                    "action": "failed",
                    "task": task_info,
                    "timestamp": datetime.now().isoformat()
                })
                self.save_progress_state()
                
                # 실패 알림
                self.notification.notify_subtask_failure(
                    task_id, f"Task {task_id}",
                    subtask_id or "main", f"Subtask {subtask_id}" if subtask_id else "Main task",
                    1, "테스트 실패"
                )
                
                return False
        else:
            logger.error("태스크 구현 요청 실패")
            return False
            
    def run_tests_in_dev_project(self) -> bool:
        """개발 프로젝트에서 테스트 실행"""
        if not self.config.get("dev_project_path"):
            logger.warning("개발 프로젝트 경로가 설정되지 않았습니다.")
            return False
            
        dev_path = Path(self.config["dev_project_path"])
        project_type = self.config.get("project_type", "gradle")
        
        if project_type == "gradle":
            # Gradle 프로젝트 테스트 실행
            test_command = ["gradlew.bat" if platform.system() == "Windows" else "./gradlew", "test"]
            
            try:
                logger.info(f"테스트 실행: {' '.join(test_command)}")
                result = subprocess.run(
                    test_command,
                    cwd=dev_path,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5분 타임아웃
                )
                
                if result.returncode == 0:
                    logger.info("테스트 성공!")
                    return True
                else:
                    logger.error(f"테스트 실패: {result.stderr}")
                    return False
                    
            except subprocess.TimeoutExpired:
                logger.error("테스트 실행 타임아웃")
                return False
            except Exception as e:
                logger.error(f"테스트 실행 중 오류: {e}")
                return False
        else:
            logger.warning(f"지원되지 않는 프로젝트 타입: {project_type}")
            return False
            
    def check_code_quality(self):
        """코드 품질 검사"""
        if not self.config.get("dev_project_path"):
            return
            
        dev_path = Path(self.config["dev_project_path"])
        src_dir = dev_path / self.config.get("src_dir", "src")
        
        if src_dir.exists():
            logger.info("코드 품질 검사 시작...")
            analysis_result = self.code_analyzer.analyze_project(str(src_dir))
            
            if analysis_result["total_mocks"] > 0 or analysis_result["total_commented_code"] > 0:
                logger.warning("코드 품질 문제 발견!")
                self.notification.notify_mock_detection(analysis_result)
            else:
                logger.info("코드 품질 검사 통과")
                
    def commit_changes(self, task_id: str, subtask_id: Optional[str] = None):
        """Git 커밋 수행"""
        if not self.config.get("git_enabled", False):
            return
            
        dev_path = Path(self.config.get("dev_project_path", "."))
        
        try:
            # Git add
            subprocess.run(["git", "add", "."], cwd=dev_path, check=True)
            
            # 커밋 메시지 생성
            commit_message = f"Task {task_id}"
            if subtask_id:
                commit_message += f" Subtask {subtask_id}"
            commit_message += " 구현 완료"
            
            # Git commit
            subprocess.run(["git", "commit", "-m", commit_message], cwd=dev_path, check=True)
            
            logger.info(f"Git 커밋 완료: {commit_message}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git 커밋 실패: {e}")
            
    def run(self):
        """오케스트레이터 실행"""
        logger.info("Enhanced Task Orchestrator 시작")
        
        # 이전 진행 상황 로드
        self.load_progress_state()
        
        # Task Master MCP를 통해 현재 진행 상황 확인
        self.check_task_master_progress()
        
        # 태스크 파일 로드
        task_file = Path(self.project_root) / self.config.get("task_definition_file", "tasks.json")
        if not task_file.exists():
            logger.error(f"태스크 파일을 찾을 수 없습니다: {task_file}")
            return
            
        with open(task_file, 'r') as f:
            tasks_data = json.load(f)
            
        # 태스크 처리
        tasks = tasks_data.get("tasks", [])
        for task in tasks:
            task_id = task.get("id")
            
            # 이미 완료된 태스크인지 확인
            if any(t.get("id") == task_id for t in self.progress_state.get("completed_tasks", [])):
                logger.info(f"태스크 {task_id}는 이미 완료되었습니다. 건너뜁니다.")
                continue
                
            # 태스크 처리
            if task.get("subtasks"):
                # 서브태스크가 있는 경우
                for subtask in task["subtasks"]:
                    subtask_id = subtask.get("id")
                    
                    # 이미 완료된 서브태스크인지 확인
                    if any(
                        t.get("id") == task_id and t.get("subtask_id") == subtask_id
                        for t in self.progress_state.get("completed_tasks", [])
                    ):
                        logger.info(f"서브태스크 {task_id}.{subtask_id}는 이미 완료되었습니다. 건너뜁니다.")
                        continue
                        
                    # 서브태스크 처리
                    if not self.process_task_with_mcp(task_id, subtask_id):
                        logger.error(f"서브태스크 {task_id}.{subtask_id} 처리 실패")
                        # 실패해도 계속 진행 (설정에 따라 변경 가능)
            else:
                # 서브태스크가 없는 경우
                if not self.process_task_with_mcp(task_id):
                    logger.error(f"태스크 {task_id} 처리 실패")
                    
        logger.info("모든 태스크 처리 완료")
        
        # 최종 진행 상황 요약
        self.print_progress_summary()
        
    def print_progress_summary(self):
        """진행 상황 요약 출력"""
        logger.info("=" * 50)
        logger.info("진행 상황 요약")
        logger.info("=" * 50)
        logger.info(f"완료된 태스크: {len(self.progress_state.get('completed_tasks', []))}")
        logger.info(f"실패한 태스크: {len(self.progress_state.get('failed_tasks', []))}")
        
        if self.progress_state.get('completed_tasks'):
            logger.info("\n완료된 태스크 목록:")
            for task in self.progress_state['completed_tasks']:
                logger.info(f"  - {task}")
                
        if self.progress_state.get('failed_tasks'):
            logger.info("\n실패한 태스크 목록:")
            for task in self.progress_state['failed_tasks']:
                logger.info(f"  - {task}")
                
        logger.info("=" * 50)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='Enhanced Task Orchestrator with Task Master MCP')
    parser.add_argument('--config', type=str, default='config.json', help='설정 파일 경로')
    parser.add_argument('--task', type=str, help='특정 태스크만 실행')
    parser.add_argument('--subtask', type=str, help='특정 서브태스크만 실행')
    parser.add_argument('--check-progress', action='store_true', help='진행 상황만 확인')
    
    args = parser.parse_args()
    
    # 오케스트레이터 생성
    orchestrator = EnhancedTaskOrchestrator(args.config)
    
    if args.check_progress:
        # 진행 상황만 확인
        orchestrator.check_task_master_progress()
        orchestrator.print_progress_summary()
    elif args.task:
        # 특정 태스크만 실행
        orchestrator.process_task_with_mcp(args.task, args.subtask)
    else:
        # 전체 실행
        orchestrator.run()


if __name__ == "__main__":
    main()
