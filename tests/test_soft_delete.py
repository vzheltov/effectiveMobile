import pytest
from rest_framework.test import APIClient

from apps.access_control.models import Role, UserRole
from apps.authentication.models import AuthSession
from apps.authentication.services import hash_password
from apps.users.models import User


@pytest.mark.django_db
def test_user_can_soft_delete_account():
    user = User.objects.create(
        email="user@example.com",
        password_hash=hash_password("StrongPass123!"),
        first_name="Иван",
        last_name="Иванов",
    )
    client = APIClient()
    login_response = client.post(
        "/api/v1/auth/login/",
        {
            "email": "user@example.com",
            "password": "StrongPass123!",
        },
        format="json",
    )
    access_token = login_response.json()["access_token"]

    delete_response = client.delete(
        "/api/v1/users/me/",
        HTTP_AUTHORIZATION=f"Bearer {access_token}",
    )

    assert delete_response.status_code == 204
    user.refresh_from_db()
    assert user.is_active is False
    assert user.deleted_at is not None
    assert AuthSession.objects.get(user=user).revoked_at is not None

    profile_response = client.get(
        "/api/v1/users/me/",
        HTTP_AUTHORIZATION=f"Bearer {access_token}",
    )
    assert profile_response.status_code == 401

    repeated_login_response = client.post(
        "/api/v1/auth/login/",
        {
            "email": "user@example.com",
            "password": "StrongPass123!",
        },
        format="json",
    )
    assert repeated_login_response.status_code == 401


@pytest.mark.django_db
def test_last_active_admin_cannot_delete_account():
    user = User.objects.create(
        email="admin@example.com",
        password_hash=hash_password("StrongPass123!"),
        first_name="Admin",
        last_name="User",
    )
    admin_role = Role.objects.create(code="admin", name="Administrator")
    UserRole.objects.create(user=user, role=admin_role)
    login_response = APIClient().post(
        "/api/v1/auth/login/",
        {
            "email": "admin@example.com",
            "password": "StrongPass123!",
        },
        format="json",
    )

    response = APIClient().delete(
        "/api/v1/users/me/",
        HTTP_AUTHORIZATION=f"Bearer {login_response.json()['access_token']}",
    )

    assert response.status_code == 400
    user.refresh_from_db()
    assert user.is_active is True
    assert user.deleted_at is None
