import streamlit as st
from db.database import init_db

# Initialize the database every time the app starts
init_db()

st.switch_page("pages/register.py")