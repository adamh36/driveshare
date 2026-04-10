"""
theme.py
CIS 476 Term Project: DriveShare

Dark theme for the Tkinter UI. Defines colors, fonts, and helper
functions for building consistent UI components across all frames.
"""

import tkinter as tk
from tkinter import ttk


class Colors:
    BG_DARK  = "#0f0f0f"   # main app background
    BG_NAV   = "#141414"   # top nav bar
    BG_CARD  = "#1a1a1a"   # card / panel background
    BG_INPUT = "#222222"   # text input background
    TEXT_PRI = "#f0f0f0"   # primary text
    TEXT_MUT = "#888888"   # muted / secondary text
    ACCENT   = "#2563eb"   # blue accent for buttons and highlights
    SUCCESS  = "#16a34a"   # green for success states
    DANGER   = "#dc2626"   # red for destructive actions
    BORDER   = "#2a2a2a"   # border lines


class Fonts:
    BRAND   = ("Helvetica", 20, "bold")
    HEADING = ("Helvetica", 15, "bold")
    SUBHEAD = ("Helvetica", 12, "bold")
    BODY    = ("Helvetica", 11)
    MUTED   = ("Helvetica", 10)
    MONO    = ("Courier", 11)


def apply_theme(root):
    """
    Apply the dark theme to the entire Tkinter app.
    Call this once on the root Tk() instance before building any frames.
    """
    root.configure(bg=Colors.BG_DARK)

    style = ttk.Style(root)

    # use a base theme that we can fully override
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    # base frame and label styles
    style.configure("TFrame",        background=Colors.BG_DARK)
    style.configure("TLabel",        background=Colors.BG_DARK,   foreground=Colors.TEXT_PRI, font=Fonts.BODY)
    style.configure("Muted.TLabel",  background=Colors.BG_DARK,   foreground=Colors.TEXT_MUT, font=Fonts.MUTED)
    style.configure("Title.TLabel",  background=Colors.BG_DARK,   foreground=Colors.TEXT_PRI, font=Fonts.BRAND)
    style.configure("Heading.TLabel",background=Colors.BG_DARK,   foreground=Colors.TEXT_PRI, font=Fonts.HEADING)

    # card-specific styles
    style.configure("Card.TFrame",         background=Colors.BG_CARD)
    style.configure("Card.TLabel",         background=Colors.BG_CARD, foreground=Colors.TEXT_PRI, font=Fonts.BODY)
    style.configure("CardHeading.TLabel",  background=Colors.BG_CARD, foreground=Colors.TEXT_PRI, font=Fonts.SUBHEAD)
    style.configure("CardMuted.TLabel",    background=Colors.BG_CARD, foreground=Colors.TEXT_MUT, font=Fonts.MUTED)
    style.configure("Accent.TLabel",       background=Colors.BG_CARD, foreground=Colors.ACCENT,   font=Fonts.SUBHEAD)

    # nav bar styles
    style.configure("Nav.TFrame",  background=Colors.BG_NAV)
    style.configure("Nav.TLabel",  background=Colors.BG_NAV, foreground=Colors.TEXT_PRI, font=Fonts.SUBHEAD)

    # status bar
    style.configure("Status.TFrame", background=Colors.BG_CARD)
    style.configure("Status.TLabel", background=Colors.BG_CARD, foreground=Colors.TEXT_MUT, font=Fonts.MUTED)

    # buttons
    style.configure("TButton",
        background=Colors.BG_CARD,
        foreground=Colors.TEXT_PRI,
        font=Fonts.BODY,
        borderwidth=1,
        relief="flat",
        padding=(10, 5)
    )
    style.map("TButton",
        background=[("active", "#2a2a2a"), ("pressed", "#333333")],
        relief=[("pressed", "flat")]
    )

    style.configure("Accent.TButton",
        background=Colors.ACCENT,
        foreground="#ffffff",
        font=Fonts.BODY,
        padding=(12, 6)
    )
    style.map("Accent.TButton",
        background=[("active", "#1d4ed8"), ("pressed", "#1e40af")]
    )

    style.configure("Ghost.TButton",
        background=Colors.BG_DARK,
        foreground=Colors.TEXT_MUT,
        font=Fonts.MUTED,
        padding=(8, 4)
    )
    style.map("Ghost.TButton",
        background=[("active", Colors.BG_CARD)],
        foreground=[("active", Colors.TEXT_PRI)]
    )

    style.configure("Nav.TButton",
        background=Colors.BG_NAV,
        foreground=Colors.TEXT_MUT,
        font=Fonts.MUTED,
        padding=(8, 4)
    )
    style.map("Nav.TButton",
        background=[("active", Colors.BG_CARD)],
        foreground=[("active", Colors.TEXT_PRI)]
    )

    style.configure("Success.TButton",
        background=Colors.SUCCESS,
        foreground="#ffffff",
        font=Fonts.BODY,
        padding=(10, 5)
    )
    style.map("Success.TButton",
        background=[("active", "#15803d")]
    )

    style.configure("Danger.TButton",
        background=Colors.DANGER,
        foreground="#ffffff",
        font=Fonts.BODY,
        padding=(10, 5)
    )
    style.map("Danger.TButton",
        background=[("active", "#b91c1c")]
    )

    # entries
    style.configure("TEntry",
        fieldbackground=Colors.BG_INPUT,
        foreground=Colors.TEXT_PRI,
        insertcolor=Colors.TEXT_PRI,
        borderwidth=1,
        relief="flat"
    )

    # treeview
    style.configure("Treeview",
        background=Colors.BG_CARD,
        foreground=Colors.TEXT_PRI,
        fieldbackground=Colors.BG_CARD,
        rowheight=28,
        font=Fonts.BODY
    )
    style.configure("Treeview.Heading",
        background=Colors.BG_DARK,
        foreground=Colors.TEXT_MUT,
        font=Fonts.MUTED,
        relief="flat"
    )
    style.map("Treeview",
        background=[("selected", Colors.ACCENT)],
        foreground=[("selected", "#ffffff")]
    )

    # combobox and spinbox
    style.configure("TCombobox",
        fieldbackground=Colors.BG_INPUT,
        background=Colors.BG_INPUT,
        foreground=Colors.TEXT_PRI,
        selectbackground=Colors.ACCENT
    )
    style.configure("TSpinbox",
        fieldbackground=Colors.BG_INPUT,
        foreground=Colors.TEXT_PRI
    )

    # checkbutton
    style.configure("TCheckbutton",
        background=Colors.BG_CARD,
        foreground=Colors.TEXT_PRI,
        font=Fonts.BODY
    )

    # scrollbar
    style.configure("TScrollbar",
        background=Colors.BG_CARD,
        troughcolor=Colors.BG_DARK,
        borderwidth=0,
        arrowsize=12
    )

    # separator
    style.configure("TSeparator", background=Colors.BORDER)


