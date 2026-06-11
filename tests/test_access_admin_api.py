import uuid

import pytest
from rest_framework.test import APIClient

from apps.access_control.models import AccessRule, BusinessResource, Role, UserRole
from apps.authentication.services import create_access_token
from apps.users.models import User


def create_user(*, email: str, role_code: str | None = None) -> User:
    user = User.objects.create(
        email=email,
        password_hash="hash",
        first_name="Test",
        last_name="User",
    )
    if role_code is not None:
        role, _ = Role.objects.get_or_create(
            code=role_code,
            defaults={"name": role_code.title()},
        )
        UserRole.objects.create(user=user, role=role)
    return user


def authenticated_client(user: User) -> APIClient:
    token = create_access_token(user)["access_token"]
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def access_data():
    admin = create_user(email="admin@example.com", role_code="admin")
    guest = create_user(email="guest@example.com", role_code="guest")
    regular_user = create_user(email="user@example.com", role_code="user")
    manager = create_user(email="manager@example.com", role_code="manager")
    target = create_user(email="target@example.com")
    resource = BusinessResource.objects.create(code="orders", name="Orders")
    rule = AccessRule.objects.create(
        role=Role.objects.get(code="guest"),
        resource=resource,
    )
    return {
        "admin": admin,
        "guest": guest,
        "regular_user": regular_user,
        "manager": manager,
        "target": target,
        "resource": resource,
        "rule": rule,
    }


@pytest.mark.django_db
def test_admin_endpoints_enforce_authentication_and_admin_role(access_data):
    admin_client = authenticated_client(access_data["admin"])
    non_admin_clients = [
        authenticated_client(access_data["guest"]),
        authenticated_client(access_data["regular_user"]),
        authenticated_client(access_data["manager"]),
    ]
    urls = [
        "/api/v1/access/roles/",
        f"/api/v1/access/roles/{Role.objects.get(code='guest').id}/",
        "/api/v1/access/resources/",
        f"/api/v1/access/resources/{access_data['resource'].id}/",
        "/api/v1/access/rules/",
        f"/api/v1/access/rules/{access_data['rule'].id}/",
        f"/api/v1/access/users/{access_data['target'].id}/roles/",
    ]

    for url in urls:
        assert APIClient().get(url).status_code == 401
        for client in non_admin_clients:
            assert client.get(url).status_code == 403
        assert admin_client.get(url).status_code == 200


@pytest.mark.django_db
def test_admin_can_manage_roles(access_data):
    client = authenticated_client(access_data["admin"])

    create_response = client.post(
        "/api/v1/access/roles/",
        {
            "code": "auditor",
            "name": "Auditor",
            "description": "Read-only reviewer",
        },
        format="json",
    )
    assert create_response.status_code == 201
    role_id = create_response.json()["id"]

    patch_response = client.patch(
        f"/api/v1/access/roles/{role_id}/",
        {"name": "Security auditor"},
        format="json",
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["name"] == "Security auditor"

    duplicate_response = client.post(
        "/api/v1/access/roles/",
        {"code": "auditor", "name": "Duplicate"},
        format="json",
    )
    assert duplicate_response.status_code == 400
    assert "code" in duplicate_response.json()

    invalid_slug_response = client.post(
        "/api/v1/access/roles/",
        {"code": "not a slug", "name": "Invalid"},
        format="json",
    )
    assert invalid_slug_response.status_code == 400
    assert "code" in invalid_slug_response.json()

    delete_response = client.delete(f"/api/v1/access/roles/{role_id}/")
    assert delete_response.status_code == 204
    assert not Role.objects.filter(id=role_id).exists()


@pytest.mark.django_db
def test_admin_role_cannot_be_deleted(access_data):
    client = authenticated_client(access_data["admin"])
    admin_role = Role.objects.get(code="admin")

    response = client.delete(f"/api/v1/access/roles/{admin_role.id}/")

    assert response.status_code == 400
    assert Role.objects.filter(id=admin_role.id).exists()


@pytest.mark.django_db
def test_admin_role_code_cannot_be_changed(access_data):
    client = authenticated_client(access_data["admin"])
    admin_role = Role.objects.get(code="admin")

    response = client.patch(
        f"/api/v1/access/roles/{admin_role.id}/",
        {"code": "former-admin"},
        format="json",
    )

    assert response.status_code == 400
    admin_role.refresh_from_db()
    assert admin_role.code == "admin"


@pytest.mark.django_db
def test_admin_can_manage_resources(access_data):
    client = authenticated_client(access_data["admin"])

    create_response = client.post(
        "/api/v1/access/resources/",
        {"code": "products", "name": "Products"},
        format="json",
    )
    assert create_response.status_code == 201
    resource_id = create_response.json()["id"]

    duplicate_response = client.post(
        "/api/v1/access/resources/",
        {"code": "products", "name": "Duplicate"},
        format="json",
    )
    assert duplicate_response.status_code == 400
    assert "code" in duplicate_response.json()

    patch_response = client.patch(
        f"/api/v1/access/resources/{resource_id}/",
        {"description": "Product catalogue"},
        format="json",
    )
    assert patch_response.status_code == 200

    delete_response = client.delete(f"/api/v1/access/resources/{resource_id}/")
    assert delete_response.status_code == 204


@pytest.mark.django_db
def test_duplicate_access_rule_returns_400(access_data):
    client = authenticated_client(access_data["admin"])
    role = Role.objects.get(code="user")

    payload = {
        "role": role.id,
        "resource": access_data["resource"].id,
        "can_read_own": True,
        "can_read_all": False,
        "can_create": True,
        "can_update_own": True,
        "can_update_all": False,
        "can_delete_own": True,
        "can_delete_all": False,
    }
    first_response = client.post("/api/v1/access/rules/", payload, format="json")
    duplicate_response = client.post("/api/v1/access/rules/", payload, format="json")

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 400
    assert "non_field_errors" in duplicate_response.json()


@pytest.mark.django_db
def test_admin_can_replace_user_roles_atomically(access_data):
    client = authenticated_client(access_data["admin"])
    target = access_data["target"]
    user_role = Role.objects.get(code="user")
    manager_role = Role.objects.get(code="manager")

    put_response = client.put(
        f"/api/v1/access/users/{target.id}/roles/",
        {"role_ids": [user_role.id, manager_role.id]},
        format="json",
    )

    assert put_response.status_code == 200
    assert {role["code"] for role in put_response.json()["roles"]} == {
        "user",
        "manager",
    }
    assert set(target.user_roles.values_list("role_id", flat=True)) == {
        user_role.id,
        manager_role.id,
    }

    invalid_response = client.put(
        f"/api/v1/access/users/{target.id}/roles/",
        {"role_ids": [user_role.id, 999_999]},
        format="json",
    )

    assert invalid_response.status_code == 400
    assert set(target.user_roles.values_list("role_id", flat=True)) == {
        user_role.id,
        manager_role.id,
    }


@pytest.mark.django_db
def test_assign_roles_returns_404_for_unknown_user(access_data):
    client = authenticated_client(access_data["admin"])

    response = client.get(f"/api/v1/access/users/{uuid.uuid4()}/roles/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_last_active_admin_cannot_remove_own_admin_role(access_data):
    admin = access_data["admin"]
    client = authenticated_client(admin)
    guest_role = Role.objects.get(code="guest")

    response = client.put(
        f"/api/v1/access/users/{admin.id}/roles/",
        {"role_ids": [guest_role.id]},
        format="json",
    )

    assert response.status_code == 400
    assert admin.user_roles.filter(role__code="admin").exists()
