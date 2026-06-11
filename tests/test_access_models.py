import pytest
from django.db import IntegrityError, transaction

from apps.access_control.models import AccessRule, BusinessResource, Role, UserRole
from apps.users.models import User


@pytest.mark.django_db
def test_role_code_is_unique():
    Role.objects.create(code="admin", name="Administrator")

    with pytest.raises(IntegrityError), transaction.atomic():
        Role.objects.create(code="admin", name="Second administrator")


@pytest.mark.django_db
def test_business_resource_code_is_unique():
    BusinessResource.objects.create(code="orders", name="Orders")

    with pytest.raises(IntegrityError), transaction.atomic():
        BusinessResource.objects.create(code="orders", name="Duplicate orders")


@pytest.mark.django_db
def test_user_role_pair_is_unique():
    user = User.objects.create(
        email="user@example.com",
        password_hash="hash",
        first_name="Иван",
        last_name="Иванов",
    )
    role = Role.objects.create(code="user", name="User")
    UserRole.objects.create(user=user, role=role)

    with pytest.raises(IntegrityError), transaction.atomic():
        UserRole.objects.create(user=user, role=role)


@pytest.mark.django_db
def test_access_rule_role_resource_pair_is_unique():
    role = Role.objects.create(code="manager", name="Manager")
    resource = BusinessResource.objects.create(code="orders", name="Orders")
    AccessRule.objects.create(role=role, resource=resource)

    with pytest.raises(IntegrityError), transaction.atomic():
        AccessRule.objects.create(role=role, resource=resource)
