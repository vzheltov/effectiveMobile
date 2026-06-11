from django.core.management.base import BaseCommand
from django.db import transaction

from apps.access_control.models import (
    AccessRule,
    BusinessResource,
    Role,
    UserRole,
)
from apps.authentication.services import hash_password, verify_password
from apps.users.models import User


ROLE_DATA = {
    "admin": {
        "name": "Administrator",
        "description": "Manages access rules and all demo resources.",
    },
    "manager": {
        "name": "Manager",
        "description": "Reads and updates all orders.",
    },
    "user": {
        "name": "User",
        "description": "Works with own orders and creates new orders.",
    },
    "guest": {
        "name": "Guest",
        "description": "Has no resource permissions.",
    },
}

RESOURCE_DATA = {
    "orders": {
        "name": "Orders",
        "description": "Mock customer orders.",
    },
    "products": {
        "name": "Products",
        "description": "Mock product catalogue.",
    },
    "access_rules": {
        "name": "Access rules",
        "description": "Role and resource access configuration.",
    },
}

DEMO_USERS = {
    "admin@example.com": {
        "password": "AdminPass123!",
        "role": "admin",
        "first_name": "Admin",
        "last_name": "Demo",
    },
    "manager@example.com": {
        "password": "ManagerPass123!",
        "role": "manager",
        "first_name": "Manager",
        "last_name": "Demo",
    },
    "user@example.com": {
        "password": "UserPass123!",
        "role": "user",
        "first_name": "User",
        "last_name": "Demo",
    },
    "guest@example.com": {
        "password": "GuestPass123!",
        "role": "guest",
        "first_name": "Guest",
        "last_name": "Demo",
    },
}

EMPTY_PERMISSIONS = {
    "can_read_own": False,
    "can_read_all": False,
    "can_create": False,
    "can_update_own": False,
    "can_update_all": False,
    "can_delete_own": False,
    "can_delete_all": False,
}

RULE_DATA = {
    ("admin", "orders"): {
        "can_read_all": True,
        "can_create": True,
        "can_update_all": True,
        "can_delete_all": True,
    },
    ("admin", "products"): {
        "can_read_all": True,
        "can_create": True,
        "can_update_all": True,
        "can_delete_all": True,
    },
    ("admin", "access_rules"): {
        "can_read_all": True,
        "can_create": True,
        "can_update_all": True,
        "can_delete_all": True,
    },
    ("manager", "orders"): {
        "can_read_all": True,
        "can_update_all": True,
    },
    ("user", "orders"): {
        "can_read_own": True,
        "can_create": True,
        "can_update_own": True,
        "can_delete_own": True,
    },
}


def password_is_valid(user: User, password: str) -> bool:
    try:
        return verify_password(password, user.password_hash)
    except ValueError:
        return False


class Command(BaseCommand):
    help = "Create or repair local demonstration users and access rules."

    @transaction.atomic
    def handle(self, *args, **options):
        roles = {
            code: Role.objects.update_or_create(code=code, defaults=data)[0]
            for code, data in ROLE_DATA.items()
        }
        resources = {
            code: BusinessResource.objects.update_or_create(
                code=code,
                defaults=data,
            )[0]
            for code, data in RESOURCE_DATA.items()
        }

        for email, data in DEMO_USERS.items():
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "password_hash": "",
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                },
            )
            user.first_name = data["first_name"]
            user.last_name = data["last_name"]
            user.middle_name = ""
            user.is_active = True
            user.deleted_at = None
            if created or not password_is_valid(user, data["password"]):
                user.password_hash = hash_password(data["password"])
            user.save()

            UserRole.objects.filter(user=user).exclude(
                role=roles[data["role"]],
            ).delete()
            UserRole.objects.get_or_create(user=user, role=roles[data["role"]])

        expected_pairs = set(RULE_DATA)
        for (role_code, resource_code), permissions in RULE_DATA.items():
            AccessRule.objects.update_or_create(
                role=roles[role_code],
                resource=resources[resource_code],
                defaults={**EMPTY_PERMISSIONS, **permissions},
            )

        for role_code, role in roles.items():
            expected_resources = {
                resources[resource_code]
                for candidate_role, resource_code in expected_pairs
                if candidate_role == role_code
            }
            AccessRule.objects.filter(
                role=role,
                resource__in=resources.values(),
            ).exclude(resource__in=expected_resources).delete()

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
