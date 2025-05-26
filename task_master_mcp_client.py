"""
Task Master MCP Client
Claude Desktop과 Task Master를 연동하기 위한 MCP 클라이언트 모듈
"""

import os
import json
import logging
import asyncio
import subprocess
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class TaskMasterMCPClient:
    """Task Master MCP 클라이언트"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).absolute()
        self.dev_project_path = None
        self.dev_project_name = None
        self._load_config()
        
    def _load_config(self):
        """설정 파일 로드"""
        config_path = self.project_root / "config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.dev_project_path = config.get('dev_project_path')
                self.dev_project_name = config.get('dev_project_name')
                
    def create_mcp_prompt(self) -> str:
        """Task Master MCP를 통해 현재 개발 상황을 확인하는 프롬프트 생성"""
        if not self.dev_project_path:
            return "Task Master MCP 설정이 없습니다. 개발 프로젝트 경로를 설정해주세요."
            
        prompt = f"""Task Master MCP를 사용하여 현재 개발 진행 상황을 확인해주세요.

프로젝트 경로: {self.dev_project_path}
프로젝트 이름: {self.dev_project_name}

다음 정보를 확인해주세요:
1. 현재 진행 중인 태스크 ID와 이름
2. 현재 진행 중인 서브태스크 ID와 이름
3. 완료된 태스크/서브태스크 목록
4. 남은 태스크/서브태스크 목록
5. 전체 진행률

MCP 명령어 예시:
- get_tasks 명령으로 전체 태스크 목록 확인
- get_task --id [task_id] 명령으로 특정 태스크 상세 정보 확인
- next_task 명령으로 다음에 작업할 태스크 확인

확인 후 JSON 형식으로 결과를 알려주세요:
{{
    "current_task": {{"id": "...", "name": "...", "status": "..."}},
    "current_subtask": {{"id": "...", "name": "...", "status": "..."}},
    "completed_tasks": [...],
    "pending_tasks": [...],
    "progress_percentage": ...
}}
"""
        return prompt
        
    def parse_mcp_response(self, response: str) -> Optional[Dict[str, Any]]:
        """MCP 응답을 파싱하여 진행 상황 정보 추출"""
        try:
            # JSON 블록 찾기
            import re
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, response, re.DOTALL)
            
            for match in matches:
                try:
                    data = json.loads(match)
                    if 'current_task' in data:
                        return data
                except json.JSONDecodeError:
                    continue
                    
            logger.warning("MCP 응답에서 유효한 JSON을 찾을 수 없습니다.")
            return None
            
        except Exception as e:
            logger.error(f"MCP 응답 파싱 중 오류: {e}")
            return None
            
    def save_progress_state(self, progress_data: Dict[str, Any]):
        """진행 상황을 파일로 저장"""
        progress_file = self.project_root / "logs" / "task_progress_state.json"
        progress_file.parent.mkdir(exist_ok=True)
        
        try:
            # 기존 상태 로드
            if progress_file.exists():
                with open(progress_file, 'r') as f:
                    existing_data = json.load(f)
            else:
                existing_data = {"history": []}
                
            # 현재 시간 추가
            import time
            progress_data["timestamp"] = time.time()
            progress_data["timestamp_str"] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 현재 상태 업데이트
            existing_data["current"] = progress_data
            existing_data["history"].append(progress_data)
            
            # 최근 100개 이력만 유지
            if len(existing_data["history"]) > 100:
                existing_data["history"] = existing_data["history"][-100:]
                
            # 저장
            with open(progress_file, 'w') as f:
                json.dump(existing_data, f, indent=2)
                
            logger.info(f"진행 상황 저장 완료: {progress_file}")
            
        except Exception as e:
            logger.error(f"진행 상황 저장 중 오류: {e}")
            
    def load_progress_state(self) -> Optional[Dict[str, Any]]:
        """저장된 진행 상황 로드"""
        progress_file = self.project_root / "logs" / "task_progress_state.json"
        
        if not progress_file.exists():
            return None
            
        try:
            with open(progress_file, 'r') as f:
                data = json.load(f)
                return data.get("current")
        except Exception as e:
            logger.error(f"진행 상황 로드 중 오류: {e}")
            return None
            
    def get_task_file_path(self, task_id: str, subtask_id: Optional[str] = None) -> Optional[Path]:
        """태스크/서브태스크에 해당하는 파일 경로 반환"""
        if not self.dev_project_path:
            return None
            
        dev_path = Path(self.dev_project_path)
        task_files_dir = dev_path / "tasks"
        
        if not task_files_dir.exists():
            logger.warning(f"태스크 파일 디렉토리가 없습니다: {task_files_dir}")
            return None
            
        # 서브태스크 파일 찾기
        if subtask_id:
            subtask_file = task_files_dir / f"subtask_{task_id}_{subtask_id}.txt"
            if subtask_file.exists():
                return subtask_file
                
        # 태스크 파일 찾기
        task_file = task_files_dir / f"task_{task_id}.txt"
        if task_file.exists():
            return task_file
            
        # 숫자 ID로도 시도
        if task_id.isdigit():
            task_file = task_files_dir / f"task_{int(task_id):03d}.txt"
            if task_file.exists():
                return task_file
                
        logger.warning(f"태스크 파일을 찾을 수 없습니다: task_id={task_id}, subtask_id={subtask_id}")
        return None
        
    def create_task_prompt(self, task_id: str, subtask_id: Optional[str] = None) -> str:
        """태스크/서브태스크 구현을 위한 프롬프트 생성"""
        task_file = self.get_task_file_path(task_id, subtask_id)
        
        if not task_file:
            return f"태스크 파일을 찾을 수 없습니다: task_id={task_id}, subtask_id={subtask_id}"
            
        # MCP를 통해 파일을 읽도록 프롬프트 생성
        file_path_in_project = str(task_file.relative_to(Path(self.dev_project_path)))
        
        prompt = f"""JetBrains MCP를 사용하여 다음 태스크를 구현해주세요.

프로젝트 경로: {self.dev_project_path}
태스크 파일: {file_path_in_project}

1. 먼저 get_file_text_by_path 명령으로 태스크 파일 내용을 읽어주세요.
2. 태스크 내용을 분석하고 구현 계획을 세워주세요.
3. 필요한 파일들을 생성하거나 수정해주세요.
4. 테스트 코드도 함께 작성해주세요.
5. 구현이 완료되면 테스트를 실행해주세요.

주의사항:
- 프로젝트 구조와 아키텍처를 준수해주세요.
- 코드 품질과 가독성을 고려해주세요.
- 모든 public 메서드에는 JavaDoc을 작성해주세요.
- 단위 테스트 커버리지는 80% 이상을 목표로 해주세요.
"""
        
        return prompt
