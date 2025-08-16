from __future__ import annotations
import json, secrets, uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from users import get_user_by_email, get_user_by_id, User
from auth import verify_user_password

# High-level design:
# - Owns session tokens
# - Uses users.py and auth.py for user retrieval and authentication


SESSIONS_PATH = Path(__file__).parent / "data" / "sessions.json"

# ======================================================================================================================
# HELPERS
# ======================================================================================================================

def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds") + "Z"

def _load_all_sessions() -> list[dict]:
    try:
        return json.loads(SESSIONS_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except json.decoder.JSONDecodeError:
        return []

def _save_all_sessions(rows: list[dict]) -> None:
    SESSIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SESSIONS_PATH.write_text(json.dumps(rows, indent=2), encoding="utf-8")

def _get_session_by_token(token: str) -> Optional[dict]:
    for row in _load_all_sessions():
        if row.get("token") == token:
            return row
    return None

# ======================================================================================================================
# API-STYLE FUNCTIONS
# ======================================================================================================================

def reset_sessions_file() -> None:
    _save_all_sessions([])

# Create and save a new active session for the given user
def create_session(user_id: str) -> dict:
    rows = _load_all_sessions()
    row = {
        "session_id": str(uuid.uuid4()),
        "user_id": user_id,
        "token": secrets.token_urlsafe(32),
        "active": True,
        "created_at": _now_iso(),
        "expires_at": None,
    }

    rows.append(row)
    _save_all_sessions(rows)
    return row

# Verify the login credentials and create a new session if verified
def login(email: str, password: str) -> Tuple[str, str]:
    user = get_user_by_email(email)
    if not user:
        raise ValueError("Invalid email")
    if not verify_user_password(user.id, password):
        raise ValueError("Invalid password")
    session = create_session(user.id)
    return session["token"], user.id

# Return the user who is logged in for this token, or None if there is no active session
def get_current_user(token: str) -> Optional[User]:
    session = _get_session_by_token(token)
    if not session or not session.get("active"):
        return None
    return get_user_by_id(session["user_id"])

# Log out the current user by invalidating their token
# Return true if user was logged out
def logout(token: str) -> bool:
    rows = _load_all_sessions()
    changed = False
    for i, row in enumerate(rows):
        if row.get("token") == token and row.get("active"):
            row["active"] = False
            row["ended_at"] = _now_iso()
            rows[i] = row
            changed = True
            break
    if changed:
        _save_all_sessions(rows)
    return changed

# ======================================================================================================================
# TESTS
# ======================================================================================================================

if __name__ == "__main__":
    from users import reset_users_file, set_user_password_hash, create_user
    from auth import signup, change_password

    # Set up a clean file system for tests
    try:
        reset_users_file()
    except Exception:
        pass
    try:
        reset_sessions_file()
    except Exception:
        pass

    # Create a user and log in
    u = signup(email="alice@example.com", first_name="Alice", last_name="Smith", password="secret123", preferred_env="lake")
    print("User:", u.email, u.id)

    token, uid = login("alice@example.com", "secret123")
    print("Token:", token[:16] + "...", "User ID:", uid)

    cu = get_current_user(token)
    print("Current user:", cu.email if cu else None)

    # Log out the user and confirm logout was successful
    logout(token)
    cu2 = get_current_user(token)
    print("After logout, current user:", cu2)