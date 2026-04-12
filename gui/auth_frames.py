"""
DriveShare GUI - Login, Register, Forgot Password frames.
CIS 476 Term Project: DriveShare
"""

import tkinter as tk
from tkinter import ttk, messagebox
from Patterns.ui_mediator import UIComponent, DriveShareMediator
from models.auth import AuthService
from Patterns.ui_chain import PasswordRecoveryService
from theme import Colors, Fonts, make_card


SECURITY_QUESTIONS = [
    "What was the name of your first pet?",
    "What city were you born in?",
    "What is your mother's maiden name?",
    "What was the name of your elementary school?",
    "What was the make of your first car?",
    "What is your oldest sibling's middle name?",
]


def _card_entry(parent, label, row, show=None, width=30):
    ttk.Label(parent, text=label, style="CardMuted.TLabel").grid(
        row=row, column=0, sticky="w", padx=(0, 14), pady=6
    )
    var = tk.StringVar()
    ttk.Entry(parent, textvariable=var, show=show, width=width).grid(
        row=row, column=1, sticky="ew", pady=6
    )
    return var


class LoginFrame(UIComponent, ttk.Frame):

    def __init__(self, parent, mediator):
        ttk.Frame.__init__(self, parent)
        UIComponent.__init__(self, mediator)
        self._build()

    def _build(self):
        self.rowconfigure(0, weight=1)
        self.rowconfigure(10, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(2, weight=1)

        hero = ttk.Frame(self, style="TFrame")
        hero.grid(row=1, column=1, pady=(0, 8))
        ttk.Label(hero, text="DriveShare", style="Title.TLabel").pack()
        ttk.Label(hero, text="Peer-to-Peer Car Rental", style="Muted.TLabel").pack(pady=(2, 24))

        card = make_card(self, padding=32)
        card.grid(row=2, column=1, sticky="ew", padx=80)
        card.columnconfigure(1, weight=1)

        ttk.Label(card, text="Sign In", style="CardHeading.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 14)
        )
        self._email    = _card_entry(card, "Email",    1)
        self._password = _card_entry(card, "Password", 2, show="*")

        ttk.Button(card, text="Sign In", style="Accent.TButton",
                   command=self._login).grid(row=3, column=0, columnspan=2,
                                             sticky="ew", pady=(20, 6))

        links = ttk.Frame(card, style="Card.TFrame")
        links.grid(row=4, column=0, columnspan=2)
        ttk.Button(links, text="Create Account", style="Ghost.TButton",
                   command=lambda: self.notify("navigate", "register")).pack(side="left", padx=3)
        ttk.Button(links, text="Forgot Password", style="Ghost.TButton",
                   command=lambda: self.notify("navigate", "forgot_password")).pack(side="left", padx=3)

        self.bind_all("<Return>", lambda _: self._login())

    def _login(self):
        ok, msg = AuthService.login(self._email.get(), self._password.get())
        if ok:
            from Patterns.ui_singleton import SessionManager
            self.notify("login_success", SessionManager().current_user)
        else:
            messagebox.showerror("Login Failed", msg)


class RegisterFrame(UIComponent, ttk.Frame):

    def __init__(self, parent, mediator):
        ttk.Frame.__init__(self, parent)
        UIComponent.__init__(self, mediator)
        self._build()

    def _build(self):
        ttk.Label(self, text="Create Account", style="Heading.TLabel").pack(pady=(22, 2))
        ttk.Label(self, text="Join DriveShare today", style="Muted.TLabel").pack(pady=(0, 14))

        outer = ttk.Frame(self)
        outer.pack(fill="both", expand=True, padx=60)

        canvas = tk.Canvas(outer, bg=Colors.BG_DARK, highlightthickness=0, bd=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = ttk.Frame(canvas)
        cwin  = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_inner_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_canvas_configure(e):
            canvas.itemconfigure(cwin, width=e.width)

        inner.bind("<Configure>", _on_inner_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        # account details card
        acct = make_card(inner, padding=22)
        acct.pack(fill="x", pady=6)
        acct.columnconfigure(1, weight=1)
        ttk.Label(acct, text="Account Details", style="CardHeading.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 10)
        )
        self._username = _card_entry(acct, "Username", 1)
        self._email    = _card_entry(acct, "Email",    2)
        self._password = _card_entry(acct, "Password", 3, show="*")
        self._confirm  = _card_entry(acct, "Confirm Password", 4, show="*")

        # role selector — owner lists cars, renter books cars, both can do everything
        ttk.Label(acct, text="I want to", style="CardMuted.TLabel").grid(
            row=5, column=0, sticky="w", padx=(0, 14), pady=6
        )
        self._role = tk.StringVar(value="renter")
        role_cb = ttk.Combobox(
            acct,
            textvariable=self._role,
            values=["renter", "owner", "both"],
            state="readonly",
            width=28
        )
        role_cb.grid(row=5, column=1, sticky="ew", pady=6)

        # security questions card
        sq = make_card(inner, padding=22)
        sq.pack(fill="x", pady=6)
        sq.columnconfigure(1, weight=1)
        ttk.Label(sq, text="Security Questions", style="CardHeading.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 2)
        )
        ttk.Label(sq, text="Required for password recovery",
                  style="CardMuted.TLabel").grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self._sq, self._sa = [], []
        for i in range(3):
            base = 2 + i * 2
            ttk.Label(sq, text=f"Question {i+1}", style="CardMuted.TLabel").grid(
                row=base, column=0, sticky="w", padx=(0, 14), pady=(6, 0)
            )
            q_var = tk.StringVar(value=SECURITY_QUESTIONS[i])
            ttk.Combobox(sq, textvariable=q_var, values=SECURITY_QUESTIONS,
                         state="readonly").grid(row=base, column=1, sticky="ew", pady=(6, 0))
            self._sq.append(q_var)
            self._sa.append(_card_entry(sq, f"Answer {i+1}", base + 1))

        bar = ttk.Frame(inner)
        bar.pack(fill="x", pady=14)
        ttk.Button(bar, text="Create Account", style="Accent.TButton",
                   command=self._register).pack(side="left", padx=4)
        ttk.Button(bar, text="Back to Login", style="Ghost.TButton",
                   command=lambda: self.notify("navigate", "login")).pack(side="left", padx=4)

    def _register(self):
        if self._password.get() != self._confirm.get():
            messagebox.showerror("Error", "Passwords do not match.")
            return
        # role is now passed through to AuthService
        ok, msg = AuthService.register(
            self._username.get(), self._email.get(), self._password.get(),
            self._role.get(),
            self._sq[0].get(), self._sa[0].get(),
            self._sq[1].get(), self._sa[1].get(),
            self._sq[2].get(), self._sa[2].get(),
        )
        if ok:
            messagebox.showinfo("Success", msg)
            self.notify("navigate", "login")
        else:
            messagebox.showerror("Registration Failed", msg)


class ForgotPasswordFrame(UIComponent, ttk.Frame):

    def __init__(self, parent, mediator):
        ttk.Frame.__init__(self, parent)
        UIComponent.__init__(self, mediator)
        self._recovery         = PasswordRecoveryService()
        self._answer_vars      = []
        self._questions_loaded = False
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(9, weight=1)

        ttk.Label(self, text="Reset Password", style="Heading.TLabel").grid(row=1, column=1, pady=(28, 2))
        ttk.Label(self, text="Answer your security questions",
                  style="Muted.TLabel").grid(row=2, column=1, pady=(0, 18))

        card = make_card(self, padding=28)
        card.grid(row=3, column=1, sticky="ew", padx=80)
        card.columnconfigure(1, weight=1)

        self._email = _card_entry(card, "Email Address", 0)

        ttk.Button(card, text="Load Security Questions", style="Ghost.TButton",
                   command=self._load).grid(row=1, column=0, columnspan=2, pady=10, sticky="w")

        self._q_frame = ttk.Frame(card, style="Card.TFrame")
        self._q_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
        self._q_frame.columnconfigure(1, weight=1)

        ttk.Separator(card).grid(row=3, column=0, columnspan=2, sticky="ew", pady=12)
        self._new_pw     = _card_entry(card, "New Password", 4, show="*")
        self._confirm_pw = _card_entry(card, "Confirm",      5, show="*")

        bar = ttk.Frame(card, style="Card.TFrame")
        bar.grid(row=6, column=0, columnspan=2, pady=(16, 0))
        ttk.Button(bar, text="Reset Password", style="Accent.TButton",
                   command=self._reset).pack(side="left", padx=4)
        ttk.Button(bar, text="Back", style="Ghost.TButton",
                   command=lambda: self.notify("navigate", "login")).pack(side="left", padx=4)

    def _load(self):
        questions = self._recovery.get_security_questions(self._email.get())
        if not questions:
            messagebox.showerror("Error", "Email not found.")
            return
        for w in self._q_frame.winfo_children():
            w.destroy()
        self._answer_vars.clear()
        for i, key in enumerate(["question1", "question2", "question3"]):
            ttk.Label(self._q_frame, text=questions[key],
                      style="CardMuted.TLabel", wraplength=380).grid(
                row=i*2, column=0, columnspan=2, sticky="w", pady=(8, 0)
            )
            self._answer_vars.append(_card_entry(self._q_frame, f"Answer {i+1}", i*2+1))
        self._questions_loaded = True

    def _reset(self):
        if not self._questions_loaded or len(self._answer_vars) < 3:
            messagebox.showerror("Error", "Please load security questions first.")
            return
        if self._new_pw.get() != self._confirm_pw.get():
            messagebox.showerror("Error", "Passwords do not match.")
            return
        ok, msg = self._recovery.verify_and_reset(
            self._email.get(),
            self._answer_vars[0].get(), self._answer_vars[1].get(),
            self._answer_vars[2].get(), self._new_pw.get(),
        )
        if ok:
            messagebox.showinfo("Success", msg)
            self.notify("navigate", "login")
        else:
            messagebox.showerror("Failed", msg)