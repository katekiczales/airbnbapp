import streamlit as st
import sys, pathlib
import pandas as pd

from recommender_service import produce_top_matches
from sessions_service import get_current_user

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.title("Top Picks")

# ---- Authentication gate ----
token = st.session_state.get("token")
user = get_current_user(token) if token else None
if not user:
    st.warning("You must be logged in to view property listings.")
    st.write("Go to **Home** to sign up or log in.")
    st.stop()

st.caption(f"You are logged in as {getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')} — {user.email}")

# ---- Load and show properties ----
props = produce_top_matches(user)
df = pd.DataFrame(props)

if df.empty:
    st.info("No properties were found in data/records.json")
else:
    st.dataframe(
        df[["property_id", "location", "type", "nightly_price", "tags", "features"]],
        use_container_width=True,
        hide_index=True,
    )