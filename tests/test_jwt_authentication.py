import pytest
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory

from apps.authentication.models import AuthSession
from apps.authentication.authentication import JWTAuthentication
from apps.authentication.services import create_access_token
from apps.users.models import User


@pytest.mark.django_db
def test_valid_access_token_identifies_user():
    user = User.objects.create(
        email="user@example.com",
        password_hash="hash",
        first_name="Иван",
        last_name="Иванов",
    )
    token_data = create_access_token(user)
    request = APIRequestFactory().get(
        "/protected/",
        HTTP_AUTHORIZATION=f"Bearer {token_data['access_token']}",
    )

    authenticated_user, session = JWTAuthentication().authenticate(request)

    assert authenticated_user == user
    assert session.user == user


@pytest.mark.django_db
def test_invalid_access_token_is_rejected():
    request = APIRequestFactory().get(
        "/protected/",
        HTTP_AUTHORIZATION="Bearer invalid-token",
    )

    with pytest.raises(AuthenticationFailed):
        JWTAuthentication().authenticate(request)


@pytest.mark.django_db
def test_revoked_session_is_rejected():
    user = User.objects.create(
        email="user@example.com",
        password_hash="hash",
        first_name="Иван",
        last_name="Иванов",
    )
    token_data = create_access_token(user)
    session = AuthSession.objects.get(user=user)
    session.revoked_at = session.created_at
    session.save(update_fields=["revoked_at"])
    request = APIRequestFactory().get(
        "/protected/",
        HTTP_AUTHORIZATION=f"Bearer {token_data['access_token']}",
    )

    with pytest.raises(AuthenticationFailed):
        JWTAuthentication().authenticate(request)
