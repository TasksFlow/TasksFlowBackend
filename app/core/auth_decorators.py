"""
FastAPI权限装饰器
专门为FastAPI路由设计的权限控制装饰器
"""
from functools import wraps
from typing import Callable, List, Union, Any
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user, get_db
from app.core.permissions import Permission, PermissionChecker
from app.models.user import User


def permission_required(
    permissions: Union[Permission, List[Permission]],
    require_all: bool = True,
    allow_self_access: bool = False,
    self_param: str = "user_id"
):
    """
    FastAPI权限装饰器
    
    Args:
        permissions: 需要的权限或权限列表
        require_all: 是否需要所有权限
        allow_self_access: 是否允许用户访问自己的资源
        self_param: 用于判断自访问的参数名
    
    Usage:
        @permission_required(Permission.READ_USERS)
        def get_users(...):
            pass
        
        @permission_required([Permission.UPDATE_USER, Permission.DELETE_USER], require_all=False)
        def manage_user(...):
            pass
        
        @permission_required(Permission.UPDATE_USER, allow_self_access=True)
        def update_user(user_id: int, current_user: User = Depends(get_current_active_user)):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 从kwargs中获取current_user
            current_user = kwargs.get('current_user')
            if not current_user:
                # 如果没有在kwargs中找到，尝试从args中找到User类型的参数
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # 检查自访问权限
            if allow_self_access and self_param in kwargs:
                target_user_id = kwargs[self_param]
                if current_user.id == target_user_id:
                    return func(*args, **kwargs)
            
            # 检查权限
            perm_list = permissions if isinstance(permissions, list) else [permissions]
            
            if require_all:
                has_access = PermissionChecker.has_all_permissions(current_user, perm_list)
            else:
                has_access = PermissionChecker.has_any_permission(current_user, perm_list)
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def admin_required(func: Callable) -> Callable:
    """管理员权限装饰器"""
    return permission_required(Permission.ADMIN_ACCESS)(func)


def authenticated_required(func: Callable) -> Callable:
    """认证装饰器（只需要登录）"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        current_user = kwargs.get('current_user')
        if not current_user:
            for arg in args:
                if isinstance(arg, User):
                    current_user = arg
                    break
        
        if not current_user or not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        return func(*args, **kwargs)
    
    return wrapper


def self_or_admin_required(self_param: str = "user_id"):
    """要求是本人或管理员才能访问"""
    return permission_required(
        Permission.ADMIN_ACCESS,
        allow_self_access=True,
        self_param=self_param
    )


# 预定义的权限装饰器
user_read_required = permission_required(Permission.READ_USERS)
user_create_required = permission_required(Permission.CREATE_USER)
user_update_required = permission_required(Permission.UPDATE_USER)
user_delete_required = permission_required(Permission.DELETE_USER)
password_reset_required = permission_required(Permission.RESET_PASSWORD)

task_read_required = permission_required(Permission.READ_TASKS)
task_create_required = permission_required(Permission.CREATE_TASK)
task_update_required = permission_required(Permission.UPDATE_TASK)
task_delete_required = permission_required(Permission.DELETE_TASK)
task_assign_required = permission_required(Permission.ASSIGN_TASK)

# 组合权限装饰器
user_management_required = permission_required([
    Permission.READ_USERS,
    Permission.CREATE_USER,
    Permission.UPDATE_USER,
    Permission.DELETE_USER
], require_all=False)

task_management_required = permission_required([
    Permission.CREATE_TASK,
    Permission.UPDATE_TASK,
    Permission.DELETE_TASK,
    Permission.ASSIGN_TASK
], require_all=False)