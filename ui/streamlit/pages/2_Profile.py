import sys, pathlib, datetime as dt
import streamlit as st

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sessions import get_current_user, logout
from users import update_user, delete_user

st.title("Your Profile")

# AUTHENTICATION GATE
token = st.session_state.get("token")
user = get_current_user(token) if token else None
if not user:
    st.warning("You must be logged in to access your profile.")
    st.write("Go to **Home** (left sidebar) to sign up or log in.")
    st.stop()

st.caption(f"Logged in as **{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}** — {user.email}")

# HELPER FUNCTIONS
def _to_date(s: str | None):
    if not s:
        return None
    try:
        return dt.date.fromisoformat(s[:10])
    except Exception:
        return None

def _iso_or_none(d: dt.date | None):
    return d.isoformat() if d else None

# Prefill values
pref_env_val = user.preferred_env or ""
group_size_val = user.group_size if user.group_size is not None else 0
budget_min = int(user.budget_min) if user.budget_min is not None else 0
budget_max = int(user.budget_max) if user.budget_max is not None else 0
travel_start_date = _to_date(user.travel_start)
travel_end_date = _to_date(user.travel_end)

st.divider()
st.subheader("Edit profile")

with st.form("profile_form", clear_on_submit=False):
    colA, colB = st.columns(2)
    with colA:
        first_name = st.text_input("First name", value=getattr(user, "first_name", "") or "")
    with colB:
        last_name = st.text_input("Last name", value=getattr(user, "last_name", "") or "")

    email = st.text_input("Email", value=user.email or "")

    env = st.selectbox(
        "Preferred environment",
        ["", "lake", "mountain", "beach", "city"],
        index=(["", "lake", "mountain", "beach", "city"].index(pref_env_val) if pref_env_val in ["lake","mountain","beach","city"] else 0),
        help="Used by recommendations."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        group_size = st.number_input("Group size", min_value=0, max_value=50, value=group_size_val, step=1)
    with col2:
        bmin = st.number_input("Budget min", min_value=0, max_value=10000, value=budget_min, step=10)
    with col3:
        bmax = st.number_input("Budget max", min_value=0, max_value=10000, value=max(budget_max, budget_min), step=10)

    cold1, cold2 = st.columns(2)
    with cold1:
        tstart = st.date_input("Travel start (optional)", value=travel_start_date)
    with cold2:
        tend = st.date_input("Travel end (optional)", value=travel_end_date)

    submitted = st.form_submit_button("Save changes")
    if submitted:
        try:
            if bmax < bmin:
                raise ValueError("Budget max must be ≥ budget min.")
            fields = {
                "email": email.strip(),
                "first_name": first_name.strip(),
                "last_name": last_name.strip(),
                "preferred_env": (env or None),
                "group_size": int(group_size) if group_size is not None else None,
                "budget_min": int(bmin),
                "budget_max": int(bmax),
                "travel_start": _iso_or_none(tstart),
                "travel_end": _iso_or_none(tend),
            }
            updated = update_user(user.id, **fields)
            st.success("Profile updated.")
            st.rerun()
        except Exception as e:
            st.error(f"Update failed: {e}")

st.divider()
st.subheader("Delete account")

with st.expander("Delete my account", expanded=False):
    st.warning("This will permanently delete your account and sign you out.")
    confirm = st.text_input("Type DELETE to confirm")
    if st.button("Delete account"):
        if confirm.strip().upper() != "DELETE":
            st.error("Type DELETE to confirm.")
        else:
            try:
                ok = delete_user(user.id)
                if ok:
                    if token:
                        logout(token)
                    st.session_state.pop("token", None)
                    st.success("Your account has been deleted.")
                    st.stop()
                else:
                    st.error("No account was deleted (user not found).")
            except Exception as e:
                st.error(f"Delete failed: {e}")