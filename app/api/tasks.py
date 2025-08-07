"""
任务管理API
展示权限装饰器在任务管理中的应用
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user
from app.core.auth_decorators import (
    authenticated_required,
    task_read_required,
    task_create_required,
    task_update_required,
    task_delete_required,
    task_assign_required,
    permission_required
)
from app.core.permissions import Permission
from app.db.database import get_db
from app.models.user import User

router = APIRouter()


# 示例任务模型（简化版）
class TaskResponse:
    def __init__(self, id: int, title: str, description: str, assigned_to: Optional[int] = None, created_by: int = None):
        self.id = id
        self.title = title
        self.description = description
        self.assigned_to = assigned_to
        self.created_by = created_by


class TaskCreate:
    def __init__(self, title: str, description: str, assigned_to: Optional[int] = None):
        self.title = title
        self.description = description
        self.assigned_to = assigned_to


class TaskUpdate:
    def __init__(self, title: Optional[str] = None, description: Optional[str] = None, assigned_to: Optional[int] = None):
        self.title = title
        self.description = description
        self.assigned_to = assigned_to


@router.get("/", response_model=List[dict])
@task_read_required
def read_tasks(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    获取任务列表
    需要任务读取权限
    """
    # 这里应该是实际的数据库查询
    # 示例返回
    return [
        {
            "id": 1,
            "title": "示例任务1",
            "description": "这是一个示例任务",
            "assigned_to": current_user.id,
            "created_by": 1
        }
    ]


@router.post("/", response_model=dict)
@task_create_required
def create_task(
    *,
    db: Session = Depends(get_db),
    task_in: dict,  # 简化为dict，实际应该使用TaskCreate schema
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    创建新任务
    需要任务创建权限
    """
    # 这里应该是实际的任务创建逻辑
    return {
        "id": 2,
        "title": task_in.get("title", "新任务"),
        "description": task_in.get("description", ""),
        "created_by": current_user.id,
        "message": "Task created successfully"
    }


@router.get("/{task_id}", response_model=dict)
@permission_required(Permission.READ_TASKS, allow_self_access=True, self_param="task_id")
def read_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    获取特定任务
    需要任务读取权限，或者是任务的创建者/被分配者
    """
    # 这里应该检查任务是否存在，以及用户是否有权限访问
    return {
        "id": task_id,
        "title": f"任务 {task_id}",
        "description": "任务描述",
        "assigned_to": current_user.id,
        "created_by": current_user.id
    }


@router.put("/{task_id}", response_model=dict)
@task_update_required
def update_task(
    *,
    db: Session = Depends(get_db),
    task_id: int,
    task_in: dict,  # 简化为dict，实际应该使用TaskUpdate schema
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    更新任务
    需要任务更新权限
    """
    # 这里应该是实际的任务更新逻辑
    return {
        "id": task_id,
        "title": task_in.get("title", f"更新的任务 {task_id}"),
        "description": task_in.get("description", "更新的描述"),
        "message": "Task updated successfully"
    }


@router.delete("/{task_id}")
@task_delete_required
def delete_task(
    *,
    db: Session = Depends(get_db),
    task_id: int,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    删除任务
    需要任务删除权限
    """
    # 这里应该是实际的任务删除逻辑
    return {"message": f"Task {task_id} deleted successfully"}


@router.post("/{task_id}/assign", response_model=dict)
@task_assign_required
def assign_task(
    *,
    db: Session = Depends(get_db),
    task_id: int,
    assign_data: dict,  # 应该包含 user_id
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    分配任务给用户
    需要任务分配权限
    """
    user_id = assign_data.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID is required"
        )
    
    # 这里应该是实际的任务分配逻辑
    return {
        "task_id": task_id,
        "assigned_to": user_id,
        "assigned_by": current_user.id,
        "message": "Task assigned successfully"
    }


@router.get("/my/tasks", response_model=List[dict])
@authenticated_required
def read_my_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    获取当前用户的任务
    只需要认证，不需要特殊权限
    """
    # 这里应该查询当前用户创建或被分配的任务
    return [
        {
            "id": 1,
            "title": "我的任务1",
            "description": "这是我的任务",
            "assigned_to": current_user.id,
            "created_by": current_user.id
        }
    ]


@router.post("/bulk-assign")
@permission_required([Permission.ASSIGN_TASK, Permission.ADMIN_ACCESS], require_all=False)
def bulk_assign_tasks(
    *,
    db: Session = Depends(get_db),
    assign_data: dict,  # 应该包含 task_ids 和 user_id
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    批量分配任务
    需要任务分配权限或管理员权限
    """
    task_ids = assign_data.get("task_ids", [])
    user_id = assign_data.get("user_id")
    
    if not task_ids or not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task IDs and User ID are required"
        )
    
    # 这里应该是实际的批量分配逻辑
    return {
        "assigned_tasks": task_ids,
        "assigned_to": user_id,
        "assigned_by": current_user.id,
        "message": f"Successfully assigned {len(task_ids)} tasks"
    }