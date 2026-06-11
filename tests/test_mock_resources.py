import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.authentication.services import create_access_token
from apps.users.models import User


def client_for(email: str) -> APIClient:
    token = create_access_token(User.objects.get(email=email))["access_token"]
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def demo_data():
    call_command("seed_demo", verbosity=0)


@pytest.mark.django_db
def test_order_list_enforces_401_403_own_and_all_scopes(demo_data):
    assert APIClient().get("/api/v1/mock/orders/").status_code == 401
    assert client_for("guest@example.com").get("/api/v1/mock/orders/").status_code == 403

    user_response = client_for("user@example.com").get("/api/v1/mock/orders/")
    assert user_response.status_code == 200
    assert [order["id"] for order in user_response.json()] == [1]
    assert all(order["mock"] is True for order in user_response.json())

    manager_response = client_for("manager@example.com").get("/api/v1/mock/orders/")
    assert manager_response.status_code == 200
    assert [order["id"] for order in manager_response.json()] == [1, 2]


@pytest.mark.django_db
def test_order_detail_checks_existence_before_permission(demo_data):
    client = client_for("user@example.com")

    own_response = client.get("/api/v1/mock/orders/1/")
    foreign_response = client.get("/api/v1/mock/orders/2/")
    missing_response = client.get("/api/v1/mock/orders/999/")

    assert own_response.status_code == 200
    assert own_response.json()["id"] == 1
    assert own_response.json()["mock"] is True
    assert foreign_response.status_code == 403
    assert missing_response.status_code == 404


@pytest.mark.django_db
def test_order_create_requires_create_permission_and_valid_payload(demo_data):
    payload = {"title": "Order C", "amount": "450.50"}

    guest_response = client_for("guest@example.com").post(
        "/api/v1/mock/orders/",
        payload,
        format="json",
    )
    user_response = client_for("user@example.com").post(
        "/api/v1/mock/orders/",
        payload,
        format="json",
    )
    invalid_response = client_for("user@example.com").post(
        "/api/v1/mock/orders/",
        {"title": "", "amount": "-1.00"},
        format="json",
    )
    incomplete_response = client_for("user@example.com").post(
        "/api/v1/mock/orders/",
        {"amount": "10.00"},
        format="json",
    )

    assert guest_response.status_code == 403
    assert user_response.status_code == 200
    assert user_response.json()["mock"] is True
    assert user_response.json()["detail"] == "Order would be created"
    assert invalid_response.status_code == 400
    assert incomplete_response.status_code == 400


@pytest.mark.django_db
def test_order_update_supports_own_and_all_permissions(demo_data):
    payload = {"title": "Updated order"}
    user_client = client_for("user@example.com")
    manager_client = client_for("manager@example.com")

    own_response = user_client.patch(
        "/api/v1/mock/orders/1/",
        payload,
        format="json",
    )
    foreign_response = user_client.patch(
        "/api/v1/mock/orders/2/",
        payload,
        format="json",
    )
    manager_response = manager_client.patch(
        "/api/v1/mock/orders/1/",
        payload,
        format="json",
    )

    assert own_response.status_code == 200
    assert own_response.json() == {
        "mock": True,
        "detail": "Order would be updated",
        "order_id": 1,
    }
    assert foreign_response.status_code == 403
    assert manager_response.status_code == 200


@pytest.mark.django_db
def test_order_delete_supports_own_and_all_permissions(demo_data):
    user_client = client_for("user@example.com")
    manager_client = client_for("manager@example.com")
    admin_client = client_for("admin@example.com")

    own_response = user_client.delete("/api/v1/mock/orders/1/")
    foreign_response = user_client.delete("/api/v1/mock/orders/2/")
    manager_response = manager_client.delete("/api/v1/mock/orders/1/")
    admin_response = admin_client.delete("/api/v1/mock/orders/2/")

    assert own_response.status_code == 200
    assert own_response.json() == {
        "mock": True,
        "detail": "Order would be deleted",
        "order_id": 1,
    }
    assert foreign_response.status_code == 403
    assert manager_response.status_code == 403
    assert admin_response.status_code == 200


@pytest.mark.django_db
def test_products_are_authorized_independently_from_orders(demo_data):
    user_client = client_for("user@example.com")
    admin_client = client_for("admin@example.com")

    assert user_client.get("/api/v1/mock/orders/").status_code == 200
    assert user_client.get("/api/v1/mock/products/").status_code == 403

    admin_response = admin_client.get("/api/v1/mock/products/")
    assert admin_response.status_code == 200
    assert admin_response.json()
    assert all(product["mock"] is True for product in admin_response.json())
