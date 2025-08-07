from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.database import engine, Base
from app.models.user import User, UserRole
from app.utils.user import get_user_by_username, create_user
from app.schemas.user import UserCreate


def create_tables():
    """创建所有数据库表"""
    Base.metadata.create_all(bind=engine)


def init_db(db: Session) -> None:
    """初始化数据库数据"""
    # 创建管理员用户
    admin_user = get_user_by_username(db, username=settings.admin_username)
    if not admin_user:
        admin_user_in = UserCreate(
            username=settings.admin_username,
            email=settings.admin_email,
            password=settings.admin_password,
            role=UserRole.ADMIN
        )
        admin_user = create_user(db, admin_user_in)
        print(f"Created admin user: {admin_user.username}")
    else:
        print(f"Admin user already exists: {admin_user.username}")


if __name__ == "__main__":
    from app.db.database import SessionLocal
    
    # 创建表
    create_tables()
    print("Database tables created successfully")
    
    # 初始化数据
    db = SessionLocal()
    try:
        init_db(db)
        print("Database initialized successfully")
    finally:
        db.close()