import uuid

import pytest

from apps.access_control.models import AccessRule, BusinessResource, Role, UserRole
from apps.access_control.services import (
    AccessScope,
    Action,
    get_read_scope,
    has_resource_permission,
)
from apps.users.models import User


def create_user(*, email: str = "user@example.com", is_active: bool = True) -> User:
    return User.objects.create(
        email=email,
        password_hash="hash",
        first_name="Иван",
        last_name="Иванов",
        is_active=is_active,
    )


def assign_rule(user: User, resource: BusinessResource, **permissions: bool) -> AccessRule:
    role = Role.objects.create(
        code=f"role-{Role.objects.count()}",
        name="Test role",
    )
    UserRole.objects.create(user=user, role=role)
    return AccessRule.objects.create(
        role=role,
        resource=resource,
        **permissions,
    )


@pytest.fixture
def orders() -> BusinessResource:
    return BusinessResource.objects.create(code="orders", name="Orders")


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("action", "permission", "owner", "expected"),
    [
        (Action.READ, "can_read_own", "own", True),
        (Action.READ, "can_read_own", "other", False),
        (Action.READ, "can_read_own", "none", False),
        (Action.READ, "can_read_all", "other", True),
        (Action.CREATE, "can_create", "none", True),
        (Action.UPDATE, "can_update_own", "own", True),
        (Action.UPDATE, "can_update_own", "other", False),
        (Action.UPDATE, "can_update_all", "other", True),
        (Action.DELETE, "can_delete_own", "own", True),
        (Action.DELETE, "can_delete_own", "other", False),
        (Action.DELETE, "can_delete_all", "other", True),
    ],
)
def test_resource_permission_rules(
    orders,
    action,
    permission,
    owner,
    expected,
):
    user = create_user()
    assign_rule(user, orders, **{permission: True})
    owner_id = {
        "own": user.id,
        "other": uuid.uuid4(),
        "none": None,
    }[owner]

    assert (
        has_resource_permission(
            user=user,
            resource_code=orders.code,
            action=action,
            owner_id=owner_id,
        )
        is expected
    )


@pytest.mark.django_db
def test_missing_access_rule_denies_permission(orders):
    user = create_user()

    assert not has_resource_permission(
        user=user,
        resource_code=orders.code,
        action=Action.READ,
        owner_id=user.id,
    )


@pytest.mark.django_db
def test_unknown_action_is_denied(orders):
    user = create_user()
    assign_rule(
        user,
        orders,
        can_read_all=True,
        can_create=True,
        can_update_all=True,
        can_delete_all=True,
    )

    assert not has_resource_permission(
        user=user,
        resource_code=orders.code,
        action="unknown",
        owner_id=user.id,
    )


@pytest.mark.django_db
def test_rule_for_another_resource_does_not_grant_permission(orders):
    user = create_user()
    products = BusinessResource.objects.create(code="products", name="Products")
    assign_rule(user, products, can_read_all=True)

    assert not has_resource_permission(
        user=user,
        resource_code=orders.code,
        action=Action.READ,
        owner_id=uuid.uuid4(),
    )


@pytest.mark.django_db
def test_permissions_from_multiple_roles_are_combined(orders):
    user = create_user()
    assign_rule(user, orders, can_update_own=True)
    assign_rule(user, orders, can_update_all=True)

    assert has_resource_permission(
        user=user,
        resource_code=orders.code,
        action=Action.UPDATE,
        owner_id=uuid.uuid4(),
    )


@pytest.mark.django_db
def test_known_string_action_is_supported(orders):
    user = create_user()
    assign_rule(user, orders, can_read_all=True)

    assert has_resource_permission(
        user=user,
        resource_code=orders.code,
        action="read",
        owner_id=uuid.uuid4(),
    )


@pytest.mark.django_db
def test_inactive_user_is_denied(orders):
    user = create_user(is_active=False)
    assign_rule(user, orders, can_read_all=True)

    assert not has_resource_permission(
        user=user,
        resource_code=orders.code,
        action=Action.READ,
        owner_id=uuid.uuid4(),
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("permissions", "expected_scope"),
    [
        ({"can_read_all": True}, AccessScope.ALL),
        ({"can_read_own": True}, AccessScope.OWN),
        ({}, AccessScope.NONE),
    ],
)
def test_read_scope(orders, permissions, expected_scope):
    user = create_user()
    if permissions:
        assign_rule(user, orders, **permissions)

    assert get_read_scope(user=user, resource_code=orders.code) == expected_scope


@pytest.mark.django_db
def test_inactive_user_has_no_read_scope(orders):
    user = create_user(is_active=False)
    assign_rule(user, orders, can_read_all=True)

    assert get_read_scope(user=user, resource_code=orders.code) == AccessScope.NONE


@pytest.mark.django_db
def test_read_all_scope_takes_priority_across_multiple_roles(orders):
    user = create_user()
    assign_rule(user, orders, can_read_own=True)
    assign_rule(user, orders, can_read_all=True)

    assert get_read_scope(user=user, resource_code=orders.code) == AccessScope.ALL
