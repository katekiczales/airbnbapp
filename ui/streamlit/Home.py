import streamlit as st
import sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from auth_service import signup
from sessions_service import login, get_current_user, logout

st.set_page_config(page_title="Summer Home Recommender", layout="centered")

from properties_service import ensure_properties

with st.spinner("Preparing property listings…"):
    _ = ensure_properties()

# HELPER FUNCTIONS
def is_authed() -> bool:
    return bool(st.session_state.get("token"))

def current_user():
    token = st.session_state.get("token")
    if not token:
        return None
    return get_current_user(token)

# UI CODE

msg = st.session_state.pop("flash_success", None)
if msg:
    st.success(msg)

st.title("Summer Home Recommender")
st.write("Log in or sign up below")

# Current session panel
with st.expander("Current session", expanded=True):
    if is_authed():
        user = current_user()
        if user:
            full_name = f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()
            st.success(f"Logged in as **{full_name or user.email}**  \nEmail: {user.email}")
            if st.button("Log out"):
                logout(st.session_state["token"])
                st.session_state.pop("token", None)
                st.rerun()
        else:
            st.warning("Session token present but no active session/user found. Try logging in again.")
    else:
        st.info("Not logged in.")

st.divider()

# Shows two columns: Log In | Sign Up
col1, col2 = st.columns(2, gap="large")

with col1:
    st.subheader("Log in")
    with st.form("login_form", clear_on_submit=False):
        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Log in")
        if submitted:
            try:
                token, uid = login(login_email.strip(), login_password)
                st.session_state["token"] = token
                st.success("Logged in")
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {e}")

with col2:
    st.subheader("Create account")
    with st.form("signup_form", clear_on_submit=False):
        su_email = st.text_input("Email", key="su_email", placeholder="you@example.com")
        su_first = st.text_input("First name", key="su_first")
        su_last = st.text_input("Last name", key="su_last")
        su_password = st.text_input("Password (minimum 8 characters)", type="password", key="su_password")

        st.caption("Set up the rest of your profile now or later:")
        pref_env = st.selectbox("Preferred environment", ["", "lake", "mountain", "beach", "city"], index=0)
        bmin = st.number_input("Budget min", min_value=0, max_value=10000, value=120, step=10)
        bmax = st.number_input("Budget max", min_value=0, max_value=10000, value=250, step=10)

        submitted = st.form_submit_button("Sign up")
        if submitted:
            try:
                if not su_email or not su_first or not su_last or not su_password:
                    raise ValueError("Email, first name, last name, and password are required.")
                if bmax and bmin and int(bmax) < int(bmin):
                    raise ValueError("Budget max must be ≥ budget min.")

                user = signup(
                    email=su_email.strip(),
                    first_name=su_first.strip(),
                    last_name=su_last.strip(),
                    password=su_password,
                    preferred_env=(pref_env or None),
                    budget_min=int(bmin),
                    budget_max=int(bmax),
                )

                token, uid = login(su_email.strip(), su_password.strip())
                st.session_state["token"] = token
                st.session_state["flash_success"] = f"Welcome, {user.first_name}! Your account has been successfully created and you are now signed in."
                st.rerun()
            except Exception as e:
                st.error(f"Sign up failed: {e}")

st.divider()
