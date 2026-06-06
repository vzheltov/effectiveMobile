import pytest
from rest_framework.test import APIClient

from apps.users.models import User


@pytest.mark.django_db
def test_user_can_register():
    response = APIClient().post(
        "/api/v1/auth/register/",
        {
            "email": "ivan@example.com",
            "first_name": "Иван",
            "last_name": "Иванов",
            "middle_name": "Иванович",
            "password": "StrongPass123!",
            "password_repeat": "StrongPass123!",
        },
        format="json",
    )

    assert response.status_code == 201

    user = User.objects.get(email="ivan@example.com")
    assert user.first_name == "Иван"
    assert user.password_hash != "StrongPass123!"
    assert "password" not in response.json()
    assert "password_hash" not in response.json()


@pytest.mark.django_db
def test_registration_rejects_duplicate_email():
    User.objects.create(
        email="ivan@example.com",
        password_hash="hash",
        first_name="Иван",
        last_name="Иванов",
    )

    response = APIClient().post(
        "/api/v1/auth/register/",
        {
            "email": "IVAN@example.com",
            "first_name": "Пётр",
            "last_name": "Петров",
            "password": "StrongPass123!",
            "password_repeat": "StrongPass123!",
        },
        format="json",
    )

    assert response.status_code == 400
    assert User.objects.count() == 1


@pytest.mark.django_db
def test_registration_rejects_different_passwords():
    response = APIClient().post(
        "/api/v1/auth/register/",
        {
            "email": "ivan@example.com",
            "first_name": "Иван",
            "last_name": "Иванов",
            "password": "StrongPass123!",
            "password_repeat": "DifferentPass123!",
        },
        format="json",
    )

    assert response.status_code == 400
    assert User.objects.exists() is False
    assert "password_repeat" in response.json()
