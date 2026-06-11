import pytest
from django.db import IntegrityError, transaction
from apps.users.models import User
from uuid import UUID


def test_user_model_exists():
    assert User


@pytest.mark.django_db
def test_user_reports_authenticated_state():
    user = User.objects.create(
        email="user@example.com",
        password_hash="hash",
        first_name="Иван",
        last_name="Иванов",
    )

    assert user.is_authenticated is True


@pytest.mark.django_db
def test_user_email_must_be_unique():
    User.objects.create(email="user@example.com")
    with pytest.raises(IntegrityError):
        User.objects.create(email="user@example.com")


@pytest.mark.django_db
def test_user_email_must_be_unique_ignoring_case():
    User.objects.create(email="user@example.com")

    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create(email="USER@example.com")


@pytest.mark.django_db
def test_user_gets_unique_uuid():
    first_user = User.objects.create(email="first@example.com")
    second_user = User.objects.create(email="seconde@example.com")
    assert isinstance(first_user.id, UUID)
    assert first_user.id != second_user.id


@pytest.mark.django_db
def test_user_stores_profile_data():
    user = User.objects.create(
        email="ivan@example.com",
        password_hash="hashed-password",
        first_name="Иван",
        last_name="Иванов",
        middle_name="Иванович",
    )
    assert user.first_name == "Иван"
    assert user.last_name == "Иванов"
    assert user.middle_name == "Иванович"
    assert user.password_hash == "hashed-password"
    assert user.is_active is True
    assert user.deleted_at is None
    assert user.created_at is not None
    assert user.updated_at is not None
