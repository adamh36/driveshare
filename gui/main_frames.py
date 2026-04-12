"""
DriveShare GUI - Dashboard, Search, List Car, My Listings, My Bookings frames.
CIS 476 Term Project: DriveShare
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date, timedelta
from Patterns.ui_mediator import UIComponent, DriveShareMediator
from Patterns.ui_singleton import SessionManager
from models.car import CarService, BookingService
from models.messaging import NotificationService
from theme import Colors, Fonts, make_card, make_scrolled_treeview, make_action_bar, styled_text


def _card_entry(parent, label, row, show=None, width=22):
    ttk.Label(parent, text=label, style="CardMuted.TLabel").grid(
        row=row, column=0, sticky="w", padx=(0, 12), pady=5
    )
    var = tk.StringVar()
    ttk.Entry(parent, textvariable=var, show=show, width=width).grid(
        row=row, column=1, sticky="ew", pady=5
    )
    return var


class DashboardFrame(UIComponent, ttk.Frame):

    def __init__(self, parent, mediator):
        ttk.Frame.__init__(self, parent)
        UIComponent.__init__(self, mediator)
        self._build()

    def _build(self):
        header = ttk.Frame(self, style="Card.TFrame")
        header.pack(fill="x")
        inner = ttk.Frame(header, style="Card.TFrame", padding=(24, 16))
        inner.pack(fill="x")

        self._welcome_lbl = ttk.Label(inner, text="Welcome back!", style="CardHeading.TLabel")
        self._welcome_lbl.pack(side="left")
        self._balance_lbl = ttk.Label(inner, text="", style="Accent.TLabel")
        self._balance_lbl.pack(side="right")

        ttk.Label(self, text="Quick Actions", style="Heading.TLabel").pack(
            anchor="w", padx=24, pady=(16, 10)
        )

        # actions are filtered based on the user's role
        self._grid_frame = ttk.Frame(self)
        self._grid_frame.pack(fill="x", padx=20)

        self._refresh_header()

    def _refresh_header(self):
        user = SessionManager().current_user
        if not user:
            return

        self._welcome_lbl.config(text=f"Welcome back, {user['username']}!")
        self._balance_lbl.config(text=f"Balance: ${user['balance']:.2f}")

        # clear old action cards before rebuilding
        for widget in self._grid_frame.winfo_children():
            widget.destroy()

        role = user["role"]

        # build action list based on role
        all_actions = [
            ("Search Cars",   "search",       "Find and book available cars near you",  ["renter", "both"]),
            ("List a Car",    "list_car",     "Earn money by renting out your vehicle", ["owner", "both"]),
            ("My Listings",   "my_listings",  "Manage your car listings",              ["owner", "both"]),
            ("My Bookings",   "my_bookings",  "View and pay for your bookings",        ["renter", "both"]),
            ("Messages",      "messages",     "Chat with owners and renters",           ["owner", "renter", "both"]),
            ("Notifications", "notifications","View alerts and updates",                ["owner", "renter", "both"]),
            ("Reviews",       "reviews",      "Leave and view rental reviews",          ["owner", "renter", "both"]),
        ]

        # only show actions relevant to this user's role
        visible = [(t, f, d) for t, f, d, roles in all_actions if role in roles]

        for i, (title, frame_name, desc) in enumerate(visible):
            row, col = divmod(i, 3)
            card = make_card(self._grid_frame, padding=18)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            self._grid_frame.columnconfigure(col, weight=1)

            ttk.Label(card, text=title, style="CardHeading.TLabel").pack(anchor="w", pady=(4, 2))
            ttk.Label(card, text=desc, style="CardMuted.TLabel",
                      wraplength=180).pack(anchor="w", pady=(0, 10))
            ttk.Button(card, text="Open", style="Ghost.TButton",
                       command=lambda f=frame_name: self.notify("navigate", f)).pack(anchor="w")

    def refresh_current(self):
        # clear old cards and rebuild based on current user's role
        for widget in self._grid_frame.winfo_children():
            widget.destroy()
        self._refresh_header()


class SearchFrame(UIComponent, ttk.Frame):

    def __init__(self, parent, mediator):
        ttk.Frame.__init__(self, parent)
        UIComponent.__init__(self, mediator)
        self._cars = []
        self._build()

    def _build(self):
        hdr = make_card(self, padding=(20, 14))
        hdr.pack(fill="x")
        ttk.Label(hdr, text="Search Cars", style="CardHeading.TLabel").pack(side="left")
        ttk.Button(hdr, text="Back", style="Ghost.TButton",
                   command=lambda: self.notify("navigate", "dashboard")).pack(side="right")

        fcard = make_card(self, padding=18)
        fcard.pack(fill="x", padx=16, pady=10)

        row1 = ttk.Frame(fcard, style="Card.TFrame")
        row1.pack(fill="x", pady=(0, 6))

        def lbl_entry(parent, text, default="", width=16):
            ttk.Label(parent, text=text, style="CardMuted.TLabel").pack(side="left", padx=(0, 4))
            var = tk.StringVar(value=default)
            ttk.Entry(parent, textvariable=var, width=width).pack(side="left", padx=(0, 16))
            return var

        self._location   = lbl_entry(row1, "Location", width=18)
        self._start_date = lbl_entry(row1, "From (YYYY-MM-DD)", str(date.today() + timedelta(days=1)), 12)
        self._end_date   = lbl_entry(row1, "To (YYYY-MM-DD)",   str(date.today() + timedelta(days=4)), 12)
        self._max_price  = lbl_entry(row1, "Max/Day ($)", width=8)

        ttk.Button(row1, text="Search", style="Accent.TButton",
                   command=self._search).pack(side="left", padx=4)

        cols = ("ID", "Year", "Make", "Model", "Location", "$/Day", "Mileage", "Owner")
        widths = {"ID": 50, "Year": 60, "Make": 90, "Model": 100,
                  "Location": 130, "$/Day": 70, "Mileage": 80, "Owner": 110}
        self._tree = make_scrolled_treeview(self, cols, heights=13, col_widths=widths)
        self._tree.bind("<Double-1>", self._show_detail)

        make_action_bar(self, [
            ("Book Selected", "Accent.TButton", self._book),
            ("Watch Car",     "Ghost.TButton",  self._watch),
        ])

    def _search(self):
        try:
            max_p = float(self._max_price.get()) if self._max_price.get().strip() else 0.0
        except ValueError:
            max_p = 0.0

        uid = SessionManager().user_id
        self._cars = [
            c for c in CarService.search_cars(
                self._location.get(), self._start_date.get(),
                self._end_date.get(), max_p
            ) if c["owner_id"] != uid
        ]

        for r in self._tree.get_children():
            self._tree.delete(r)
        for c in self._cars:
            self._tree.insert("", "end", values=(
                c["id"], c["year"], c["make"], c["model"],
                c["location"], f"${c['price_per_day']:.2f}",
                f"{c['mileage']:,}", c.get("owner_name", "")
            ))

    def _selected_car(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a car first.")
            return None
        return self._cars[self._tree.index(sel[0])]

    def _show_detail(self, _=None):
        car = self._selected_car()
        if car:
            messagebox.showinfo(
                f"{car['year']} {car['make']} {car['model']}",
                f"Location: {car['location']}\n"
                f"Price: ${car['price_per_day']:.2f}/day\n"
                f"Mileage: {car['mileage']:,} mi\n"
                f"Owner: {car.get('owner_name','')}\n\n"
                f"{car.get('description','No description provided.')}"
            )

    def _book(self):
        car = self._selected_car()
        if not car:
            return
        ok, msg, bid = BookingService.create_booking(
            car["id"], self._start_date.get(), self._end_date.get()
        )
        if ok:
            if messagebox.askyesno("Booking Created", f"{msg}\n\nWould you like to pay now?"):
                ok2, msg2 = BookingService.pay_booking(bid)
                messagebox.showinfo("Payment", msg2)
                self.notify("booking_created", bid)
        else:
            messagebox.showerror("Booking Failed", msg)

    def _watch(self):
        car = self._selected_car()
        if not car:
            return
        max_p_str = simpledialog.askstring(
            "Watch Car", "Max price/day to notify you (leave blank for any):",
            parent=self
        )
        try:
            max_p = float(max_p_str) if max_p_str and max_p_str.strip() else 0.0
        except ValueError:
            max_p = 0.0
        ok, msg = CarService.watch_car(car["id"], max_p)
        messagebox.showinfo("Watch Car", msg)


class ListCarFrame(UIComponent, ttk.Frame):

    def __init__(self, parent, mediator):
        ttk.Frame.__init__(self, parent)
        UIComponent.__init__(self, mediator)
        self._build()

    def _build(self):
        hdr = make_card(self, padding=(20, 14))
        hdr.pack(fill="x")
        ttk.Label(hdr, text="List Your Car", style="CardHeading.TLabel").pack(side="left")
        ttk.Button(hdr, text="Back", style="Ghost.TButton",
                   command=lambda: self.notify("navigate", "dashboard")).pack(side="right")

        card = make_card(self, padding=28)
        card.pack(padx=60, pady=20, fill="x")
        card.columnconfigure(1, weight=1)

        ttk.Label(card, text="Vehicle Details", style="CardHeading.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 14)
        )

        fields = [
            ("Make",           "make"),
            ("Model",          "model"),
            ("Year",           "year"),
            ("Mileage (mi)",   "mileage"),
            ("Pickup Location","location"),
            ("Price / Day ($)","price"),
        ]
        self._vars = {}
        for i, (label, key) in enumerate(fields, 1):
            ttk.Label(card, text=label, style="CardMuted.TLabel").grid(
                row=i, column=0, sticky="w", padx=(0, 14), pady=6
            )
            var = tk.StringVar()
            ttk.Entry(card, textvariable=var, width=32).grid(row=i, column=1, sticky="ew", pady=6)
            self._vars[key] = var

        ttk.Label(card, text="Description", style="CardMuted.TLabel").grid(
            row=len(fields)+1, column=0, sticky="nw", padx=(0, 14), pady=6
        )
        self._desc = styled_text(card, height=4, width=36)
        self._desc.grid(row=len(fields)+1, column=1, sticky="ew", pady=6)

        btn_bar = ttk.Frame(card, style="Card.TFrame")
        btn_bar.grid(row=len(fields)+2, column=0, columnspan=2, pady=(16, 0))
        ttk.Button(btn_bar, text="List Car", style="Accent.TButton",
                   command=self._submit).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="Clear", style="Ghost.TButton",
                   command=self._clear).pack(side="left", padx=4)

    def _submit(self):
        v = self._vars
        try:
            ok, msg = CarService.create_listing(
                make=v["make"].get(), model=v["model"].get(),
                year=int(v["year"].get()), mileage=int(v["mileage"].get()),
                location=v["location"].get(), price_per_day=float(v["price"].get()),
                description=self._desc.get("1.0", "end").strip(),
            )
        except ValueError:
            messagebox.showerror("Error", "Year, mileage, and price must be valid numbers.")
            return

        if ok:
            messagebox.showinfo("Success", msg)
            self._clear()
            self.notify("car_listed", None)
        else:
            messagebox.showerror("Error", msg)

    def _clear(self):
        for var in self._vars.values():
            var.set("")
        self._desc.delete("1.0", "end")


class MyListingsFrame(UIComponent, ttk.Frame):

    def __init__(self, parent, mediator):
        ttk.Frame.__init__(self, parent)
        UIComponent.__init__(self, mediator)
        self._cars = []
        self._build()

    def _build(self):
        hdr = make_card(self, padding=(20, 14))
        hdr.pack(fill="x")
        ttk.Label(hdr, text="My Car Listings", style="CardHeading.TLabel").pack(side="left")
        ttk.Button(hdr, text="Back", style="Ghost.TButton",
                   command=lambda: self.notify("navigate", "dashboard")).pack(side="right")

        cols = ("ID", "Year", "Make", "Model", "Location", "$/Day", "Available")
        widths = {"ID":50,"Year":60,"Make":90,"Model":100,"Location":150,"$/Day":80,"Available":80}
        self._tree = make_scrolled_treeview(self, cols, heights=10, col_widths=widths)

        make_action_bar(self, [
            ("Refresh",          "Ghost.TButton",  self._refresh),
            ("Edit Selected",    "Accent.TButton", self._edit),
            ("Manage Calendar",  "Ghost.TButton",  self._manage_calendar),
        ])

        self._refresh()

    def _refresh(self):
        uid = SessionManager().user_id
        self._cars = CarService.get_owner_cars(uid) if uid else []
        for r in self._tree.get_children():
            self._tree.delete(r)
        for c in self._cars:
            self._tree.insert("", "end", values=(
                c["id"], c["year"], c["make"], c["model"],
                c["location"], f"${c['price_per_day']:.2f}",
                "Yes" if c["available"] else "No"
            ))

    def _edit(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a car to edit.")
            return
        car = self._cars[self._tree.index(sel[0])]
        EditListingDialog(self, car)
        self._refresh()

    def _manage_calendar(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a car to manage its calendar.")
            return
        car = self._cars[self._tree.index(sel[0])]
        AvailabilityCalendarDialog(self, car)

    def refresh_current(self):
        self._refresh()


class EditListingDialog(tk.Toplevel):

    def __init__(self, parent, car):
        super().__init__(parent)
        self.title(f"Edit: {car['year']} {car['make']} {car['model']}")
        self.configure(bg=Colors.BG_DARK)
        self.resizable(False, False)
        self._car = car

        card = make_card(self, padding=24)
        card.pack(padx=20, pady=20)
        card.columnconfigure(1, weight=1)

        ttk.Label(card, text=f"Editing: {car['year']} {car['make']} {car['model']}",
                  style="CardHeading.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,14))

        ttk.Label(card, text="Price / Day ($)", style="CardMuted.TLabel").grid(
            row=1, column=0, sticky="w", padx=(0,12), pady=6
        )
        self._price = tk.StringVar(value=str(car["price_per_day"]))
        ttk.Entry(card, textvariable=self._price, width=16).grid(row=1, column=1, sticky="ew", pady=6)

        self._avail = tk.BooleanVar(value=bool(car["available"]))
        ttk.Checkbutton(card, text="Available for Rent", variable=self._avail).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=6
        )

        ttk.Label(card, text="Description", style="CardMuted.TLabel").grid(
            row=3, column=0, sticky="nw", padx=(0,12), pady=6
        )
        self._desc = styled_text(card, height=4, width=30)
        self._desc.insert("1.0", car.get("description", ""))
        self._desc.grid(row=3, column=1, sticky="ew", pady=6)

        btn_bar = ttk.Frame(card, style="Card.TFrame")
        btn_bar.grid(row=4, column=0, columnspan=2, pady=(14, 0))
        ttk.Button(btn_bar, text="Save Changes", style="Accent.TButton",
                   command=self._save).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="Cancel", style="Ghost.TButton",
                   command=self.destroy).pack(side="left", padx=4)

        self.grab_set()
        parent.wait_window(self)

    def _save(self):
        try:
            price = float(self._price.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid price.", parent=self)
            return
        ok, msg = CarService.update_listing(
            self._car["id"], price, self._avail.get(),
            self._desc.get("1.0", "end").strip()
        )
        messagebox.showinfo("Update", msg, parent=self)
        self.destroy()


class AvailabilityCalendarDialog(tk.Toplevel):
    """
    Owner sets which dates are available or blocked for a specific car.
    Uses tkcalendar for a visual calendar widget.
    Dates not explicitly set are treated as available by default.
    """

    def __init__(self, parent, car):
        super().__init__(parent)
        self.title(f"Availability Calendar: {car['year']} {car['make']} {car['model']}")
        self.configure(bg=Colors.BG_DARK)
        self.geometry("520x480")
        self._car = car
        self._build()

    def _build(self):
        try:
            from tkcalendar import Calendar
        except ImportError:
            messagebox.showerror(
                "Missing Package",
                "Please install tkcalendar:\n\npip install tkcalendar",
                parent=self
            )
            self.destroy()
            return

        ttk.Label(self, text="Click a date then mark it Available or Blocked.",
                  style="Muted.TLabel").pack(pady=(16, 8))

        # load existing availability for this car
        self._availability = CarService.get_availability(self._car["id"])

        self._cal = Calendar(
            self,
            selectmode="day",
            date_pattern="yyyy-mm-dd",
            background=Colors.BG_CARD,
            foreground=Colors.TEXT_PRI,
            headersbackground=Colors.BG_DARK,
            headersforeground=Colors.TEXT_MUT,
            selectbackground=Colors.ACCENT,
            normalbackground=Colors.BG_CARD,
            normalforeground=Colors.TEXT_PRI,
            weekendbackground=Colors.BG_CARD,
            weekendforeground=Colors.TEXT_MUT,
            othermonthbackground=Colors.BG_DARK,
            othermonthforeground="#444444",
            font=Fonts.BODY
        )
        self._cal.pack(padx=20, pady=8, fill="both", expand=True)

        # highlight already-set dates
        self._refresh_highlights()

        btn_bar = ttk.Frame(self, style="TFrame")
        btn_bar.pack(pady=12)

        ttk.Button(btn_bar, text="Mark Available", style="Success.TButton",
                   command=lambda: self._set(1)).pack(side="left", padx=6)
        ttk.Button(btn_bar, text="Mark Blocked", style="Danger.TButton",
                   command=lambda: self._set(0)).pack(side="left", padx=6)
        ttk.Button(btn_bar, text="Close", style="Ghost.TButton",
                   command=self.destroy).pack(side="left", padx=6)

        self._status = ttk.Label(self, text="", style="Muted.TLabel")
        self._status.pack()

    def _set(self, is_available):
        selected = self._cal.get_date()
        CarService.set_availability(self._car["id"], selected, is_available)
        self._availability = CarService.get_availability(self._car["id"])
        self._refresh_highlights()
        status = "Available" if is_available else "Blocked"
        self._status.config(text=f"{selected} marked as {status}.")

    def _refresh_highlights(self):
        # clear all existing tags first
        self._cal.calevent_remove("all")

        for date_str, is_avail in self._availability.items():
            try:
                year, month, day = map(int, date_str.split("-"))
                import datetime
                d = datetime.date(year, month, day)
                if is_avail:
                    self._cal.calevent_create(d, "Available", "available")
                else:
                    self._cal.calevent_create(d, "Blocked", "blocked")
            except Exception:
                pass

        self._cal.tag_config("available", background="#16a34a", foreground="white")
        self._cal.tag_config("blocked",   background="#dc2626", foreground="white")


class MyBookingsFrame(UIComponent, ttk.Frame):

    def __init__(self, parent, mediator):
        ttk.Frame.__init__(self, parent)
        UIComponent.__init__(self, mediator)
        self._bookings = []
        self._build()

    def _build(self):
        hdr = make_card(self, padding=(20, 14))
        hdr.pack(fill="x")
        ttk.Label(hdr, text="My Bookings", style="CardHeading.TLabel").pack(side="left")
        ttk.Button(hdr, text="Back", style="Ghost.TButton",
                   command=lambda: self.notify("navigate", "dashboard")).pack(side="right")

        cols = ("ID", "Car", "Location", "Start", "End", "Total", "Status")
        widths = {"ID":50,"Car":140,"Location":120,"Start":90,"End":90,"Total":80,"Status":90}
        self._tree = make_scrolled_treeview(self, cols, heights=13, col_widths=widths)

        make_action_bar(self, [
            ("Refresh",        "Ghost.TButton",   self._refresh),
            ("Pay Selected",   "Success.TButton", self._pay),
            ("Cancel Selected","Danger.TButton",  self._cancel),
        ])

        self._refresh()

    def _refresh(self):
        uid = SessionManager().user_id
        self._bookings = BookingService.get_user_bookings(uid) if uid else []
        for r in self._tree.get_children():
            self._tree.delete(r)
        for b in self._bookings:
            status_label = {
                "pending":   "Pending",
                "confirmed": "Confirmed",
                "cancelled": "Cancelled",
                "completed": "Completed"
            }.get(b["status"], b["status"])
            self._tree.insert("", "end", values=(
                b["id"], f"{b['year']} {b['make']} {b['model']}",
                b["location"], b["start_date"], b["end_date"],
                f"${b['total_price']:.2f}", status_label
            ))

    def _selected(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a booking first.")
            return None
        return self._bookings[self._tree.index(sel[0])]

    def _pay(self):
        b = self._selected()
        if not b:
            return
        ok, msg = BookingService.pay_booking(b["id"])
        messagebox.showinfo("Payment", msg)
        self._refresh()
        if ok:
            self.notify("booking_created", b["id"])

    def _cancel(self):
        b = self._selected()
        if not b:
            return
        if messagebox.askyesno("Confirm", "Cancel this booking?"):
            ok, msg = BookingService.cancel_booking(b["id"])
            messagebox.showinfo("Cancel", msg)
            self._refresh()

    def refresh_current(self):
        self._refresh()