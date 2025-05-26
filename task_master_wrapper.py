#!/usr/bin/env python
"""
Task Master Wrapper - 기존 task-master 명령어와의 호환성을 위한 래퍼
"""

import os
import sys
import json
import argparse
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from task_orchestrator import TaskOrchestrator


class TaskMasterWrapper:
    def __init__(self, config_path="config.json"):
        self.orchestrator = TaskOrchestrator(config_path)
        self.tasks_data = self.orchestrator.tasks_data
    
    def list_tasks(self, filter_status=None, show_details=False):
        """태스크 목록을 표시합니다."""
        print("\n=== 태스크 목록 ===\n")
        
        if not self.tasks_data.get("tasks"):
            print("등록된 태스크가 없습니다.")
            return
        
        for task in self.tasks_data["tasks"]:
            if filter_status and task.get("status") != filter_status:
                continue
                
            status_emoji = {
                "pending": "⏳",
                "in_progress": "🔄",
                "completed": "✅",
                "failed": "❌"
            }.get(task.get("status", "pending"), "❓")
            
            print(f"{status_emoji} [{task['id']}] {task.get('name', 'Unnamed Task')}")
            print(f"   상태: {task.get('status', 'pending')}")
            
            if show_details and task.get("description"):
                print(f"   설명: {task['description']}")
            
            # 서브태스크 정보
            subtasks = task.get("subtasks", [])
            if subtasks:
                completed_subtasks = sum(1 for st in subtasks if st.get("status") == "completed")
                print(f"   서브태스크: {completed_subtasks}/{len(subtasks)} 완료")
                
                if show_details:
                    for subtask in subtasks:
                        st_emoji = {
                            "pending": "  ⏳",
                            "in_progress": "  🔄",
                            "completed": "  ✅",
                            "failed": "  ❌"
                        }.get(subtask.get("status", "pending"), "  ❓")
                        print(f"     {st_emoji} [{subtask['id']}] {subtask.get('name', 'Unnamed Subtask')}")
            
            # 시작/완료 시간
            if task.get("started_at"):
                print(f"   시작: {task['started_at']}")
            if task.get("completed_at"):
                print(f"   완료: {task['completed_at']}")
                
            print()  # 빈 줄
    
    def show_status(self):
        """프로젝트 진행 상황을 요약합니다."""
        print("\n=== 프로젝트 진행 상황 ===\n")
        
        total_tasks = len(self.tasks_data.get("tasks", []))
        if total_tasks == 0:
            print("등록된 태스크가 없습니다.")
            return
        
        # 태스크 상태별 집계
        status_counts = {
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "failed": 0
        }
        
        total_subtasks = 0
        completed_subtasks = 0
        
        for task in self.tasks_data["tasks"]:
            status = task.get("status", "pending")
            status_counts[status] = status_counts.get(status, 0) + 1
            
            subtasks = task.get("subtasks", [])
            total_subtasks += len(subtasks)
            completed_subtasks += sum(1 for st in subtasks if st.get("status") == "completed")
        
        # 진행률 계산
        completed_tasks = status_counts["completed"]
        task_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        subtask_progress = (completed_subtasks / total_subtasks * 100) if total_subtasks > 0 else 0
        
        print(f"총 태스크: {total_tasks}")
        print(f"  - 대기중: {status_counts['pending']}")
        print(f"  - 진행중: {status_counts['in_progress']}")
        print(f"  - 완료: {status_counts['completed']}")
        print(f"  - 실패: {status_counts['failed']}")
        print(f"\n태스크 진행률: {task_progress:.1f}%")
        print(f"서브태스크 진행률: {subtask_progress:.1f}% ({completed_subtasks}/{total_subtasks})")
        
        # 테스트 이력 정보
        test_history_file = os.path.join("logs", "test_history.json")
        if os.path.exists(test_history_file):
            try:
                with open(test_history_file, 'r') as f:
                    test_history = json.load(f)
                    
                print(f"\n테스트 실행 통계:")
                print(f"  - 총 실행: {test_history.get('total_runs', 0)}회")
                print(f"  - 성공: {test_history.get('total_passes', 0)}회")
                print(f"  - 실패: {test_history.get('total_failures', 0)}회")
                
                if test_history.get('last_run'):
                    last_run = datetime.fromtimestamp(test_history['last_run'])
                    print(f"  - 마지막 실행: {last_run.strftime('%Y-%m-%d %H:%M:%S')}")
            except Exception as e:
                pass
    
    def reset_task(self, task_id=None, subtask_id=None):
        """태스크 또는 서브태스크의 상태를 초기화합니다."""
        if task_id:
            task = self.orchestrator.get_task_by_id(task_id)
            if not task:
                print(f"태스크 '{task_id}'를 찾을 수 없습니다.")
                return False
                
            if subtask_id:
                subtask = self.orchestrator.get_subtask_by_id(task, subtask_id)
                if not subtask:
                    print(f"서브태스크 '{subtask_id}'를 찾을 수 없습니다.")
                    return False
                    
                subtask["status"] = "pending"
                subtask["failure_count"] = 0
                print(f"서브태스크 '{subtask.get('name', subtask_id)}' 상태를 초기화했습니다.")
            else:
                task["status"] = "pending"
                task["failure_count"] = 0
                task.pop("started_at", None)
                task.pop("completed_at", None)
                
                # 모든 서브태스크도 초기화
                for subtask in task.get("subtasks", []):
                    subtask["status"] = "pending"
                    subtask["failure_count"] = 0
                    
                print(f"태스크 '{task.get('name', task_id)}' 상태를 초기화했습니다.")
        else:
            # 모든 태스크 초기화
            for task in self.tasks_data["tasks"]:
                task["status"] = "pending"
                task["failure_count"] = 0
                task.pop("started_at", None)
                task.pop("completed_at", None)
                
                for subtask in task.get("subtasks", []):
                    subtask["status"] = "pending"
                    subtask["failure_count"] = 0
                    
            print("모든 태스크 상태를 초기화했습니다.")
        
        self.orchestrator._save_tasks_data()
        return True


