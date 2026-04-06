import streamlit as st 

class SessionManager:
    # Class variable shared across every instance
    _instance = None 


    def __new__(cls):
        # Before creating a new object, check if one already exists
        if cls._instance is None: 
            cls._instance = super().__new__(cls) # If not, create it and store it in _instance
        return cls._instance #  If yes, just return the existing one
    
    def login(self, user):
        # Store the logged in user's info in streamlit's session stae
        st.session_state["user"] = user 

    def logout(self):
        # pop user from session state
        st.session_state.pop("user", None)

    def get_user(self):
        # Return the currently logged in user, or None if nobody is. 
        return st.session_state.get("user", None)    
    
    def is_logged_in(self):
        # Check if there is a user in current session 
        return "user" in st.session_state
    
session = SessionManager()