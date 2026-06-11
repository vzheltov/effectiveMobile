import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_openapi_schema_and_swagger_are_available():
    schema_response = APIClient().get("/api/schema/?format=json")
    docs_response = APIClient().get("/api/docs/")

    assert schema_response.status_code == 200
    assert docs_response.status_code == 200

    schema = schema_response.json()
    assert schema["components"]["securitySchemes"]["BearerAuth"] == {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    assert "/api/v1/auth/login/" in schema["paths"]
    assert "/api/v1/access/rules/" in schema["paths"]
    assert "/api/v1/mock/orders/" in schema["paths"]
