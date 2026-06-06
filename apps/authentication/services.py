import bcrypt


def hash_password(raw_password: str) -> str:
    password_bytes = raw_password.encode("utf-8")
    password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt())

    return password_hash.decode("utf-8")


def verify_password(raw_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(
        raw_password.encode("utf-8"),
        password_hash.encode("utf-8"),
    )
