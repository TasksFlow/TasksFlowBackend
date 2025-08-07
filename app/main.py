from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import api_router
from app.db.init_db import create_tables

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="GPU/CPU任务管理系统API",
    openapi_url="/api/openapi.json" if settings.debug else None,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(api_router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    # 创建数据库表
    create_tables()
    print("Application started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    print("Application shutdown")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Task Management System API",
        "version": settings.app_version,
        "docs_url": "/api/docs" if settings.debug else None
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}