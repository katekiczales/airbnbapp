import json
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict
from typing import Any

from interactions_service import load_interactions
from properties_service import ensure_properties
from users_service import User

TOP_N_PROPERTIES = 5
DATA_PATH = Path(__file__).parent / "data" / "records.json"

"""
This service handles all recommender logic for the app's recommender. This include collaborative filtering and 
standard recommender filtering (as discussed in class).
"""

class UserPrefs:
    def __init__(
        self,
        budget: float,
        preferred_environment: str,
        weight_afford: float = 0.4,
        weight_env: float = 0.2,
        weight_prefs: float = 0.4,
    ):
        self.budget = budget
        self.preferred_environment = preferred_environment
        self.weight_afford = weight_afford
        self.weight_env = weight_env
        self.weight_prefs = weight_prefs

    def normalize_weights(self):
        total = self.weight_afford + self.weight_env + self.weight_prefs
        if total == 0:
            self.weight_afford, self.weight_env, self.weight_prefs = 1.0, 0.0, 0.0
        else:
            self.weight_afford /= total
            self.weight_env /= total
            self.weight_prefs /= total

    def __repr__(self):
        return (
            f"UserPrefs(budget={self.budget}, "
            f"preferred_environment={self.preferred_environment!r}, "
            f"w_afford={self.weight_afford:.3f}, w_env={self.weight_env:.3f})"
            f"w_prefs={self.weight_prefs:.3f})"
        )

# ======================================================================================================================
# HELPER FUNCTIONS (for internal use)
# ======================================================================================================================

def score_properties(df, prefs, affinity: dict[str, float] | None = None):
    """
    Score the properties based on affordability, environment, and affinity preferences
    :param df: the properties
    :param prefs: the user preferences
    :param affinity: the generated user affinity
    :return: the scored properties
    """
    df = df.copy()

    # Affordability (vectorized on the numeric column)
    budget = prefs.budget
    prices = df["nightly_price"].to_numpy(dtype=float)
    afford = np.clip((budget - prices) / max(budget, 0.001), 0.0, 1.0) #avoid division by 0; clip

    # Environment: 1 if preferred_environment in tags, else 0 (no apply; list comprehension)
    if prefs.preferred_environment:
        env = np.array(
            [1.0 if prefs.preferred_environment in tags else 0.0 for tags in df["tags"]],
            dtype=float
        )
    else:
        env = np.zeros(len(df), dtype=float)

    # If affinity exists, score the properties using it
    if affinity:
        pref_scores = []
        for feats, tags in zip(df.get("features", []), df.get("tags", [])):
            toks = []
            if isinstance(feats, list):
                toks += [str(t).strip().lower() for t in feats]
            if isinstance(tags, list):
                toks += [str(t).strip().lower() for t in tags]
            vals = [affinity[t] for t in toks if t in affinity]
            pref_scores.append(float(sum(vals) / len(vals)) if vals else 0.0)
        prefs_score = np.array(pref_scores, dtype=float)
    else:
        prefs_score = np.zeros(len(df), dtype=float)

    # Weighted score
    df["afford_score"] = afford
    df["env_score"] = env
    df["prefs_score"] = prefs_score  # NEW
    df["match_score"] = (
        prefs.weight_afford * df["afford_score"] +
        prefs.weight_env    * df["env_score"] +
        prefs.weight_prefs * df["prefs_score"]
    )

    return df.sort_values("match_score", ascending=False)

def run_vectorization(user: User, n: int):
    """
    Run vectorization for the properties
    :param user: the current user
    :param n: the number of properties to return
    :return: the top n properties
    """
    properties = ensure_properties()

    df = pd.DataFrame(properties)

    prefs = UserPrefs(
        user.budget_max,
        user.preferred_env,
        weight_afford=10,
        weight_env=5,
        weight_prefs=3,
    )
    prefs.normalize_weights()

    affinity = build_user_affinity(user.id, df)

    scored = score_properties(df, prefs, affinity=affinity)

    top = scored.head(n).copy()

    top["score"] = ((top["match_score"] * 100).round(1)).astype(str) + "%"

    cols = [
        "property_id", "location", "type", "nightly_price",
        "features", "tags",
        "score"
    ]
    top = top[cols]

    top.reset_index(drop=True, inplace=True)
    out = top.to_dict(orient="records")
    with open(DATA_PATH, "w") as f:
        json.dump(out, f, indent=2)

    return out

def build_user_affinity(user_id: str, df: pd.DataFrame) -> dict[str, float]:
    """
    Builds affinity for the given user using tokens (which are either property features or tags).
    Each view event contributes 1 and each save event contributes 3, normalized over the range [0, 1].

    :param user_id: the user id
    :param df: the properties
    :return: the user's affinity as a dictionary
    """

    # Only look at the interactions for the current user
    rows = [r for r in load_interactions() if r.get("user_id") == user_id]
    if not rows:
        return {}

    # Make a dictionary containing features and tags for each property
    by_id: dict[str, tuple[list[Any], list[Any]]] = {}
    for rec in df.to_dict(orient="records"):
        by_id[rec.get("property_id")] = (rec.get("features") or [], rec.get("tags") or [])

    # Look at each relevant interaction
    counts: dict[str, float] = defaultdict(float)
    for row in rows:
        pid = row.get("property_id")
        if pid not in by_id:
            continue
        weight = row.get("weight")
        if weight is None:
            weight = 3.0 if row.get("event") == "save" else 1.0

        # Create a list of the properties features and tags with appropriate normalized weights
        feats, tags = by_id[pid]
        tokens = [*(feats or []), *(tags or [])]
        for token in tokens:
            t = str(token).strip().lower()
            if t:
                counts[t] += float(weight)

    if not counts:
        return {}

    m = max(counts.values()) or 1.0
    return {tok: cnt / m for tok, cnt in counts.items()}

# ======================================================================================================================
# API-STYLE FUNCTIONS
# ======================================================================================================================

def produce_top_matches(user: User, n:int=TOP_N_PROPERTIES):
    """
    Return the top n properties for the current user. This function exists to ensure separation between
    frontend-serving functions and backend functions for code cleanliness.

    :param user: the current user
    :param n: the number of properties to return
    :return: the top n properties for the current user
    """
    return run_vectorization(user, n)