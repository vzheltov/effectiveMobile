import uuid
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.authentication import models
from apps.users.models import User


@pytest.mark.django_db
def test_auth_session_can_be_created():
    user = User.objects.create(
        email="user@example.com",
        password_hash="hash",
        first_name="Иван",
        last_name="Иванов",
    )
    jti = uuid.uuid4()
    expires_at = timezone.now() + timedelta(hours=1)

    session = models.AuthSession.objects.create(
        user=user,
        jti=jti,
        expires_at=expires_at,
    )

    assert session.user == user
    assert session.jti == jti
    assert session.expires_at == expires_at
    assert session.revoked_at is None
    assert session.created_at is not None
