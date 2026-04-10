"""
MEDIATOR PATTERN: UI Navigation Coordinator
CIS 476 Term Project: DriveShare

The UIMediator acts as the central coordinator between all pages.
Instead of pages switching to each other directly, they go through
the mediator — so no page needs to know about any other page.

Pattern roles:
  Mediator     → UIMediator
  Colleagues   → login.py, register.py, owner_dashboard.py,
                 renter_dashboard.py, search.py, messages.py, history.py
"""

import streamlit as st
from Patterns.session import session


class UIMediator:

    def __init__(self):
        # the mediator talks to the session to know who is logged in
        self.session = session

    def navigate_after_login(self, role):
        # after login, send the user to the right dashboard based on their role
        if role in ("owner", "both"):
            st.switch_page("pages/owner_dashboard.py")
        else:
            st.switch_page("pages/renter_dashboard.py")

    def handle_logout(self):
        # clear the session and send the user back to login
        self.session.logout()
        st.switch_page("pages/login.py")

    def go_to_login(self):
        st.switch_page("pages/login.py")

    def go_to_register(self):
        st.switch_page("pages/register.py")

    def go_to_search(self):
        st.switch_page("pages/search.py")

    def go_to_messages(self):
        st.switch_page("pages/messages.py")

    def go_to_history(self):
        st.switch_page("pages/history.py")

    def go_to_owner_dashboard(self):
        st.switch_page("pages/owner_dashboard.py")

    def go_to_renter_dashboard(self):
        st.switch_page("pages/renter_dashboard.py")


# single shared instance — import this everywhere instead of creating new ones
mediator = UIMediator()