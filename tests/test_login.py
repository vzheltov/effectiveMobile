import pytest
from rest_framework.test import APIClient

from apps.authentication.models import AuthSession
from apps.authentication.services import hash_password
from apps.users.models import User


@pytest.mark.django_db
def test_user_can_login():
    user = User.objects.create(
        email="user@example.com",
        password_hash=hash_password("StrongPass123!"),
        first_name="Иван",
        last_name="Иванов",
    )

    response = APIClient().post(
        "/api/v1/auth/login/",
        {
            "email": "user@example.com",
            "password": "StrongPass123!",
        },
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["access_token"]
    assert response.json()["token_type"] == "Bearer"
    assert response.json()["expires_in"] == 3600
    assert AuthSession.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_login_rejects_wrong_password():
    User.objects.create(
        email="user@example.com",
        password_hash=hash_password("StrongPass123!"),
        first_name="Иван",
        last_name="Иванов",
    )

    response = APIClient().post(
        "/api/v1/auth/login/",
        {
            "email": "user@example.com",
            "password": "WrongPass123!",
        },
        format="json",
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"
    assert AuthSession.objects.exists() is False


@pytest.mark.django_db
def test_login_rejects_unknown_email():
    response = APIClient().post(
        "/api/v1/auth/login/",
        {
            "email": "unknown@example.com",
            "password": "StrongPass123!",
        },
        format="json",
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"
    assert AuthSession.objects.exists() is False


@pytest.mark.django_db
def test_login_rejects_inactive_user():
    User.objects.create(
        email="user@example.com",
        password_hash=hash_password("StrongPass123!"),
        first_name="Иван",
        last_name="Иванов",
        is_active=False,
    )

    response = APIClient().post(
        "/api/v1/auth/login/",
        {
            "email": "user@example.com",
            "password": "StrongPass123!",
        },
        format="json",
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"
    assert AuthSession.objects.exists() is False


@pytest.mark.django_db
def test_login_rejects_corrupted_password_hash():
    User.objects.create(
        email="user@example.com",
        password_hash="not-a-bcrypt-hash",
        first_name="Иван",
        last_name="Иванов",
    )

    response = APIClient().post(
        "/api/v1/auth/login/",
        {
            "email": "user@example.com",
            "password": "StrongPass123!",
        },
        format="json",
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"
    assert not AuthSession.objects.exists()
