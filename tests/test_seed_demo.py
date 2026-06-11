import pytest
from django.core.management import call_command

from apps.access_control.models import AccessRule, BusinessResource, Role, UserRole
from apps.authentication.services import verify_password
from apps.users.models import User


DEMO_USERS = {
    "admin@example.com": ("AdminPass123!", "admin"),
    "manager@example.com": ("ManagerPass123!", "manager"),
    "user@example.com": ("UserPass123!", "user"),
    "guest@example.com": ("GuestPass123!", "guest"),
}


@pytest.mark.django_db
def test_seed_demo_creates_expected_access_data():
    call_command("seed_demo")

    assert set(Role.objects.values_list("code", flat=True)) == {
        "admin",
        "manager",
        "user",
        "guest",
    }
    assert set(BusinessResource.objects.values_list("code", flat=True)) == {
        "orders",
        "products",
        "access_rules",
    }
    assert set(User.objects.values_list("email", flat=True)) == set(DEMO_USERS)

    for email, (password, role_code) in DEMO_USERS.items():
        user = User.objects.get(email=email)
        assert user.is_active
        assert verify_password(password, user.password_hash)
        assert set(user.user_roles.values_list("role__code", flat=True)) == {role_code}

    admin_orders = AccessRule.objects.get(
        role__code="admin",
        resource__code="orders",
    )
    assert admin_orders.can_read_all
    assert admin_orders.can_create
    assert admin_orders.can_update_all
    assert admin_orders.can_delete_all

    manager_orders = AccessRule.objects.get(
        role__code="manager",
        resource__code="orders",
    )
    assert manager_orders.can_read_all
    assert manager_orders.can_update_all
    assert not manager_orders.can_delete_all

    user_orders = AccessRule.objects.get(
        role__code="user",
        resource__code="orders",
    )
    assert user_orders.can_read_own
    assert user_orders.can_create
    assert user_orders.can_update_own
    assert user_orders.can_delete_own
    assert not user_orders.can_read_all

    assert not AccessRule.objects.filter(role__code="guest").exists()


@pytest.mark.django_db
def test_seed_demo_is_idempotent_and_repairs_demo_data():
    call_command("seed_demo")
    user = User.objects.get(email="user@example.com")
    user.is_active = False
    user.save(update_fields=["is_active"])
    AccessRule.objects.filter(
        role__code="user",
        resource__code="orders",
    ).update(can_read_all=True)

    call_command("seed_demo")

    assert Role.objects.count() == 4
    assert BusinessResource.objects.count() == 3
    assert User.objects.count() == 4
    assert UserRole.objects.count() == 4
    assert AccessRule.objects.count() == 5

    user.refresh_from_db()
    assert user.is_active
    assert not AccessRule.objects.get(
        role__code="user",
        resource__code="orders",
    ).can_read_all