def main():
    parser = argparse.ArgumentParser(
        description='Task Master - AI 자동화 프로젝트 관리 도구',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python task_master_wrapper.py list              # 모든 태스크 목록 표시
  python task_master_wrapper.py list --status pending  # 대기중인 태스크만 표시
  python task_master_wrapper.py list --details    # 상세 정보 포함
  python task_master_wrapper.py status            # 프로젝트 진행 상황 요약
  python task_master_wrapper.py reset             # 모든 태스크 상태 초기화
  python task_master_wrapper.py reset --task task-1  # 특정 태스크 초기화
  python task_master_wrapper.py run               # 태스크 실행 (task_orchestrator.py 호출)
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='사용 가능한 명령어')
    
    # list 명령어
    list_parser = subparsers.add_parser('list', help='태스크 목록 표시')
    list_parser.add_argument('--status', choices=['pending', 'in_progress', 'completed', 'failed'],
                           help='특정 상태의 태스크만 표시')
    list_parser.add_argument('--details', '-d', action='store_true',
                           help='상세 정보 표시')
    
    # status 명령어
    status_parser = subparsers.add_parser('status', help='프로젝트 진행 상황 요약')
    
    # reset 명령어
    reset_parser = subparsers.add_parser('reset', help='태스크 상태 초기화')
    reset_parser.add_argument('--task', '-t', help='초기화할 태스크 ID')
    reset_parser.add_argument('--subtask', '-s', help='초기화할 서브태스크 ID')
    
    # run 명령어
    run_parser = subparsers.add_parser('run', help='태스크 실행')
    run_parser.add_argument('--task', '-t', help='실행할 태스크 ID')
    run_parser.add_argument('--subtask', '-s', help='실행할 서브태스크 ID')
    
    # 설정 파일 옵션 (모든 명령어에 공통)
    parser.add_argument('--config', '-c', default='config.json',
                       help='설정 파일 경로 (기본값: config.json)')
    
    args = parser.parse_args()
    
    # 명령어가 없으면 status 표시
    if not args.command:
        args.command = 'status'
    
    # TaskMasterWrapper 초기화
    wrapper = TaskMasterWrapper(args.config)
    
    # 명령어 실행
    if args.command == 'list':
        wrapper.list_tasks(filter_status=args.status, show_details=args.details)
    
    elif args.command == 'status':
        wrapper.show_status()
    
    elif args.command == 'reset':
        wrapper.reset_task(task_id=args.task, subtask_id=args.subtask)
    
    elif args.command == 'run':
        # task_orchestrator.py 실행
        from task_orchestrator import main as orchestrator_main
        sys.argv = ['task_orchestrator.py', '--config', args.config]
        if args.task:
            sys.argv.extend(['--task', args.task])
        if args.subtask:
            sys.argv.extend(['--subtask', args.subtask])
        orchestrator_main()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()