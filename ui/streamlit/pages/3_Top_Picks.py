import streamlit as st
import sys, pathlib
import pandas as pd

from recommender_service import produce_top_matches
from sessions_service import get_current_user

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# On this page, users can view the top properties recommended to them.

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

with st.spinner("Computing your top picks..."):
    props = produce_top_matches(user, n=5)

df = pd.DataFrame(props)

if df.empty:
    st.info("No properties were found in data/records.json")
else:
    st.dataframe(
        df[["property_id", "location", "type", "nightly_price", "tags", "features", "score"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "property_id": "Property ID",
            "location": "Location",
            "type": "Type",
            "nightly_price": st.column_config.NumberColumn("Nightly Price", format="$%d"),
            "tags": "Tags",
            "features": "Features",
            "score": "Percent Match",
        },
    )