def make_card(parent, padding=16):
    """
    Returns a styled card frame with a subtle background.
    Use this for any panel that should visually stand out from the page.
    """
    frame = ttk.Frame(parent, style="Card.TFrame", padding=padding)
    return frame


def make_scrolled_treeview(parent, columns, heights=10, col_widths=None):
    """
    Returns a Treeview with a vertical scrollbar attached.
    Packs itself into parent automatically.
    """
    wrapper = ttk.Frame(parent)
    wrapper.pack(fill="both", expand=True, padx=16, pady=8)

    sb = ttk.Scrollbar(wrapper, orient="vertical")
    sb.pack(side="right", fill="y")

    tree = ttk.Treeview(
        wrapper,
        columns=columns,
        show="headings",
        height=heights,
        yscrollcommand=sb.set
    )
    sb.config(command=tree.yview)

    for col in columns:
        width = (col_widths or {}).get(col, 100)
        tree.heading(col, text=col)
        tree.column(col, width=width, anchor="w")

    tree.pack(fill="both", expand=True)
    return tree


def make_action_bar(parent, buttons):
    """
    Creates a bottom bar with a list of buttons.
    buttons = list of (label, style, command) tuples.
    """
    bar = ttk.Frame(parent, style="TFrame", padding=(16, 8))
    bar.pack(fill="x", side="bottom")
    for label, style, cmd in buttons:
        ttk.Button(bar, text=label, style=style, command=cmd).pack(side="left", padx=4)


def styled_text(parent, height=6, width=40):
    """
    Returns a tk.Text widget styled to match the dark theme.
    """
    widget = tk.Text(
        parent,
        height=height,
        width=width,
        bg=Colors.BG_INPUT,
        fg=Colors.TEXT_PRI,
        insertbackground=Colors.TEXT_PRI,
        relief="flat",
        font=Fonts.BODY,
        padx=8,
        pady=6,
        wrap="word"
    )
    return widget