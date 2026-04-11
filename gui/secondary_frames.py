"""
DriveShare GUI - Messages, Notifications, Reviews frames.
CIS 476 Term Project: DriveShare
"""

import tkinter as tk
from tkinter import ttk, messagebox
from Patterns.ui_mediator import UIComponent, DriveShareMediator
from Patterns.ui_singleton import SessionManager
from models.messaging import MessageService, NotificationService, ReviewService
from theme import Colors, Fonts, make_card, make_scrolled_treeview, make_action_bar, styled_text


class MessagesFrame(UIComponent, ttk.Frame):

    def __init__(self, parent, mediator):
        ttk.Frame.__init__(self, parent)
        UIComponent.__init__(self, mediator)
        self._messages = []
        self._build()

    def _build(self):
        hdr = make_card(self, padding=(20, 14))
        hdr.pack(fill="x")
        ttk.Label(hdr, text="Messages", style="CardHeading.TLabel").pack(side="left")
        ttk.Button(hdr, text="Back", style="Ghost.TButton",
                   command=lambda: self.notify("navigate", "dashboard")).pack(side="right")

        pane = ttk.PanedWindow(self, orient="horizontal")
        pane.pack(fill="both", expand=True, padx=16, pady=12)

        left = ttk.Frame(pane)
        pane.add(left, weight=1)

        ttk.Label(left, text="Inbox", style="Heading.TLabel").pack(anchor="w", pady=(0, 6))
        cols = ("From", "Preview", "Time", "")
        widths = {"From": 90, "Preview": 140, "Time": 100, "": 24}

        sb = ttk.Scrollbar(left, orient="vertical")
        sb.pack(side="right", fill="y")
        self._inbox_tree = ttk.Treeview(left, columns=cols, show="headings",
                                         height=16, yscrollcommand=sb.set)
        sb.config(command=self._inbox_tree.yview)
        for c in cols:
            self._inbox_tree.heading(c, text=c)
            self._inbox_tree.column(c, width=widths.get(c, 100))
        self._inbox_tree.pack(fill="both", expand=True)
        self._inbox_tree.bind("<<TreeviewSelect>>", self._on_select)

        ttk.Button(left, text="Refresh", style="Ghost.TButton",
                   command=self._refresh_inbox).pack(anchor="w", pady=6)

        right = ttk.Frame(pane)
        pane.add(right, weight=2)

        compose = make_card(right, padding=16)
        compose.pack(fill="x", pady=(0, 10))
        compose.columnconfigure(1, weight=1)

        ttk.Label(compose, text="New Message", style="CardHeading.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 10)
        )
        ttk.Label(compose, text="To (User ID):", style="CardMuted.TLabel").grid(
            row=1, column=0, sticky="w", padx=(0, 12), pady=5
        )
        self._to_id = tk.StringVar()
        ttk.Entry(compose, textvariable=self._to_id, width=10).grid(row=1, column=1, sticky="w", pady=5)

        ttk.Label(compose, text="Message:", style="CardMuted.TLabel").grid(
            row=2, column=0, sticky="nw", padx=(0, 12), pady=5
        )
        self._msg_text = styled_text(compose, height=4, width=36)
        self._msg_text.grid(row=2, column=1, sticky="ew", pady=5)

        ttk.Button(compose, text="Send", style="Accent.TButton",
                   command=self._send).grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 0))

        ttk.Label(right, text="Selected Message", style="Muted.TLabel").pack(anchor="w", pady=(6, 2))
        self._detail = styled_text(right, height=8, width=40)
        self._detail.config(state="disabled")
        self._detail.pack(fill="both", expand=True)

        self._refresh_inbox()

    def _refresh_inbox(self):
        uid = SessionManager().user_id
        self._messages = MessageService.get_inbox(uid) if uid else []
        for r in self._inbox_tree.get_children():
            self._inbox_tree.delete(r)
        for m in self._messages:
            preview = m["content"][:35] + "..." if len(m["content"]) > 35 else m["content"]
            badge   = "NEW" if not m["is_read"] else ""
            self._inbox_tree.insert("", "end", values=(
                m["sender_name"], preview, m["sent_at"][:16], badge
            ))

    def _on_select(self, _=None):
        sel = self._inbox_tree.selection()
        if not sel:
            return
        msg = self._messages[self._inbox_tree.index(sel[0])]
        MessageService.mark_read(msg["id"])
        self._detail.config(state="normal")
        self._detail.delete("1.0", "end")
        self._detail.insert("1.0",
            f"From:  {msg['sender_name']}\nTime:  {msg['sent_at']}\n"
            f"{'─'*40}\n\n{msg['content']}"
        )
        self._detail.config(state="disabled")
        self._refresh_inbox()

    def _send(self):
        try:
            to_id = int(self._to_id.get())
        except ValueError:
            messagebox.showerror("Error", "Enter a valid User ID.")
            return
        content = self._msg_text.get("1.0", "end").strip()
        ok, msg = MessageService.send_message(to_id, content)
        if ok:
            self._msg_text.delete("1.0", "end")
            messagebox.showinfo("Sent", "Message delivered!")
        else:
            messagebox.showerror("Error", msg)

    def refresh_current(self):
        self._refresh_inbox()


