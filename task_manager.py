"""
Task Manager - Task Master 스타일의 task 관리 기능
"""
import json
import os
import logging
from typing import List, Dict, Optional, Union
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class TaskManager:
    def __init__(self, tasks_file="tasks.json"):
        self.tasks_file = tasks_file
        self.tasks_data = self._load_tasks()
        
    def _load_tasks(self) -> Dict:
        """tasks.json 파일 로드"""
        if not os.path.exists(self.tasks_file):
            return {"tasks": [], "metadata": {"last_updated": None, "version": "1.0"}}
        
        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load tasks: {e}")
            return {"tasks": [], "metadata": {}}
    
    def _save_tasks(self) -> bool:
        """tasks.json 파일 저장"""
        try:
            self.tasks_data["metadata"]["last_updated"] = datetime.now().isoformat()
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(self.tasks_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save tasks: {e}")
            return False
    
    def list_tasks(self, status: Optional[str] = None, with_subtasks: bool = True) -> List[Dict]:
        """모든 task 목록 반환"""
        tasks = self.tasks_data.get("tasks", [])
        
        if status:
            tasks = [t for t in tasks if t.get("status") == status]
        
        if not with_subtasks:
            # subtask 제외
            for task in tasks:
                task_copy = task.copy()
                task_copy.pop("subtasks", None)
                yield task_copy
        else:
            return tasks
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """특정 task 가져오기"""
        for task in self.tasks_data.get("tasks", []):
            if str(task.get("id")) == str(task_id):
                return task
            # subtask 검색
            for subtask in task.get("subtasks", []):
                if f"{task['id']}.{subtask['id']}" == task_id:
                    return subtask
        return None
    
    def get_next_task(self) -> Optional[Dict]:
        """다음으로 수행할 task 찾기 (의존성 고려)"""
        tasks = self.tasks_data.get("tasks", [])
        
        for task in tasks:
            if task.get("status") != "pending":
                continue
                
            # 의존성 확인
            dependencies = task.get("dependencies", [])
            if dependencies:
                all_deps_completed = True
                for dep_id in dependencies:
                    dep_task = self.get_task(str(dep_id))
                    if not dep_task or dep_task.get("status") != "done":
                        all_deps_completed = False
                        break
                
                if not all_deps_completed:
                    continue
            
            # 우선순위 고려
            return task
        
        return None
    
    def set_task_status(self, task_id: str, status: str) -> bool:
        """task 상태 변경"""
        valid_statuses = ["pending", "in-progress", "done", "review", "deferred", "cancelled"]
        if status not in valid_statuses:
            logger.error(f"Invalid status: {status}")
            return False
        
        task = self._find_task_for_update(task_id)
        if task:
            task["status"] = status
            task["updated_at"] = datetime.now().isoformat()
            return self._save_tasks()
        
        return False
    
    def _find_task_for_update(self, task_id: str) -> Optional[Dict]:
        """업데이트를 위한 task 찾기 (참조 반환)"""
        for task in self.tasks_data.get("tasks", []):
            if str(task.get("id")) == str(task_id):
                return task
            # subtask 검색
            for subtask in task.get("subtasks", []):
                if f"{task['id']}.{subtask['id']}" == task_id:
                    return subtask
        return None
    
    def add_task(self, title: str, description: str, 
                 dependencies: Optional[List[str]] = None,
                 priority: str = "medium") -> Optional[str]:
        """새 task 추가"""
        tasks = self.tasks_data.get("tasks", [])
        
        # 새 ID 생성
        max_id = 0
        for task in tasks:
            task_id = int(task.get("id", 0))
            if task_id > max_id:
                max_id = task_id
        
        new_id = str(max_id + 1)
        
        new_task = {
            "id": new_id,
            "title": title,
            "description": description,
            "status": "pending",
            "priority": priority,
            "dependencies": dependencies or [],
            "created_at": datetime.now().isoformat(),
            "subtasks": []
        }
        
        tasks.append(new_task)
        self.tasks_data["tasks"] = tasks
        
        if self._save_tasks():
            return new_id
        return None
    
    def add_subtask(self, parent_id: str, title: str, description: str) -> Optional[str]:
        """subtask 추가"""
        parent_task = self._find_task_for_update(parent_id)
        if not parent_task:
            logger.error(f"Parent task {parent_id} not found")
            return None
        
        subtasks = parent_task.get("subtasks", [])
        
        # 새 subtask ID 생성
        max_id = 0
        for subtask in subtasks:
            subtask_id = int(subtask.get("id", 0))
            if subtask_id > max_id:
                max_id = subtask_id
        
        new_subtask_id = str(max_id + 1)
        
        new_subtask = {
            "id": new_subtask_id,
            "title": title,
            "description": description,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        subtasks.append(new_subtask)
        parent_task["subtasks"] = subtasks
        
        if self._save_tasks():
            return f"{parent_id}.{new_subtask_id}"
        return None
    
    def move_task(self, from_id: str, to_id: str) -> bool:
        """task 이동/재구성"""
        # from_id와 to_id 파싱
        from_parts = from_id.split('.')
        to_parts = to_id.split('.')
        
        # 구현 예정: Task Master의 move 로직
        logger.info(f"Moving task from {from_id} to {to_id}")
        # TODO: 구현
        return False
    
    def update_tasks(self, from_id: int, prompt: str, use_ai: bool = True) -> bool:
        """특정 ID부터의 모든 task 업데이트"""
        tasks = self.tasks_data.get("tasks", [])
        updated_count = 0
        
        for task in tasks:
            if int(task.get("id", 0)) >= from_id:
                # AI를 사용한 업데이트 또는 수동 업데이트
                if use_ai:
                    # TODO: AI 모델을 사용한 task 업데이트
                    logger.info(f"Updating task {task['id']} with AI prompt: {prompt}")
                else:
                    task["description"] += f"\n\n[Updated]: {prompt}"
                    task["updated_at"] = datetime.now().isoformat()
                
                updated_count += 1
        
        if updated_count > 0:
            self._save_tasks()
            logger.info(f"Updated {updated_count} tasks")
            return True
        
        return False
    
    def expand_task(self, task_id: str, num_subtasks: int = 3, 
                    prompt: Optional[str] = None, use_ai: bool = True) -> bool:
        """task를 subtask로 확장"""
        task = self._find_task_for_update(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return False
        
        if use_ai:
            # TODO: AI를 사용한 subtask 생성
            logger.info(f"Expanding task {task_id} with AI")
        else:
            # 기본 subtask 생성
            for i in range(1, num_subtasks + 1):
                self.add_subtask(
                    task_id,
                    f"Subtask {i} for {task['title']}",
                    f"Implementation details for subtask {i}"
                )
        
        return True
    
    def analyze_complexity(self, threshold: int = 5) -> Dict:
        """task 복잡도 분석"""
        analysis = {
            "total_tasks": 0,
            "complex_tasks": [],
            "simple_tasks": [],
            "recommendations": []
        }
        
        tasks = self.tasks_data.get("tasks", [])
        
        for task in tasks:
            complexity_score = self._calculate_complexity(task)
            analysis["total_tasks"] += 1
            
            if complexity_score >= threshold:
                analysis["complex_tasks"].append({
                    "id": task["id"],
                    "title": task["title"],
                    "score": complexity_score,
                    "reasons": self._get_complexity_reasons(task)
                })
                analysis["recommendations"].append(
                    f"Task {task['id']} should be broken down into subtasks"
                )
            else:
                analysis["simple_tasks"].append({
                    "id": task["id"],
                    "title": task["title"],
                    "score": complexity_score
                })
        
        return analysis
    
    def _calculate_complexity(self, task: Dict) -> int:
        """task 복잡도 계산"""
        score = 0
        
        # 설명 길이
        description_length = len(task.get("description", ""))
        if description_length > 500:
            score += 3
        elif description_length > 200:
            score += 2
        elif description_length > 100:
            score += 1
        
        # 의존성 수
        dependencies = len(task.get("dependencies", []))
        score += dependencies
        
        # 기술 스택 언급 수
        tech_keywords = ["API", "database", "authentication", "integration", 
                        "migration", "security", "performance", "architecture"]
        description = task.get("description", "").lower()
        for keyword in tech_keywords:
            if keyword in description:
                score += 1
        
        # 이미 subtask가 있으면 복잡도 감소
        if task.get("subtasks"):
            score = max(0, score - 2)
        
        return score
    
    def _get_complexity_reasons(self, task: Dict) -> List[str]:
        """복잡도가 높은 이유 분석"""
        reasons = []
        
        if len(task.get("description", "")) > 200:
            reasons.append("Long description indicates complex requirements")
        
        dependencies = len(task.get("dependencies", []))
        if dependencies > 2:
            reasons.append(f"Has {dependencies} dependencies")
        
        if not task.get("subtasks"):
            reasons.append("No subtasks defined")
        
        return reasons