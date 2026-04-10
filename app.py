import streamlit as st
from db.database import init_db
from Patterns.session import session
from Patterns.mediator import mediator
from utils.theme import apply_theme

st.set_page_config(page_title="DriveShare", page_icon="", layout="centered")

apply_theme()
init_db()

if not session.is_logged_in():
    st.switch_page("pages/login.py")
else:
    user = session.get_user()
    mediator.navigate_after_login(user["role"])