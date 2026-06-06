import pytest
from rest_framework.test import APIClient

from apps.authentication.models import AuthSession
from apps.authentication.services import hash_password
from apps.users.models import User


@pytest.mark.django_db
def test_logout_revokes_current_session():
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

    logout_response = client.post(
        "/api/v1/auth/logout/",
        HTTP_AUTHORIZATION=f"Bearer {access_token}",
    )

    assert logout_response.status_code == 204
    session = AuthSession.objects.get(user=user)
    assert session.revoked_at is not None

    repeated_logout_response = client.post(
        "/api/v1/auth/logout/",
        HTTP_AUTHORIZATION=f"Bearer {access_token}",
    )
    assert repeated_logout_response.status_code == 401