class NotificationsFrame(UIComponent, ttk.Frame):

    def __init__(self, parent, mediator):
        ttk.Frame.__init__(self, parent)
        UIComponent.__init__(self, mediator)
        self._build()

    def _build(self):
        hdr = make_card(self, padding=(20, 14))
        hdr.pack(fill="x")
        ttk.Label(hdr, text="Notifications", style="CardHeading.TLabel").pack(side="left")
        ttk.Button(hdr, text="Back", style="Ghost.TButton",
                   command=lambda: self.notify("navigate", "dashboard")).pack(side="right")

        cols = ("Time", "Message", "Read")
        widths = {"Time": 140, "Message": 520, "Read": 50}
        self._tree = make_scrolled_treeview(self, cols, heights=16, col_widths=widths)

        make_action_bar(self, [
            ("Refresh",       "Ghost.TButton",  self._refresh),
            ("Mark All Read", "Accent.TButton", self._mark_all),
        ])

        self._refresh()

    def _refresh(self):
        uid   = SessionManager().user_id
        notifs = NotificationService.get_notifications(uid) if uid else []
        for r in self._tree.get_children():
            self._tree.delete(r)
        for n in notifs:
            read = "Yes" if n["is_read"] else "No"
            self._tree.insert("", "end", values=(n["created_at"][:16], n["message"], read))

    def _mark_all(self):
        uid = SessionManager().user_id
        if uid:
            NotificationService.mark_all_read(uid)
            self._refresh()
            self.notify("notification_update", 0)

    def refresh_current(self):
        self._refresh()


class ReviewsFrame(UIComponent, ttk.Frame):

    def __init__(self, parent, mediator):
        ttk.Frame.__init__(self, parent)
        UIComponent.__init__(self, mediator)
        self._build()

    def _build(self):
        hdr = make_card(self, padding=(20, 14))
        hdr.pack(fill="x")
        ttk.Label(hdr, text="Reviews", style="CardHeading.TLabel").pack(side="left")
        ttk.Button(hdr, text="Back", style="Ghost.TButton",
                   command=lambda: self.notify("navigate", "dashboard")).pack(side="right")

        leave = make_card(self, padding=20)
        leave.pack(fill="x", padx=16, pady=12)
        leave.columnconfigure(1, weight=1)
        leave.columnconfigure(3, weight=1)

        ttk.Label(leave, text="Leave a Review", style="CardHeading.TLabel").grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 12)
        )

        ttk.Label(leave, text="Booking ID:", style="CardMuted.TLabel").grid(row=1, column=0, sticky="w", padx=(0,8))
        self._booking_id = tk.StringVar()
        ttk.Entry(leave, textvariable=self._booking_id, width=10).grid(row=1, column=1, sticky="w", padx=(0,20))

        ttk.Label(leave, text="Reviewee User ID:", style="CardMuted.TLabel").grid(row=1, column=2, sticky="w", padx=(0,8))
        self._reviewee_id = tk.StringVar()
        ttk.Entry(leave, textvariable=self._reviewee_id, width=10).grid(row=1, column=3, sticky="w")

        ttk.Label(leave, text="Rating (1-5):", style="CardMuted.TLabel").grid(row=2, column=0, sticky="w", padx=(0,8), pady=8)
        self._rating = tk.StringVar(value="5")
        ttk.Spinbox(leave, from_=1, to=5, textvariable=self._rating, width=6).grid(row=2, column=1, sticky="w")

        ttk.Label(leave, text="Comment:", style="CardMuted.TLabel").grid(row=3, column=0, sticky="nw", padx=(0,8), pady=6)
        self._comment = styled_text(leave, height=3, width=50)
        self._comment.grid(row=3, column=1, columnspan=3, sticky="ew", pady=6)

        ttk.Button(leave, text="Submit Review", style="Accent.TButton",
                   command=self._submit).grid(row=4, column=0, columnspan=4, sticky="w", pady=(10, 0))

        ttk.Label(self, text="Reviews Received", style="Heading.TLabel").pack(
            anchor="w", padx=20, pady=(8, 4)
        )

        cols = ("Reviewer", "Rating", "Comment", "Date")
        widths = {"Reviewer": 120, "Rating": 80, "Comment": 340, "Date": 90}
        self._tree = make_scrolled_treeview(self, cols, heights=8, col_widths=widths)

        make_action_bar(self, [("Refresh", "Ghost.TButton", self._refresh_reviews)])
        self._refresh_reviews()

    def _submit(self):
        try:
            bid = int(self._booking_id.get())
            rid = int(self._reviewee_id.get())
            rat = int(self._rating.get())
        except ValueError:
            messagebox.showerror("Error", "Booking ID, Reviewee ID and Rating must be integers.")
            return
        ok, msg = ReviewService.leave_review(bid, rid, rat, self._comment.get("1.0","end").strip())
        messagebox.showinfo("Review", msg)
        if ok:
            self._comment.delete("1.0", "end")
            self._refresh_reviews()

    def _refresh_reviews(self):
        uid = SessionManager().user_id
        reviews = ReviewService.get_reviews_for_user(uid) if uid else []
        for r in self._tree.get_children():
            self._tree.delete(r)
        for r in reviews:
            stars = "*" * r["rating"]
            self._tree.insert("", "end", values=(
                r["reviewer_name"], stars,
                r.get("comment", ""), r["created_at"][:10]
            ))

    def refresh_current(self):
        self._refresh_reviews()