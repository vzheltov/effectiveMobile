import pytest
from rest_framework.test import APIClient

from apps.authentication.services import hash_password
from apps.users.models import User


@pytest.mark.django_db
def test_profile_requires_authentication():
    response = APIClient().get("/api/v1/users/me/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_user_can_read_own_profile():
    User.objects.create(
        email="user@example.com",
        password_hash=hash_password("StrongPass123!"),
        first_name="Иван",
        last_name="Иванов",
        middle_name="Иванович",
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

    response = client.get(
        "/api/v1/users/me/",
        HTTP_AUTHORIZATION=f"Bearer {login_response.json()['access_token']}",
    )

    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"
    assert response.json()["first_name"] == "Иван"
    assert response.json()["last_name"] == "Иванов"
    assert response.json()["middle_name"] == "Иванович"
    assert "password_hash" not in response.json()


@pytest.mark.django_db
def test_user_can_update_own_profile():
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

    response = client.patch(
        "/api/v1/users/me/",
        {
            "first_name": "Пётр",
            "is_active": False,
            "password_hash": "stolen",
        },
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {login_response.json()['access_token']}",
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.email == "user@example.com"
    assert user.first_name == "Пётр"
    assert user.is_active is True
    assert user.password_hash != "stolen"


@pytest.mark.django_db
def test_profile_update_rejects_email_owned_by_another_user():
    user = User.objects.create(
        email="user@example.com",
        password_hash=hash_password("StrongPass123!"),
        first_name="Иван",
        last_name="Иванов",
    )
    User.objects.create(
        email="other@example.com",
        password_hash="hash",
        first_name="Пётр",
        last_name="Петров",
    )
    login_response = APIClient().post(
        "/api/v1/auth/login/",
        {
            "email": "user@example.com",
            "password": "StrongPass123!",
        },
        format="json",
    )

    response = APIClient().patch(
        "/api/v1/users/me/",
        {"email": "OTHER@example.com"},
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {login_response.json()['access_token']}",
    )

    assert response.status_code == 400
    user.refresh_from_db()
    assert user.email == "user@example.com"


@pytest.mark.django_db
def test_profile_update_rejects_new_email():
    user = User.objects.create(
        email="user@example.com",
        password_hash=hash_password("StrongPass123!"),
        first_name="Иван",
        last_name="Иванов",
    )
    login_response = APIClient().post(
        "/api/v1/auth/login/",
        {
            "email": "user@example.com",
            "password": "StrongPass123!",
        },
        format="json",
    )

    response = APIClient().patch(
        "/api/v1/users/me/",
        {"email": "renamed@example.com"},
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {login_response.json()['access_token']}",
    )

    assert response.status_code == 400
    user.refresh_from_db()
    assert user.email == "user@example.com"
