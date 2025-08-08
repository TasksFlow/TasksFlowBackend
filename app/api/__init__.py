from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .tasks import router as tasks_router
from .monitoring import router as monitoring_router

api_router = APIRouter()

# 包含所有路由
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
api_router.include_router(monitoring_router, prefix="/monitoring", tags=["monitoring"])

__all__ = ["api_router"]