from __future__ import annotations
import os, hashlib, binascii
from datetime import datetime
from users import User, get_user_by_email, create_user, set_user_password_hash, get_user_by_id
import hmac

_ALGO = "pbkdf2_sha256"
_ITER = 310000

# High-level design:
# - Owns the password logic
# - No direct file I/O for users

# ======================================================================================================================
# HELPERS
# ======================================================================================================================

def _now_iso() -> str:
    return datetime.isoformat(timespec="seconds")

# Returns hashed password in the form 'pbkdf2_sha256$ITER$SALT_HEX$HASH_HEX'
def _hash_password(plain_password: str) -> str:
    if not isinstance(plain_password, str) or len(plain_password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, _ITER)
    return f"{_ALGO}${_ITER}${binascii.hexlify(salt).decode()}${binascii.hexlify(dk).decode()}"

def _verify_password(plain_password: str, stored_password: str) -> bool:
    try:
        algo, iter_s, salt_hex, hash_hex = stored_password.split("$", 3)
        if algo != _ALGO:
            return False

        iters = int(iter_s)
        salt = binascii.unhexlify(salt_hex.encode())
        expected = binascii.unhexlify(hash_hex.encode())

        dk = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iters)

        return hmac.compare_digest(dk, expected)
    except Exception:
        return False

# ======================================================================================================================
# API-STYLE FUNCTIONS
# ======================================================================================================================

def signup(*, email: str, first_name: str, last_name: str, password: str, **optional_fields) -> User:
    if get_user_by_email(email):
        raise ValueError("A user with this email already exists")

    user = create_user(email=email, first_name=first_name, last_name=last_name, **optional_fields)
    return set_user_password_hash(user.id, _hash_password(password))

def verify_user_password(user_id: str, password: str) -> bool:
    user = get_user_by_id(user_id)
    print(user)
    if not user:
        raise ValueError(f"The user with user id {user_id} was not found")
    elif not user.password_hash:
        raise ValueError(f"The user with user id {user_id} has no password hash")
    return _verify_password(password, user.password_hash)

# First check the user's password, then if valid, update their password
def change_password(*, email: str, old_password: str, new_password: str) -> User:
    user = get_user_by_email(email)
    if not user:
        raise ValueError(f"User with email {email} not found")
    if not user.password_hash or not _verify_password(old_password, user.password_hash):
        raise ValueError("Current password is incorrect")
    if new_password == old_password:
        raise ValueError("New password must differ from the current password")
    return set_user_password_hash(user.id, _hash_password(new_password))

# ======================================================================================================================
# TESTS
# ======================================================================================================================
if __name__ == "__main__":
    from users import reset_users_file
    try:
        reset_users_file()
    except ValueError:
        pass

    test_user = signup(email="test@example.com", first_name="Jane", last_name="Doe", password="secret123", preferred_env="lake")
    print(test_user)
    # -> True
    print("Verify OK:", verify_user_password(test_user.id, "secret123"))
    # -> False
    print("Verify FAIL:", verify_user_password(test_user.id, "nope"))

    change_password(email="test@example.com", old_password="secret123", new_password="newpass456")
    # -> True
    print("Verify new:", verify_user_password(test_user.id, "newpass456"))

