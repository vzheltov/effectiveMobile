import uuid
from datetime import timedelta

import bcrypt
import jwt
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed

from apps.authentication.models import AuthSession
from apps.users.models import User


def hash_password(raw_password: str) -> str:
    password_bytes = raw_password.encode("utf-8")
    password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt())

    return password_hash.decode("utf-8")


def verify_password(raw_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(
        raw_password.encode("utf-8"),
        password_hash.encode("utf-8"),
    )


@transaction.atomic
def create_access_token(user: User) -> dict:
    issued_at = timezone.now()
    expires_at = issued_at + timedelta(seconds=settings.JWT_TTL_SECONDS)
    jti = uuid.uuid4()

    AuthSession.objects.create(
        user=user,
        jti=jti,
        expires_at=expires_at,
    )

    payload = {
        "sub": str(user.id),
        "jti": str(jti),
        "iat": issued_at,
        "exp": expires_at,
        "type": "access",
    }

    access_token = jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm="HS256",
    )

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": settings.JWT_TTL_SECONDS,
    }


@transaction.atomic
def login_user(email: str, password: str) -> dict:
    normalized_email = email.strip().lower()

    try:
        user = User.objects.get(
            email__iexact=normalized_email,
            is_active=True,
        )
    except User.DoesNotExist as error:
        raise AuthenticationFailed("Invalid email or password") from error

    if not verify_password(password, user.password_hash):
        raise AuthenticationFailed("Invalid email or password")

    return create_access_token(user)


def revoke_session(session: AuthSession) -> None:
    session.revoked_at = timezone.now()
    session.save(update_fields=["revoked_at"])
