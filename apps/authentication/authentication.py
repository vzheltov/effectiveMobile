import jwt
from uuid import UUID

from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from apps.authentication.models import AuthSession
from apps.users.models import User


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        authorization = get_authorization_header(request).split()

        if not authorization:
            return None

        if len(authorization) != 2 or authorization[0].lower() != b"bearer":
            raise AuthenticationFailed("Invalid authorization header")

        try:
            payload = jwt.decode(
                authorization[1],
                settings.JWT_SECRET,
                algorithms=["HS256"],
                options={"require": ["sub", "jti", "iat", "exp", "type"]},
            )
        except jwt.InvalidTokenError as error:
            raise AuthenticationFailed("Invalid or expired token") from error

        if payload["type"] != "access":
            raise AuthenticationFailed("Invalid token type")

        try:
            user_id = UUID(str(payload["sub"]))
            session_jti = UUID(str(payload["jti"]))
        except (TypeError, ValueError) as error:
            raise AuthenticationFailed("Invalid or expired token") from error

        try:
            user = User.objects.get(id=user_id, is_active=True)
            session = AuthSession.objects.get(
                user=user,
                jti=session_jti,
            )
        except (User.DoesNotExist, AuthSession.DoesNotExist) as error:
            raise AuthenticationFailed("Invalid or expired token") from error

        if session.revoked_at is not None or session.expires_at <= timezone.now():
            raise AuthenticationFailed("Invalid or expired token")

        return user, session

    def authenticate_header(self, request):
        return "Bearer"
