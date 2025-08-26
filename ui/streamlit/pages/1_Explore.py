import streamlit as st
import sys, pathlib
import pandas as pd

from interactions_service import log_save, get_user_interactions, log_view
from properties_service import ensure_properties

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sessions_service import get_current_user

st.title("Explore Property Listings")

# ---- Authentication gate ----
token = st.session_state.get("token")
user = get_current_user(token) if token else None
if not user:
    st.warning("You must be logged in to view property listings.")
    st.write("Go to **Home** to sign up or log in.")
    st.stop()

st.caption(f"You are logged in as {getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')} — {user.email}")

# ---- Load and show properties ----

props = ensure_properties()
labels = [f"{p['property_id']} — {p['location']} (${p['nightly_price']})" for p in props]

idx = st.selectbox("Choose a place to save", range(len(props)), format_func=lambda i: labels[i], key="prop_select_idx")
selected = props[idx]
prop_id = selected["property_id"]

st.subheader("Selected property")
st.markdown(
    f"**ID:** {prop_id}  \n"
    f"**Location:** {selected.get('location')}  \n"
    f"**Type:** {selected.get('type')}  \n"
    f"**Nightly price:** ${selected.get('nightly_price')}  \n"
    f"**Capacity:** {selected.get('capacity')}  \n"
    f"**Features:** {', '.join(selected.get('features', []))}  \n"
    f"**Tags:** {', '.join(selected.get('tags', []))}"
)

col1, _ = st.columns([1,3])
with col1:
    if st.button("Save this property"):
        # TODO: let them see saved properties
        rec = log_save(user.id, prop_id)
        st.success(f"Saved {prop_id} at {rec['ts']}")

# Only log a view when the property is actually clicked (i.e., don't log the default)
prev_id = st.session_state.get("last_viewed_prop_id")
if prev_id is None:
    st.session_state["last_viewed_prop_id"] = prop_id
elif prop_id != prev_id:
    log_view(user.id, prop_id)
    st.session_state["last_viewed_prop_id"] = prop_id

with st.expander("Your recent interactions"):
    rows = get_user_interactions(user.id)
    st.write(rows[-10:] if rows else "None yet")