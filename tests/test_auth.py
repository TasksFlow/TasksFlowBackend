import pytest
from fastapi.testclient import TestClient
from app.schemas.user import UserCreate
from app.utils.user import create_user
from app.models.user import UserRole


class TestAuth:
    """认证相关测试"""

    def test_login_json_success(self, client: TestClient, regular_user):
        """测试JSON登录成功"""
        response = client.post(
            "/api/auth/login-json",
            json={"username": "testuser", "password": "testpassword123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_json_invalid_credentials(self, client: TestClient, regular_user):
        """测试JSON登录失败 - 错误凭据"""
        response = client.post(
            "/api/auth/login-json",
            json={"username": "testuser", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_json_nonexistent_user(self, client: TestClient):
        """测试JSON登录失败 - 用户不存在"""
        response = client.post(
            "/api/auth/login-json",
            json={"username": "nonexistent", "password": "password"}
        )
        assert response.status_code == 401

    def test_login_form_success(self, client: TestClient, regular_user):
        """测试表单登录成功"""
        response = client.post(
            "/api/auth/login",
            data={"username": "testuser", "password": "testpassword123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_form_invalid_credentials(self, client: TestClient, regular_user):
        """测试表单登录失败"""
        response = client.post(
            "/api/auth/login",
            data={"username": "testuser", "password": "wrongpassword"}
        )
        assert response.status_code == 401

    def test_get_current_user_success(self, client: TestClient, auth_headers_user):
        """测试获取当前用户成功"""
        response = client.get("/api/users/me", headers=auth_headers_user)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "testuser@example.com"
        assert data["role"] == "user"

    def test_get_current_user_no_token(self, client: TestClient):
        """测试获取当前用户失败 - 无token"""
        response = client.get("/api/users/me")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client: TestClient):
        """测试获取当前用户失败 - 无效token"""
        response = client.get(
            "/api/users/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    def test_update_current_user(self, client: TestClient, auth_headers_user):
        """测试更新当前用户信息"""
        update_data = {
            "email": "newemail@example.com",
            "full_name": "New Full Name"
        }
        response = client.put(
            "/api/users/me",
            json=update_data,
            headers=auth_headers_user
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newemail@example.com"
        assert data["full_name"] == "New Full Name"

    def test_change_password_success(self, client: TestClient, auth_headers_user):
        """测试修改密码成功"""
        password_data = {
            "current_password": "testpassword123",
            "new_password": "newpassword123"
        }
        response = client.post(
            "/api/users/me/change-password",
            json=password_data,
            headers=auth_headers_user
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Password changed successfully"

    def test_change_password_wrong_current(self, client: TestClient, auth_headers_user):
        """测试修改密码失败 - 当前密码错误"""
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword123"
        }
        response = client.post(
            "/api/users/me/change-password",
            json=password_data,
            headers=auth_headers_user
        )
        assert response.status_code == 400
        assert "Current password is incorrect" in response.json()["detail"]