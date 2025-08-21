import json
import numpy as np
import pandas as pd
from pathlib import Path

from users_service import User

TOP_N_PROPERTIES = 5
DATA_PATH = Path(__file__).parent / "data" / "records.json"

"""
Handle all logic for the app's recommender
"""

# Add features and weight_features back it later once added to User
class UserPrefs:
    def __init__(
        self,
        budget: float,
        preferred_environment: str,   # e.g., 'lakefront', 'urban', ...
        # must_have_features: None,
        weight_afford: float = 0.5,
        weight_env: float = 0.3,
        # w_feat: float = 0.2,
    ):
        self.budget = budget
        self.preferred_environment = preferred_environment
        # self.must_have_features = must_have_features
        self.weight_afford = weight_afford
        self.weight_env = weight_env
        # self.w_feat = w_feat

    def normalize_weights(self):
        total = self.weight_afford + self.weight_env # + self.w_feat
        if total == 0:
            # self.weight_afford, self.w_env, self.w_feat = 1.0, 0.0, 0.0
            self.weight_afford, self.weight_env = 1.0, 0.0
        else:
            self.weight_afford /= total
            self.weight_env /= total
            # self.w_feat /= total

    def __repr__(self):
        return (
            f"UserPrefs(budget={self.budget}, "
            f"preferred_environment={self.preferred_environment!r}, "
            # f"must_have_features={self.must_have_features}, "
            # f"w_afford={self.weight_afford:.3f}, w_env={self.weight_env:.3f}, w_feat={self.w_feat:.3f})"
            f"w_afford={self.weight_afford:.3f}, w_env={self.weight_env:.3f})"
        )

def score_properties(df, prefs):
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

    # Feature overlap: |must_have ∩ features| / |must_have| (no apply; list comprehension)
    # if prefs.must_have_features:
    #     mh = {f.lower() for f in prefs.must_have_features}
    #     mh_len = max(len(mh), 1)
    #     feat = np.array([
    #         len(mh.intersection([f.lower() for f in fs])) / mh_len
    #         for fs in df["features"]
    #     ], dtype=float)
    # else:
    #     feat = np.zeros(len(df), dtype=float)

    # Weighted score
    df["afford_score"] = afford
    df["env_score"] = env
    # df["feat_score"] = feat
    df["match_score"] = (
        prefs.weight_afford * df["afford_score"] +
        prefs.weight_env    * df["env_score"]
        # prefs.w_feat   * df["feat_score"]
    )

    return df.sort_values("match_score", ascending=False)

def run_vectorization(user: User, n: int):
    properties = get_properties()

    df = pd.DataFrame(properties)

    prefs = UserPrefs(user.budget_max, user.preferred_env,
                      weight_afford=10, weight_env=5)
    prefs.normalize_weights()
    print(prefs)

    scored = score_properties(df, prefs)
    scored[["property_id", "location", "type", "nightly_price", "afford_score", "env_score",
            "match_score"]].head(10)
    # scored[["property_id", "location", "type", "nightly_price", "afford_score", "env_score", "feat_score",
    #         "match_score"]].head(10)

    cols = ["property_id", "location", "type", "nightly_price", "features", "tags", "match_score"]
    top = scored.head(TOP_N_PROPERTIES)[cols]
    top = top.assign(match_score=top["match_score"].round(3))
    top.reset_index(drop=True)

    # Save the top n properties to json for use on frontend
    out = top.to_dict(orient="records")
    with open(DATA_PATH, "w") as f:
        json.dump(out, f, indent=2)
    print("Saved top_matches.json with", len(out), "records.")
    print(json.dumps(out[:2], indent=2))
    return out

def produce_top_matches(user: User, n:int=TOP_N_PROPERTIES):
    return run_vectorization(user, n)

# if __name__ == "__main__":
    # top_properties = produce_top_matches()
    # print(top_properties)