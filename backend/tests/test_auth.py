import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestAuth:
    def test_register_user(self, api_client):
        """Test user registration."""
        data = {
            "email": "newuser@test.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "first_name": "New",
            "last_name": "User",
            "role": "student",
        }
        response = api_client.post("/api/accounts/register/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email="newuser@test.com").exists()

    def test_login_user(self, api_client, student_user):
        """Test user login."""
        data = {
            "email": "student@test.com",
            "password": "testpass123",
        }
        response = api_client.post("/api/accounts/login/", data)
        assert response.status_code == status.HTTP_200_OK
        assert "tokens" in response.data
        assert "access" in response.data["tokens"]
        assert "refresh" in response.data["tokens"]

    def test_login_invalid_credentials(self, api_client, student_user):
        """Test login with invalid credentials."""
        data = {
            "email": "student@test.com",
            "password": "wrongpassword",
        }
        response = api_client.post("/api/accounts/login/", data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_password_reset_request(self, api_client, student_user):
        """Test password reset request."""
        data = {"email": "student@test.com"}
        response = api_client.post("/api/accounts/password/reset/", data)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]

    def test_user_list_requires_admin(self, api_client, authenticated_client):
        """Test that UserListView is admin-only."""
        response = authenticated_client.get("/api/accounts/users/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_list_users(self, admin_client):
        """Test that admin can list users."""
        response = admin_client.get("/api/accounts/users/")
        assert response.status_code == status.HTTP_200_OK

    def test_teacher_cannot_list_users(self, teacher_client):
        """Test that teacher cannot list users."""
        response = teacher_client.get("/api/accounts/users/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_student_cannot_list_users(self, authenticated_client):
        """Test that student cannot list users."""
        response = authenticated_client.get("/api/accounts/users/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
