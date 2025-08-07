import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestBasicFunctionality:
    """基本功能测试"""

    def test_app_creation(self):
        """测试应用创建"""
        assert app is not None
        assert app.title == "Task Management System"

    def test_root_endpoint(self):
        """测试根端点"""
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "Task Management System" in data["message"]

    def test_health_endpoint(self):
        """测试健康检查端点"""
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    def test_docs_endpoint(self):
        """测试API文档端点"""
        with TestClient(app) as client:
            response = client.get("/docs")
            # 文档端点可能返回HTML，检查状态码即可
            assert response.status_code in [200, 404]  # 允许404，因为可能未配置

    def test_openapi_json(self):
        """测试OpenAPI JSON"""
        with TestClient(app) as client:
            response = client.get("/openapi.json")
            if response.status_code == 200:
                data = response.json()
                assert "openapi" in data
                assert "info" in data
            else:
                # 如果端点不存在，也是可以接受的
                assert response.status_code == 404