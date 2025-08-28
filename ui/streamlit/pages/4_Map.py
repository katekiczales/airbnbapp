import sys, pathlib
import streamlit as st
import json

from properties_service import load_properties_from_disk
from visualization_service import get_map_dataframe

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sessions_service import get_current_user

"""
On this page, users can view a map showing the geographical distribution of properties.
"""

st.title("Property Listings Map")

# Auth gate
token = st.session_state.get("token")
user = get_current_user(token) if token else None
if not user:
    st.warning("You must be logged in to view the map. Go to Home to log in.")
    st.stop()

@st.cache_data(show_spinner=False)
def _map_df():
    return get_map_dataframe()

df = _map_df()
if df.empty:
    st.error("No mappable rows. Ensure your properties have numeric 'latitude' and 'longitude' attributes.")
    st.stop()

print(df)
st.map(df, latitude="lat", longitude="lon")

with st.expander("Shown points (first 50)"):
    st.dataframe(df.head(50), use_container_width=True, hide_index=True)