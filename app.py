import json
from pathlib import Path

from users import get_user_by_id, get_user_by_email, get_user_preferences, create_user, reset_users_file
from sessions import login, get_current_user, reset_sessions_file
from auth import signup

# Path to the properties data
DATA_PATH = Path(__file__).parent / "data" / "properties.json"

# For development
DEMO_EMAIL = "janedoe@example.com"
DEMO_PASSWORD = "secret123"
DEMO_FIRST = "Jane"
DEMO_LAST = "Doe"

# Load the properties from the json file
# Return the properties as a list of dictionaries
def load_properties() -> list[dict]:
    with open(DATA_PATH, "r") as file:
        properties = json.load(file)
        # print(json.dumps(properties, indent=2))
        return properties

# Placeholder for more complex recommending logic
def recommend(user_id: str, properties: list[dict], top_n) -> list[dict]:
    user_preferences = get_user_preferences(user_id)

    group_size = user_preferences["group_size"]
    preferred_env = user_preferences["preferred_env"]
    budget_min = user_preferences["budget_min"]
    budget_max = user_preferences["budget_max"]
    travel_start = user_preferences["travel_start"]
    travel_end = user_preferences["travel_end"]

    filtered = [
        props for props in properties
        if (preferred_env is None or preferred_env in props.get("tags", []))
        and budget_min <= props["nightly_price"] <= budget_max
    ]

    filtered.sort(key=lambda props: props["nightly_price"])
    return filtered[:top_n]

# Called when a user first arrives to the app; handles either their login or signup
def handle_login_or_signup():
    user = get_user_by_email(DEMO_EMAIL)
    if user:
        return user
    return signup(
        email=DEMO_EMAIL,
        first_name=DEMO_FIRST,
        last_name=DEMO_LAST,
        password=DEMO_PASSWORD,
        preferred_env="lake",
        budget_min=100,
        budget_max=300,
    )

# Main
def main():
    reset_users_file()
    reset_sessions_file()

    user = handle_login_or_signup()

    token, uid = login(DEMO_EMAIL, DEMO_PASSWORD)
    print(f"[Login] Session token issued for user_id={uid}: {token[:12]}...")

    current = get_current_user(token)
    if not current:
        print("[Auth Gate] Not authenticated → redirect to login page")
        return
    print(f"[Auth Gate] Current user: {current.first_name} {current.last_name}")

    props = load_properties()
    n_wanted_recommendations = 3
    recommendations = recommend(current.id, props, n_wanted_recommendations)

    print(f"\nTop {n_wanted_recommendations} recommendations:")
    print(json.dumps(recommendations, indent=2))

if __name__ == "__main__":
    main()