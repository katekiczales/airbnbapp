from __future__ import annotations
import json, secrets, uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from users_service import get_user_by_email, get_user_by_id, User
from auth_service import verify_user_password

SESSIONS_PATH = Path(__file__).parent / "data" / "sessions.json"

"""
Handles all sessions for the app. Does not do any authentication (uses authentication_service.py for this)
Does not do any direct user retrieval (uses users_service.py for this)
"""

# ======================================================================================================================
# HELPERS
# ======================================================================================================================

def _now_iso() -> str:
    """
      Returns the ISO 8601 formatted datetime string

      :return: the datetime string
    """
    return datetime.now().isoformat(timespec="seconds") + "Z"

def _load_all_sessions() -> list[dict]:
    """
      Loads all sessions from the sessions.json file

      :return: all sessions
    """
    try:
        return json.loads(SESSIONS_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except json.decoder.JSONDecodeError:
        return []

def _save_all_sessions(rows: list[dict]) -> None:
    """
      Saves all sessions to the sessions.json file

      :param rows: a list of sessions
      :return: None
    """
    SESSIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SESSIONS_PATH.write_text(json.dumps(rows, indent=2), encoding="utf-8")

def _get_session_by_token(token: str) -> Optional[dict]:
    """
      Return the session matching the given token

      :param token: the token
      :return: the session if found, None otherwise
    """
    for row in _load_all_sessions():
        if row.get("token") == token:
            return row
    return None

# ======================================================================================================================
# API-STYLE FUNCTIONS
# ======================================================================================================================

def reset_sessions_file() -> None:
    """
      Resets the sessions file to empty. Useful for re-setting the app.
    """
    _save_all_sessions([])

def create_session(user_id: str) -> dict:
    """
      Create and save a new active session for the gien user

      :param user_id: the user id
      :return: the created session
    """
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

def login(email: str, password: str) -> Tuple[str, str]:
    """
      Verify the login credentials and creates a new session if verified

      :param email: the email of the user
      :param password: the password of the user
      :return: a tuple of the token for the session and the user id
    """
    user = get_user_by_email(email)
    if not user:
        raise ValueError("Invalid email")
    if not verify_user_password(user.id, password):
        raise ValueError("Invalid password")
    session = create_session(user.id)
    return session["token"], user.id

def get_current_user(token: str) -> Optional[User]:
    """
      Retrieves the user who is logged in for the given token

      :param token: the token
      :return: User (if there is a session) or None
    """
    session = _get_session_by_token(token)
    if not session or not session.get("active"):
        return None
    return get_user_by_id(session["user_id"])

def logout(token: str) -> bool:
    """
    Logs out the current user matching the token by invalidating the token

    :param token: the token
    :return: TRUE if the user was logged out; FALSE otherwise
    """
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
    from users_service import reset_users_file
    from auth_service import signup

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