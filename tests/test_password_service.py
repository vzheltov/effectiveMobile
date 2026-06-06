from apps.authentication import services


def test_password_is_not_stored_as_plain_text():
    password_hash = services.hash_password("StrongPass123!")

    assert password_hash != "StrongPass123!"


def test_correct_password_is_accepted():
    password_hash = services.hash_password("StrongPass123!")

    assert services.verify_password("StrongPass123!", password_hash) is True


def test_wrong_password_is_rejected():
    password_hash = services.hash_password("StrongPass123!")

    assert services.verify_password("WrongPass123!", password_hash) is False
