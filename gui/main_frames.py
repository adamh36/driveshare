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

        grid = ttk.Frame(self)
        grid.pack(fill="x", padx=20)

        actions = [
            ("Search Cars",   "search",       "Find and book available cars near you"),
            ("List a Car",    "list_car",     "Earn money by renting out your vehicle"),
            ("My Listings",   "my_listings",  "Manage your car listings"),
            ("My Bookings",   "my_bookings",  "View and pay for your bookings"),
            ("Messages",      "messages",     "Chat with owners and renters"),
            ("Notifications", "notifications","View alerts and updates"),
            ("Reviews",       "reviews",      "Leave and view rental reviews"),
        ]

        for i, (title, frame_name, desc) in enumerate(actions):
            row, col = divmod(i, 3)
            card = make_card(grid, padding=18)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            grid.columnconfigure(col, weight=1)

            ttk.Label(card, text=title, style="CardHeading.TLabel").pack(anchor="w", pady=(4, 2))
            ttk.Label(card, text=desc, style="CardMuted.TLabel",
                      wraplength=180).pack(anchor="w", pady=(0, 10))
            ttk.Button(card, text="Open", style="Ghost.TButton",
                       command=lambda f=frame_name: self.notify("navigate", f)).pack(anchor="w")

        self._refresh_header()

    def _refresh_header(self):
        user = SessionManager().current_user
        if user:
            self._welcome_lbl.config(text=f"Welcome back, {user['username']}!")
            self._balance_lbl.config(text=f"Balance: ${user['balance']:.2f}")

    def refresh_current(self):
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
        self._start_date = lbl_entry(row1, "From", str(date.today() + timedelta(days=1)), 12)
        self._end_date   = lbl_entry(row1, "To",   str(date.today() + timedelta(days=4)), 12)
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
            "Watch Car", "Max price/day to be notified (leave blank for any):",
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
        self._tree = make_scrolled_treeview(self, cols, heights=13, col_widths=widths)

        make_action_bar(self, [
            ("Refresh",       "Ghost.TButton",  self._refresh),
            ("Edit Selected", "Accent.TButton", self._edit),
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

        ttk.Label(card, text="Price / Day ($)", style="CardMuted.TLabel").grid(row=1, column=0, sticky="w", padx=(0,12), pady=6)
        self._price = tk.StringVar(value=str(car["price_per_day"]))
        ttk.Entry(card, textvariable=self._price, width=16).grid(row=1, column=1, sticky="ew", pady=6)

        self._avail = tk.BooleanVar(value=bool(car["available"]))
        ttk.Checkbutton(card, text="Available for Rent", variable=self._avail).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=6
        )

        ttk.Label(card, text="Description", style="CardMuted.TLabel").grid(row=3, column=0, sticky="nw", padx=(0,12), pady=6)
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
            ("Cancel Selected","Danger.TButton",   self._cancel),
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
                "cancelled": "Cancelled"
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