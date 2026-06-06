from django.db import transaction
from django.utils import timezone

from apps.authentication.services import hash_password
from apps.users.models import User


@transaction.atomic
def register_user(**validated_data) -> User:
    password = validated_data.pop("password")
    validated_data.pop("password_repeat")

    return User.objects.create(
        **validated_data,
        password_hash=hash_password(password),
    )


@transaction.atomic
def deactivate_user(user: User) -> None:
    deactivated_at = timezone.now()
    user.is_active = False
    user.deleted_at = deactivated_at
    user.save(update_fields=["is_active", "deleted_at", "updated_at"])
    user.auth_sessions.filter(revoked_at__isnull=True).update(
        revoked_at=deactivated_at,
    )
