import json
import uuid, copy
from pathlib import Path
from dataclasses import dataclass, asdict

# Path to the users data
DATA_PATH = Path(__file__).parent / "data" / "users.json"

USER_FIELDS = {
    "email", "first_name", "last_name", "group_size", "preferred_env",
    "budget_min", "budget_max", "travel_start", "travel_end"
}

"""
Handles all user logic. Owns the users record and JSON I/O for users.
Has no knowledge of hashing algorithms or sessions. Just stores the hash for a given user.
"""

@dataclass
class User:
    """Stored user record for auth and recommendations.

    Attributes:
        id: Stable UUID string.
        email: The user's email. Used as login identifier (unique).
        first_name: The user's first name.
        last_name: The user's last name.
        group_size: The user's group size.
        preferred_env: The preferred environment for the user.
        budget_min: Nightly min budget in dollars.
        budget_max: Nightly max budget in dollars.
        travel_start: The user's travel start date.
        travel_end: The user's travel end date.
        password_hash: The user's password hash.
    """

    id: str
    email: str
    first_name: str
    last_name: str
    group_size: int | None = None
    preferred_env: str | None = None
    budget_min: int | None = None
    budget_max: int | None = None
    travel_start: str | None = None
    travel_end: str | None = None
    password_hash: str = ""

# ======================================================================================================================
# HELPER FUNCTIONS (for internal use)
# ======================================================================================================================

def _load_all() -> list[dict]:
    """
    Load all users data from the users.json file

    :return: data for all users
    """
    users =  json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return users

def _save_all(rows: list[dict]) -> None:
    """
    Save all users data to the users.json file

    :param rows: the data to be saved
    :return: None
    """
    DATA_PATH.write_text(json.dumps(rows, indent=2), encoding="utf-8")

# ======================================================================================================================
# API-STYLE FUNCTIONS (for internal and external use)
# ======================================================================================================================

def list_users() -> list[User]:
    """
    Convert all JSON users into a list of user objects

    :return: a list of user objects
    """
    return [User(**row) for row in _load_all()]

def get_user_by_id(user_id: str) -> User | None:
    """
    Get a user by ID

    :param user_id: the user's id
    :return: the user if found, None otherwise
    """
    for row in _load_all():
        if row["id"] == user_id:
            return User(**row)
    return None

def get_user_by_email(email: str) -> User | None:
    """
    Get a user by email
    :param email: the user's email
    :return: the user if found, None otherwise
    """
    for row in _load_all():
        if row["email"] == email:
            return User(**row)
    return None

def create_user(*, email: str, first_name: str, last_name: str, **optional_fields) -> User:
    """
    Create a new user
    :param email: the user's email
    :param first_name: the user's first name
    :param last_name: the user's last name
    :param optional_fields: fields representing the user's preferences (optional at time of signup)
    :return: the new user
    """

    # Assign the user a randomly generated (but random) id
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        first_name=first_name,
        last_name=last_name,
        **optional_fields
    )

    rows = _load_all()
    rows.append(asdict(user))
    _save_all(rows)
    return user

def update_user(user_id: str, **fields) -> User:
    """
    Update a user with the given fields (some of them may be changed)
    :param user_id: the users id
    :param fields: fields a user is able to update through the UI
    :return: the updated user
    """
    rows = _load_all()
    for i, row in enumerate(rows):
        if row["id"] == user_id:
            updated_user = copy.deepcopy(row)
            for key, value in fields.items():
                if key in USER_FIELDS:
                    updated_user[key] = value
            rows[i] = updated_user
            _save_all(rows)
            return User(**updated_user)
    raise KeyError(f"User with id {user_id} not found")

def delete_user(user_id: str) -> bool:
    """
    Delete a user
    :param user_id: the user's id
    :return: TRUE if deletion succeeded; otherwise, FALSE
    """
    rows = _load_all()
    new_rows = [r for r in rows if r["id"] != user_id]
    if len(new_rows) == len(rows):
        return False
    _save_all(new_rows)
    return True

def get_user_preferences(user_id: str) -> dict:
    """
    Return the user's preferences
    :param user_id: the user's id
    :return: the user's preferences
    """
    user = get_user_by_id(user_id)
    return {
        "group_size": user.group_size,
        "preferred_env": user.preferred_env,
        "budget_min": user.budget_min,
        "budget_max": user.budget_max,
        "travel_start": user.travel_start,
        "travel_end": user.travel_end
    }

def reset_users_file() -> None:
    """
    Reset the users file to empty. Useful for resetting the app.
    :return: None
    """
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text("[]", encoding="utf-8")

def set_user_password_hash(user_id: str, password_hash: str) -> User:
    """
    Update the user's password hash
    :param user_id: the user's id
    :param password_hash: the new password hash
    :return: the updated user
    """
    rows = _load_all()
    for i, row in enumerate(rows):
        if row["id"] == user_id:
            row["password_hash"] = password_hash
            rows[i] = row
            _save_all(rows)
            return User(**row)
    raise KeyError(f"User with id {user_id} not found")

# ======================================================================================================================
# TESTS
# ======================================================================================================================

if __name__ == "__main__":
    # Create a user
    u = create_user(email="alice@example.com", first_name="Alice", last_name="Summers", preferred_env="lake", budget_min=100, budget_max=250)
    print("Created:", u)

    # Read the user by email
    got = get_user_by_email("alice@example.com")
    print("Fetched:", got)

    # Update the user
    upd = update_user(u.id, group_size=4, budget_max=230)
    print("Updated:", upd)

    # List all users
    print("All users:", list_users())

    # Delete the user
    deleted = delete_user(u.id)
    print("Deleted:", deleted)

