from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


def get_user(db: Session, user_id: int) -> Optional[User]:
    """根据ID获取用户"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """根据用户名获取用户"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """根据邮箱获取用户"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_username_or_email(db: Session, username_or_email: str) -> Optional[User]:
    """根据用户名或邮箱获取用户"""
    return db.query(User).filter(
        or_(User.username == username_or_email, User.email == username_or_email)
    ).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """获取用户列表"""
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate) -> User:
    """创建用户"""
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """更新用户信息"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int) -> bool:
    """删除用户"""
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True


def authenticate_user(db: Session, username_or_email: str, password: str) -> Optional[User]:
    """验证用户登录"""
    user = get_user_by_username_or_email(db, username_or_email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def change_user_password(db: Session, user: User, old_password: str, new_password: str) -> bool:
    """修改用户密码"""
    if not verify_password(old_password, user.hashed_password):
        return False
    
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    return True


def reset_user_password(db: Session, user: User, new_password: str) -> bool:
    """重置用户密码（管理员功能）"""
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    return True


def is_username_taken(db: Session, username: str, exclude_user_id: Optional[int] = None) -> bool:
    """检查用户名是否已被使用"""
    query = db.query(User).filter(User.username == username)
    if exclude_user_id:
        query = query.filter(User.id != exclude_user_id)
    return query.first() is not None


def is_email_taken(db: Session, email: str, exclude_user_id: Optional[int] = None) -> bool:
    """检查邮箱是否已被使用"""
    query = db.query(User).filter(User.email == email)
    if exclude_user_id:
        query = query.filter(User.id != exclude_user_id)
    return query.first() is not None