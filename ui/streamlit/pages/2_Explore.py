import streamlit as st
import sys, pathlib
import pandas as pd

from interactions_service import log_save, get_user_interactions, log_view
from properties_service import ensure_properties

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sessions_service import get_current_user

"""
On this page, users can explore all properties available on the app. They can also save properties and view
saved properties.
"""

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
if not props:
    st.warning("No properties available.")
    st.stop()

labels = [f"{p['property_id']} — {p['location']} (${p['nightly_price']})" for p in props]

idx = st.selectbox(
    "Choose a place to save",
    options=range(len(props)),
    format_func=lambda i: labels[i],
    index=None,
    placeholder="— Select a property —",
    key="prop_select_idx",
)

if idx is None:
    st.info("Pick a property to see details.")
    st.stop()

selected = props[idx]
prop_id = selected["property_id"]

st.subheader("Selected property")
st.markdown(
    f"**ID:** {prop_id}  \n"
    f"**Location:** {selected.get('location','—')}  \n"
    f"**Type:** {selected.get('type','—')}  \n"
    f"**Nightly price:** ${selected.get('nightly_price','—')}  \n"
    f"**Capacity:** {selected.get('capacity','—')}  \n"
    f"**Features:** {', '.join(selected.get('features') or [])}  \n"
    f"**Tags:** {', '.join(selected.get('tags') or [])}"
)

col1, _ = st.columns([1,3])
with col1:
    if st.button("Save this property"):
        rec = log_save(user.id, prop_id)
        st.success(f"Saved {prop_id} at {rec['ts']}")

# Only log a view when the property is actually clicked (i.e., don't log the default)
prev_id = st.session_state.get("last_viewed_prop_id")
if prev_id is None:
    st.session_state["last_viewed_prop_id"] = prop_id
elif prop_id != prev_id:
    log_view(user.id, prop_id)
    st.session_state["last_viewed_prop_id"] = prop_id

st.divider()

with st.expander("Your recent interactions"):
    rows = get_user_interactions(user.id)
    st.write(rows[-10:] if rows else "None yet")

st.divider()
st.subheader("Your saved properties")

props = ensure_properties()
by_id = {p["property_id"]: p for p in props}

events = [r for r in get_user_interactions(user.id) if r.get("event") == "save"]
latest = {}
for r in events:
    pid = r["property_id"]
    if pid not in latest or r["ts"] > latest[pid]["ts"]:
        latest[pid] = r

saved_props = [by_id[pid] for pid in latest.keys() if pid in by_id]

if not saved_props:
    st.caption("You haven’t saved any places yet.")
else:
    import pandas as pd
    df = pd.DataFrame(saved_props)[
        ["property_id", "location", "type", "nightly_price", "capacity", "tags", "features"]
        ]
    st.dataframe(
        df.rename(columns={
            "property_id": "Property ID",
            "location": "Location",
            "type": "Type",
            "nightly_price": "Nightly Price",
            "capacity": "Capacity",
            "tags": "Tags",
            "features": "Features",
        }),
        use_container_width=True,
        hide_index=True,
    )