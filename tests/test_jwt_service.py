import jwt
import pytest
from django.conf import settings
from django.utils import timezone

from apps.authentication.models import AuthSession
from apps.authentication.services import create_access_token
from apps.users.models import User


@pytest.mark.django_db
def test_access_token_creates_auth_session():
    user = User.objects.create(
        email="user@example.com",
        password_hash="hash",
        first_name="Иван",
        last_name="Иванов",
    )

    token_data = create_access_token(user)
    payload = jwt.decode(
        token_data["access_token"],
        settings.JWT_SECRET,
        algorithms=["HS256"],
    )

    session = AuthSession.objects.get(jti=payload["jti"])

    assert payload["sub"] == str(user.id)
    assert payload["type"] == "access"
    assert session.user == user
    assert session.revoked_at is None
    assert session.expires_at > timezone.now()
    assert token_data["expires_in"] == settings.JWT_TTL_SECONDS
