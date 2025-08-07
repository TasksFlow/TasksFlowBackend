from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 应用配置
    app_name: str = "Task Management System"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # 数据库配置
    database_url: str = "sqlite:///./task_management.db"
    
    # JWT配置
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # 管理员账户配置
    admin_username: str = "admin"
    admin_email: str = "admin@example.com"
    admin_password: str = "admin123"
    
    # 资源监控配置
    resource_monitor_interval: int = 5
    resource_history_days: int = 30
    
    # 任务配置
    max_concurrent_tasks: int = 1
    task_timeout_seconds: int = 3600
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()