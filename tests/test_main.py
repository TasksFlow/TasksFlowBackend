import pytest
from fastapi.testclient import TestClient


class TestMainEndpoints:
    """主要端点测试"""

    def test_root_endpoint(self, client: TestClient):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Task Management System API"
        assert "version" in data
        assert "docs_url" in data

    def test_health_check(self, client: TestClient):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_api_docs_accessible(self, client: TestClient):
        """测试API文档可访问"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_openapi_json(self, client: TestClient):
        """测试OpenAPI JSON可访问"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_cors_headers(self, client: TestClient):
        """测试CORS头部"""
        response = client.options("/api/users/me")
        assert response.status_code == 200
        # 检查CORS相关头部是否存在
        assert "access-control-allow-origin" in response.headers

    def test_404_endpoint(self, client: TestClient):
        """测试不存在的端点"""
        response = client.get("/nonexistent")
        assert response.status_code == 404