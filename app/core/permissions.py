"""
面向切面的权限管理装饰器
基于Python装饰器实现的权限控制系统
"""
from functools import wraps
from typing import Callable, List, Optional, Union
from enum import Enum
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_current_active_user
from app.db.database import get_db
from app.models.user import User, UserRole


class Permission(Enum):
    """权限枚举"""
    # 用户权限
    READ_SELF = "read_self"           # 读取自己的信息
    UPDATE_SELF = "update_self"       # 更新自己的信息
    DELETE_SELF = "delete_self"       # 删除自己的账户
    
    # 用户管理权限
    READ_USERS = "read_users"         # 读取用户列表
    CREATE_USER = "create_user"       # 创建用户
    UPDATE_USER = "update_user"       # 更新用户信息
    DELETE_USER = "delete_user"       # 删除用户
    RESET_PASSWORD = "reset_password" # 重置用户密码
    
    # 任务权限
    READ_TASKS = "read_tasks"         # 读取任务
    CREATE_TASK = "create_task"       # 创建任务
    UPDATE_TASK = "update_task"       # 更新任务
    DELETE_TASK = "delete_task"       # 删除任务
    ASSIGN_TASK = "assign_task"       # 分配任务
    
    # 系统管理权限
    ADMIN_ACCESS = "admin_access"     # 管理员访问权限
    SYSTEM_CONFIG = "system_config"   # 系统配置权限


class PermissionChecker:
    """权限检查器"""
    
    # 角色权限映射
    ROLE_PERMISSIONS = {
        UserRole.ADMIN: [
            # 管理员拥有所有权限
            Permission.READ_SELF,
            Permission.UPDATE_SELF,
            Permission.DELETE_SELF,
            Permission.READ_USERS,
            Permission.CREATE_USER,
            Permission.UPDATE_USER,
            Permission.DELETE_USER,
            Permission.RESET_PASSWORD,
            Permission.READ_TASKS,
            Permission.CREATE_TASK,
            Permission.UPDATE_TASK,
            Permission.DELETE_TASK,
            Permission.ASSIGN_TASK,
            Permission.ADMIN_ACCESS,
            Permission.SYSTEM_CONFIG,
        ],
        UserRole.USER: [
            # 普通用户权限
            Permission.READ_SELF,
            Permission.UPDATE_SELF,
            Permission.READ_TASKS,
            Permission.CREATE_TASK,
            Permission.UPDATE_TASK,
        ]
    }
    
    @classmethod
    def has_permission(cls, user: User, permission: Permission) -> bool:
        """检查用户是否有指定权限"""
        if not user or not user.is_active:
            return False
        
        user_permissions = cls.ROLE_PERMISSIONS.get(user.role, [])
        return permission in user_permissions
    
    @classmethod
    def has_any_permission(cls, user: User, permissions: List[Permission]) -> bool:
        """检查用户是否有任意一个权限"""
        return any(cls.has_permission(user, perm) for perm in permissions)
    
    @classmethod
    def has_all_permissions(cls, user: User, permissions: List[Permission]) -> bool:
        """检查用户是否有所有权限"""
        return all(cls.has_permission(user, perm) for perm in permissions)


def require_permission(
    permission: Union[Permission, List[Permission]],
    require_all: bool = True,
    allow_self_access: bool = False,
    self_access_param: str = "user_id"
):
    """
    权限装饰器
    
    Args:
        permission: 需要的权限或权限列表
        require_all: 是否需要所有权限（True）还是任意一个权限（False）
        allow_self_access: 是否允许用户访问自己的资源
        self_access_param: 用于判断自访问的参数名
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 获取当前用户
            current_user = None
            db = None
            
            # 从参数中提取用户和数据库会话
            for arg in args:
                if isinstance(arg, User):
                    current_user = arg
                elif isinstance(arg, Session):
                    db = arg
            
            for key, value in kwargs.items():
                if key == "current_user" and isinstance(value, User):
                    current_user = value
                elif key == "db" and isinstance(value, Session):
                    db = value
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # 检查自访问权限
            if allow_self_access and self_access_param in kwargs:
                target_user_id = kwargs[self_access_param]
                if current_user.id == target_user_id:
                    # 用户访问自己的资源，允许通过
                    return await func(*args, **kwargs)
            
            # 检查权限
            permissions = permission if isinstance(permission, list) else [permission]
            
            if require_all:
                has_access = PermissionChecker.has_all_permissions(current_user, permissions)
            else:
                has_access = PermissionChecker.has_any_permission(current_user, permissions)
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 获取当前用户
            current_user = None
            db = None
            
            # 从参数中提取用户和数据库会话
            for arg in args:
                if isinstance(arg, User):
                    current_user = arg
                elif isinstance(arg, Session):
                    db = arg
            
            for key, value in kwargs.items():
                if key == "current_user" and isinstance(value, User):
                    current_user = value
                elif key == "db" and isinstance(value, Session):
                    db = value
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # 检查自访问权限
            if allow_self_access and self_access_param in kwargs:
                target_user_id = kwargs[self_access_param]
                if current_user.id == target_user_id:
                    # 用户访问自己的资源，允许通过
                    return func(*args, **kwargs)
            
            # 检查权限
            permissions = permission if isinstance(permission, list) else [permission]
            
            if require_all:
                has_access = PermissionChecker.has_all_permissions(current_user, permissions)
            else:
                has_access = PermissionChecker.has_any_permission(current_user, permissions)
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            return func(*args, **kwargs)
        
        # 检查函数是否是异步的
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def require_admin(func: Callable) -> Callable:
    """管理员权限装饰器（简化版）"""
    return require_permission(Permission.ADMIN_ACCESS)(func)


def require_authenticated(func: Callable) -> Callable:
    """认证装饰器（只需要登录）"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 获取当前用户
        current_user = None
        
        for arg in args:
            if isinstance(arg, User):
                current_user = arg
        
        for key, value in kwargs.items():
            if key == "current_user" and isinstance(value, User):
                current_user = value
        
        if not current_user or not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        return func(*args, **kwargs)
    
    return wrapper


def require_self_or_admin(self_access_param: str = "user_id"):
    """要求是本人或管理员才能访问"""
    return require_permission(
        Permission.ADMIN_ACCESS,
        allow_self_access=True,
        self_access_param=self_access_param
    )


# 常用权限装饰器组合
require_user_management = require_permission([
    Permission.READ_USERS,
    Permission.CREATE_USER,
    Permission.UPDATE_USER,
    Permission.DELETE_USER
], require_all=False)

require_task_management = require_permission([
    Permission.CREATE_TASK,
    Permission.UPDATE_TASK,
    Permission.DELETE_TASK,
    Permission.ASSIGN_TASK
], require_all=False)