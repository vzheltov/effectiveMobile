from django.db import transaction

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
