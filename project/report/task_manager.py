"""
异步任务管理模块
使用内存存储任务状态，支持后台线程执行报告生成
"""
import threading
import uuid
from datetime import datetime
from typing import Dict, Optional

class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        self.tasks = {}  # {task_id: task_info}
        self.lock = threading.Lock()
    
    def create_task(self, task_type: str, params: Dict) -> str:
        """创建新任务"""
        task_id = str(uuid.uuid4())
        
        with self.lock:
            self.tasks[task_id] = {
                'task_id': task_id,
                'task_type': task_type,
                'status': 'pending',  # pending, processing, completed, failed
                'params': params,
                'result': None,
                'error': None,
                'progress': 0,
                'message': '任务已创建',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        
        return task_id
    
    def update_task(self, task_id: str, status: str = None, progress: int = None, 
                   message: str = None, result: Dict = None, error: str = None):
        """更新任务状态"""
        with self.lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            
            if status:
                task['status'] = status
            if progress is not None:
                task['progress'] = progress
            if message:
                task['message'] = message
            if result:
                task['result'] = result
            if error:
                task['error'] = error
            
            task['updated_at'] = datetime.now().isoformat()
        
        return True
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务信息"""
        with self.lock:
            return self.tasks.get(task_id)
    
    def delete_task(self, task_id: str):
        """删除任务"""
        with self.lock:
            if task_id in self.tasks:
                del self.tasks[task_id]

# 全局任务管理器实例
task_manager = TaskManager()
