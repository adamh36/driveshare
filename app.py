import streamlit as st
from db.database import init_db

init_db()

st.set_page_config(page_title="DriveShare", page_icon="🚗", layout="wide")

if "user" not in st.session_state:
    st.switch_page("pages/register.py")