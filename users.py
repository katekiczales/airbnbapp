import json
import uuid, copy
from pathlib import Path
from dataclasses import dataclass, asdict

# High-level design:
# - Owns the users record and JSON I/O for users
# - Knows nothing about hashing algorithms or sessions, does not write the hash, just stores it for a given user

# Path to the users data
DATA_PATH = Path(__file__).parent / "data" / "users.json"

USER_FIELDS = {
    "email", "first_name", "last_name", "group_size", "preferred_env",
    "budget_min", "budget_max", "travel_start", "travel_end"
}

# ----- User Data -----
# Only id, email, and name are required upfront, the others can be added later on.
# id: str
# email: str
# first_name: str
# last_name: str
# group_size: int | None
# preferred_env: str | None
# budget_min: int | None
# budget_max: int | None
# travel_start: str | None
# travel_end: str | None

@dataclass
class User:
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

# Load users data from the json file as a list of dictionaries
def _load_all() -> list[dict]:
    users =  json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return users

# Save users data to the json file
def _save_all(rows: list[dict]) -> None:
    DATA_PATH.write_text(json.dumps(rows, indent=2), encoding="utf-8")

# ======================================================================================================================
# API-STYLE FUNCTIONS (for internal and external use)
# ======================================================================================================================

# Convert users into User objects and return them
def list_users() -> list[User]:
    return [User(**row) for row in _load_all()]

# Return an existing user by id; if that user does not exist, return nothing
def get_user_by_id(user_id: str) -> User | None:
    for row in _load_all():
        if row["id"] == user_id:
            return User(**row)
    return None

# Return an existing user by email; if that user does not exist, return nothing
def get_user_by_email(email: str) -> User | None:
    for row in _load_all():
        if row["email"] == email:
            return User(**row)
    return None

# Create and return a new user
def create_user(*, email: str, first_name: str, last_name: str, **optional_fields) -> User:
    # Create a new user object with a randomly generated (but unique) id
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

# Update all given fields for the user
def update_user(user_id: str, **fields) -> User:
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

# Delete the user with the given user id
# Returns true if delete was successful, false otherwise (user not found)
def delete_user(user_id: str) -> bool:
    rows = _load_all()
    new_rows = [r for r in rows if r["id"] != user_id]
    if len(new_rows) == len(rows):
        return False
    _save_all(new_rows)
    return True

# Return the user's travel preferences
def get_user_preferences(user_id: str) -> dict:
    user = get_user_by_id(user_id)
    return {
        "group_size": user.group_size,
        "preferred_env": user.preferred_env,
        "budget_min": user.budget_min,
        "budget_max": user.budget_max,
        "travel_start": user.travel_start,
        "travel_end": user.travel_end
    }

# Reset the users file (for testing purposes)
def reset_users_file() -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text("[]", encoding="utf-8")

# Set a new password hash for the given user
def set_user_password_hash(user_id: str, password_hash: str) -> User:
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

