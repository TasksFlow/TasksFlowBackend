import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import get_db, Base
from app.core.config import settings
from app.models.user import User, UserRole
from app.utils.user import create_user
from app.schemas.user import UserCreate

# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆盖数据库依赖"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def db_engine():
    """数据库引擎fixture"""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """数据库会话fixture"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client():
    """测试客户端fixture"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_user(db_session):
    """管理员用户fixture"""
    user_data = UserCreate(
        username="testadmin",
        email="testadmin@example.com",
        password="testpassword123",
        role=UserRole.ADMIN
    )
    user = create_user(db_session, user_data)
    return user


@pytest.fixture
def regular_user(db_session):
    """普通用户fixture"""
    user_data = UserCreate(
        username="testuser",
        email="testuser@example.com",
        password="testpassword123",
        role=UserRole.USER
    )
    user = create_user(db_session, user_data)
    return user


@pytest.fixture
def admin_token(client, admin_user):
    """管理员token fixture"""
    response = client.post(
        "/api/auth/login-json",
        json={"username": "testadmin", "password": "testpassword123"}
    )
    return response.json()["access_token"]


@pytest.fixture
def user_token(client, regular_user):
    """普通用户token fixture"""
    response = client.post(
        "/api/auth/login-json",
        json={"username": "testuser", "password": "testpassword123"}
    )
    return response.json()["access_token"]


@pytest.fixture
def auth_headers_admin(admin_token):
    """管理员认证头fixture"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def auth_headers_user(user_token):
    """普通用户认证头fixture"""
    return {"Authorization": f"Bearer {user_token}"}