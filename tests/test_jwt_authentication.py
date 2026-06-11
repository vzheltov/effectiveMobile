import uuid
from datetime import timedelta

import jwt
import pytest
from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory

from apps.authentication.models import AuthSession
from apps.authentication.authentication import JWTAuthentication
from apps.authentication.services import create_access_token
from apps.users.models import User


def create_user() -> User:
    return User.objects.create(
        email="user@example.com",
        password_hash="hash",
        first_name="Иван",
        last_name="Иванов",
    )


def request_with_payload(payload):
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    return APIRequestFactory().get(
        "/protected/",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )


@pytest.mark.django_db
def test_valid_access_token_identifies_user():
    user = create_user()
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
    user = create_user()
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


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("claim", "value"),
    [
        ("sub", "not-a-uuid"),
        ("jti", "not-a-uuid"),
    ],
)
def test_malformed_uuid_claim_is_rejected(claim, value):
    user = create_user()
    payload = {
        "sub": str(user.id),
        "jti": str(uuid.uuid4()),
        "iat": timezone.now(),
        "exp": timezone.now() + timedelta(hours=1),
        "type": "access",
    }
    payload[claim] = value

    with pytest.raises(AuthenticationFailed):
        JWTAuthentication().authenticate(request_with_payload(payload))


@pytest.mark.django_db
def test_expired_token_is_rejected():
    user = create_user()
    request = request_with_payload(
        {
            "sub": str(user.id),
            "jti": str(uuid.uuid4()),
            "iat": timezone.now() - timedelta(hours=2),
            "exp": timezone.now() - timedelta(hours=1),
            "type": "access",
        }
    )

    with pytest.raises(AuthenticationFailed):
        JWTAuthentication().authenticate(request)


@pytest.mark.django_db
def test_token_with_missing_required_claim_is_rejected():
    user = create_user()
    request = request_with_payload(
        {
            "sub": str(user.id),
            "iat": timezone.now(),
            "exp": timezone.now() + timedelta(hours=1),
            "type": "access",
        }
    )

    with pytest.raises(AuthenticationFailed):
        JWTAuthentication().authenticate(request)


@pytest.mark.django_db
def test_token_without_matching_session_is_rejected():
    user = create_user()
    request = request_with_payload(
        {
            "sub": str(user.id),
            "jti": str(uuid.uuid4()),
            "iat": timezone.now(),
            "exp": timezone.now() + timedelta(hours=1),
            "type": "access",
        }
    )

    with pytest.raises(AuthenticationFailed):
        JWTAuthentication().authenticate(request)


@pytest.mark.django_db
def test_expired_database_session_is_rejected():
    user = create_user()
    token_data = create_access_token(user)
    AuthSession.objects.filter(user=user).update(expires_at=timezone.now() - timedelta(seconds=1))
    request = APIRequestFactory().get(
        "/protected/",
        HTTP_AUTHORIZATION=f"Bearer {token_data['access_token']}",
    )

    with pytest.raises(AuthenticationFailed):
        JWTAuthentication().authenticate(request)
