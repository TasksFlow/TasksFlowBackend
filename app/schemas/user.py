from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    role: Optional[UserRole] = Field(default=UserRole.USER, description="用户角色")


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    role: Optional[UserRole] = Field(None, description="用户角色")
    is_active: Optional[bool] = Field(None, description="是否激活")


class UserChangePassword(BaseModel):
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")


class UserResetPassword(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")


class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenData(BaseModel):
    username: Optional[str] = None