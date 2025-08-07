import pytest
from fastapi.testclient import TestClient
from app.models.user import UserRole


class TestUserManagement:
    """用户管理相关测试"""

    def test_get_all_users_admin(self, client: TestClient, auth_headers_admin, regular_user):
        """测试管理员获取所有用户"""
        response = client.get("/api/users/", headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 2  # 至少有admin和regular用户

    def test_get_all_users_non_admin(self, client: TestClient, auth_headers_user):
        """测试非管理员获取所有用户 - 应该被拒绝"""
        response = client.get("/api/users/", headers=auth_headers_user)
        assert response.status_code == 403

    def test_create_user_admin(self, client: TestClient, auth_headers_admin):
        """测试管理员创建用户"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpassword123",
            "role": "user",
            "full_name": "New User"
        }
        response = client.post(
            "/api/users/",
            json=user_data,
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "user"

    def test_create_user_duplicate_username(self, client: TestClient, auth_headers_admin, regular_user):
        """测试创建重复用户名的用户"""
        user_data = {
            "username": "testuser",  # 已存在的用户名
            "email": "another@example.com",
            "password": "password123",
            "role": "user"
        }
        response = client.post(
            "/api/users/",
            json=user_data,
            headers=auth_headers_admin
        )
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]

    def test_create_user_duplicate_email(self, client: TestClient, auth_headers_admin, regular_user):
        """测试创建重复邮箱的用户"""
        user_data = {
            "username": "anotheruser",
            "email": "testuser@example.com",  # 已存在的邮箱
            "password": "password123",
            "role": "user"
        }
        response = client.post(
            "/api/users/",
            json=user_data,
            headers=auth_headers_admin
        )
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_create_user_non_admin(self, client: TestClient, auth_headers_user):
        """测试非管理员创建用户 - 应该被拒绝"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "role": "user"
        }
        response = client.post(
            "/api/users/",
            json=user_data,
            headers=auth_headers_user
        )
        assert response.status_code == 403

    def test_get_user_by_id_admin(self, client: TestClient, auth_headers_admin, regular_user):
        """测试管理员通过ID获取用户"""
        response = client.get(f"/api/users/{regular_user.id}", headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == regular_user.id
        assert data["username"] == "testuser"

    def test_get_user_by_id_non_admin(self, client: TestClient, auth_headers_user, admin_user):
        """测试非管理员通过ID获取用户 - 应该被拒绝"""
        response = client.get(f"/api/users/{admin_user.id}", headers=auth_headers_user)
        assert response.status_code == 403

    def test_get_nonexistent_user(self, client: TestClient, auth_headers_admin):
        """测试获取不存在的用户"""
        response = client.get("/api/users/99999", headers=auth_headers_admin)
        assert response.status_code == 404

    def test_update_user_admin(self, client: TestClient, auth_headers_admin, regular_user):
        """测试管理员更新用户"""
        update_data = {
            "email": "updated@example.com",
            "full_name": "Updated Name",
            "role": "admin"
        }
        response = client.put(
            f"/api/users/{regular_user.id}",
            json=update_data,
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated@example.com"
        assert data["full_name"] == "Updated Name"
        assert data["role"] == "admin"

    def test_update_user_non_admin(self, client: TestClient, auth_headers_user, admin_user):
        """测试非管理员更新用户 - 应该被拒绝"""
        update_data = {"email": "hacker@example.com"}
        response = client.put(
            f"/api/users/{admin_user.id}",
            json=update_data,
            headers=auth_headers_user
        )
        assert response.status_code == 403

    def test_delete_user_admin(self, client: TestClient, auth_headers_admin, db_session):
        """测试管理员删除用户"""
        # 先创建一个用户用于删除
        from app.utils.user import create_user
        from app.schemas.user import UserCreate
        
        user_data = UserCreate(
            username="todelete",
            email="todelete@example.com",
            password="password123",
            role=UserRole.USER
        )
        user_to_delete = create_user(db_session, user_data)
        
        response = client.delete(
            f"/api/users/{user_to_delete.id}",
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        assert response.json()["message"] == "User deleted successfully"

    def test_delete_user_non_admin(self, client: TestClient, auth_headers_user, admin_user):
        """测试非管理员删除用户 - 应该被拒绝"""
        response = client.delete(
            f"/api/users/{admin_user.id}",
            headers=auth_headers_user
        )
        assert response.status_code == 403

    def test_delete_nonexistent_user(self, client: TestClient, auth_headers_admin):
        """测试删除不存在的用户"""
        response = client.delete("/api/users/99999", headers=auth_headers_admin)
        assert response.status_code == 404