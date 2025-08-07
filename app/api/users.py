from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user
from app.core.auth_decorators import (
    authenticated_required,
    user_read_required,
    user_create_required,
    user_update_required,
    user_delete_required,
    password_reset_required,
    self_or_admin_required
)
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserUpdate,
    UserChangePassword,
    UserResetPassword
)
from app.utils.user import (
    get_user,
    get_users,
    create_user,
    update_user,
    delete_user,
    change_user_password,
    reset_user_password,
    is_username_taken,
    is_email_taken
)

router = APIRouter()


@router.get("/me", response_model=UserResponse)
@authenticated_required
def read_user_me(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get current user
    """
    return current_user


@router.put("/me", response_model=UserResponse)
@authenticated_required
def update_user_me(
    *,
    db: Session = Depends(get_db),
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Update own user
    """
    # 检查用户名是否已被使用
    if user_in.username and is_username_taken(db, user_in.username, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # 检查邮箱是否已被使用
    if user_in.email and is_email_taken(db, user_in.email, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 普通用户不能修改自己的角色
    if user_in.role is not None:
        user_in.role = None
    
    user = update_user(db, current_user.id, user_in)
    return user


@router.post("/me/change-password")
@authenticated_required
def change_password_me(
    *,
    db: Session = Depends(get_db),
    password_data: UserChangePassword,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Change current user password
    """
    if not change_user_password(
        db, current_user, password_data.old_password, password_data.new_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    return {"message": "Password updated successfully"}


@router.get("/", response_model=List[UserResponse])
@user_read_required
def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieve users (Admin only)
    """
    users = get_users(db, skip=skip, limit=limit)
    return users


@router.post("/", response_model=UserResponse)
@user_create_required
def create_user_by_admin(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Create new user (Admin only)
    """
    # 检查用户名是否已被使用
    if is_username_taken(db, user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # 检查邮箱是否已被使用
    if is_email_taken(db, user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = create_user(db, user_in)
    return user


@router.get("/{user_id}", response_model=UserResponse)
@self_or_admin_required()
def read_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get a specific user by id (Self or Admin only)
    """
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
@self_or_admin_required()
def update_user_by_id(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Update a user (Self or Admin only)
    """
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 检查用户名是否已被使用
    if user_in.username and is_username_taken(db, user_in.username, user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # 检查邮箱是否已被使用
    if user_in.email and is_email_taken(db, user_in.email, user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = update_user(db, user_id, user_in)
    return user


@router.delete("/{user_id}")
@user_delete_required
def delete_user_by_id(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Delete a user (Admin only)
    """
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 不能删除自己
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    delete_user(db, user_id)
    return {"message": "User deleted successfully"}


@router.post("/{user_id}/reset-password")
@password_reset_required
def reset_user_password_by_id(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    password_data: UserResetPassword,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Reset a user's password (Admin only)
    """
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 不能重置自己的密码（应该使用修改密码接口）
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reset your own password. Use change password instead."
        )
    
    reset_user_password(db, user_id, password_data.new_password)
    return {"message": "Password reset successfully"}
