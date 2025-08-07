from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router

api_router = APIRouter()

# 包含所有路由
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(users_router, prefix="/users", tags=["users"])

__all__ = ["api_router"]