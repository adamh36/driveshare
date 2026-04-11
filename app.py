"""
DriveShare — Main Entry Point
CIS 476 Term Project

Initializes the database and launches the Tkinter GUI.
All navigation is handled through the Mediator pattern (Patterns/ui_mediator.py).
"""

import tkinter as tk
from tkinter import ttk

from db.database import init_db
from Patterns.ui_mediator import UIComponent, DriveShareMediator
from Patterns.ui_singleton import SessionManager
from models.auth import AuthService
from theme import Colors, apply_theme


class StatusBar(UIComponent, ttk.Frame):

    def __init__(self, parent, mediator):
        ttk.Frame.__init__(self, parent, style="Status.TFrame")
        UIComponent.__init__(self, mediator)

        inner = ttk.Frame(self, style="Status.TFrame", padding=(14, 5))
        inner.pack(fill="x")

        self._left  = ttk.Label(inner, text="Not signed in", style="Status.TLabel")
        self._left.pack(side="left")

        self._right = ttk.Label(inner, text="DriveShare v1.0", style="Status.TLabel")
        self._right.pack(side="right")

    def set_user(self, user):
        self._left.config(
            text=f"  {user['username']}   |   {user['email']}   |   ${user['balance']:.2f}"
        )

    def clear_user(self):
        self._left.config(text="Not signed in")


class NavPanel(UIComponent, ttk.Frame):

    def __init__(self, parent, mediator):
        ttk.Frame.__init__(self, parent, style="Nav.TFrame")
        UIComponent.__init__(self, mediator)
        self._build()

    def _build(self):
        inner = ttk.Frame(self, style="Nav.TFrame", padding=(16, 10))
        inner.pack(fill="x")

        ttk.Label(inner, text="DriveShare", style="Nav.TLabel").pack(side="left")

        self._right = ttk.Frame(inner, style="Nav.TFrame")
        self._right.pack(side="right")

        self._notif_btn = ttk.Button(
            self._right, text="Notifications", style="Nav.TButton",
            command=lambda: self.notify("navigate", "notifications")
        )
        self._logout_btn = ttk.Button(
            self._right, text="Sign Out", style="Nav.TButton",
            command=self._logout
        )

    def show_logged_in(self):
        self._notif_btn.pack(side="left", padx=4)
        self._logout_btn.pack(side="left", padx=4)

    def show_logged_out(self):
        self._notif_btn.pack_forget()
        self._logout_btn.pack_forget()

    def _logout(self):
        AuthService.logout()
        self.notify("logout", None)


class ContentPanel(UIComponent, ttk.Frame):

    def __init__(self, parent, mediator):
        ttk.Frame.__init__(self, parent)
        UIComponent.__init__(self, mediator)
        self._frames = {}
        self._current = ""

    def register_frame(self, name, frame):
        frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._frames[name] = frame

    def show_frame(self, name):
        frame = self._frames.get(name)
        if not frame:
            return
        frame.tkraise()
        self._current = name

    def refresh_current(self):
        frame = self._frames.get(self._current)
        if frame and hasattr(frame, "refresh_current"):
            frame.refresh_current()


class DriveShareApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("DriveShare - Peer-to-Peer Car Rental")
        self.geometry("1100x720")
        self.minsize(860, 580)

        apply_theme(self)
        init_db()

        mediator = DriveShareMediator()

        nav = NavPanel(self, mediator)
        nav.pack(fill="x", side="top")

        tk.Frame(self, bg=Colors.ACCENT, height=2).pack(fill="x")

        status = StatusBar(self, mediator)
        status.pack(fill="x", side="bottom")

        tk.Frame(self, bg=Colors.BORDER, height=1).pack(fill="x", side="bottom")

        content = ContentPanel(self, mediator)
        content.pack(fill="both", expand=True)

        from gui.auth_frames      import LoginFrame, RegisterFrame, ForgotPasswordFrame
        from gui.main_frames      import (DashboardFrame, SearchFrame,
                                          ListCarFrame, MyListingsFrame, MyBookingsFrame)
        from gui.secondary_frames import MessagesFrame, NotificationsFrame, ReviewsFrame

        frames = {
            "login":           LoginFrame(content, mediator),
            "register":        RegisterFrame(content, mediator),
            "forgot_password": ForgotPasswordFrame(content, mediator),
            "dashboard":       DashboardFrame(content, mediator),
            "search":          SearchFrame(content, mediator),
            "list_car":        ListCarFrame(content, mediator),
            "my_listings":     MyListingsFrame(content, mediator),
            "my_bookings":     MyBookingsFrame(content, mediator),
            "messages":        MessagesFrame(content, mediator),
            "notifications":   NotificationsFrame(content, mediator),
            "reviews":         ReviewsFrame(content, mediator),
        }

        for name, frame in frames.items():
            content.register_frame(name, frame)

        mediator.register("nav",        nav)
        mediator.register("status_bar", status)
        mediator.register("content",    content)

        content.show_frame("login")
        nav.show_logged_out()


if __name__ == "__main__":
    app = DriveShareApp()
    app.mainloop()