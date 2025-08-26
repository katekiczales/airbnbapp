from __future__ import annotations
from pathlib import Path
from typing import List, Dict
import json
from datetime import datetime

INTERACTIONS_PATH = Path(__file__).resolve().parents[1] / "data" / "interactions.json"
EVENT_WEIGHTS = {"view": 1, "save": 3}

# ======================================================================================================================
# HELPER FUNCTIONS (for internal use)
# ======================================================================================================================

def _now_iso() -> str:
    now = datetime.now()
    return now.isoformat() + "Z"

def _ensure_data_file() -> None:
    if not INTERACTIONS_PATH.exists():
        INTERACTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
        INTERACTIONS_PATH.write_text("[]", encoding="utf-8")

def load_interactions() -> List[Dict]:
    _ensure_data_file()
    try:
        return json.loads(INTERACTIONS_PATH.read_text(encoding="utf-8"))
    except RuntimeError:
        return []

def save_interactions(rows: List[Dict]) -> None:
    INTERACTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    INTERACTIONS_PATH.write_text(json.dumps(rows, indent=2), encoding="utf-8")

def log_interaction(user_id: str, property_id: str, event: str) -> Dict:
    """
    Append a single interaction to the list of events

    :return: The interaction record
    """
    if event not in EVENT_WEIGHTS:
        raise ValueError("event must be 'view' or 'save'")
    rows = load_interactions()
    rec = {
        "ts": _now_iso(),
        "user_id": user_id,
        "property_id": property_id,
        "event": event,
        "weight": EVENT_WEIGHTS[event],
    }
    rows.append(rec)
    save_interactions(rows)
    return rec

# ======================================================================================================================
# API-STYLE FUNCTIONS
# ======================================================================================================================

def log_view(user_id: str, property_id: str) -> Dict:
    """
    Log a view event
    :param user_id: the user's id
    :param property_id: the property's id
    :return: the event record
    """
    return log_interaction(user_id, property_id, "view")

def log_save(user_id: str, property_id: str) -> Dict:
    """
    Log a save event
    :param user_id: the user's id
    :param property_id: the property's id
    :return: the event record
    """
    return log_interaction(user_id, property_id, "save")

def reset_interactions_file() -> None:
    """
    Clear all interaction data. For dev/testing purposes.

    :return: None
    """
    INTERACTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    INTERACTIONS_PATH.write_text("[]", encoding="utf-8")

def get_user_interactions(user_id: str) -> List[Dict]:
    """
    Get all interactions for a given user

    :param user_id: the user id
    :return: the interactions for that user
    """
    return [r for r in load_interactions() if r.get("user_id") == user_id]