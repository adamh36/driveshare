"""
models/auth.py
CIS 476 Term Project: DriveShare

AuthService handles login, registration, and logout.
Talks to the database and updates the SessionManager singleton.
"""

import bcrypt
from db.database import get_connection
from Patterns.ui_singleton import SessionManager


class AuthService:

    @staticmethod
    def login(email, password):
        if not email or not password:
            return False, "Please fill in all fields."

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user is None:
            return False, "No account found with that email."

        if not bcrypt.checkpw(password.encode("utf-8"), user["password"]):
            return False, "Incorrect password."

        user_dict = {
            "id":       user["id"],
            "username": user["name"],
            "email":    user["email"],
            "role":     user["role"],
            "balance":  AuthService._get_balance(user["id"])
        }

        SessionManager().login(user_dict)
        return True, "Login successful."

    @staticmethod
    def register(username, email, password, role, q1, a1, q2, a2, q3, a3):
        # role is now passed in from the register form — owner, renter, or both
        if not all([username, email, password, role, q1, a1, q2, a2, q3, a3]):
            return False, "Please fill in all fields."

        if "@" not in email or "." not in email:
            return False, "Please enter a valid email address."

        if len(password) < 6:
            return False, "Password must be at least 6 characters."

        if role not in ("owner", "renter", "both"):
            return False, "Please select a valid role."

        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                (username, email, hashed, role)
            )
            user_id = cursor.lastrowid

            for question, answer in [(q1, a1), (q2, a2), (q3, a3)]:
                cursor.execute(
                    "INSERT INTO security_questions (user_id, question, answer) VALUES (?, ?, ?)",
                    (user_id, question, answer)
                )

            conn.commit()
            conn.close()
            return True, "Account created successfully. You can now log in."

        except Exception:
            conn.close()
            return False, "An account with that email already exists."

    @staticmethod
    def logout():
        SessionManager().logout()

    @staticmethod
    def _get_balance(user_id):
        # starts everyone at $500, adds received payments, subtracts spent
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COALESCE(SUM(p.amount), 0) AS received
            FROM payments p
            JOIN bookings b ON p.booking_id = b.id
            JOIN cars c ON b.car_id = c.id
            WHERE c.owner_id = ? AND p.status = 'completed'
        """, (user_id,))
        received = cursor.fetchone()["received"]

        cursor.execute("""
            SELECT COALESCE(SUM(p.amount), 0) AS spent
            FROM payments p
            JOIN bookings b ON p.booking_id = b.id
            WHERE b.renter_id = ? AND p.status = 'completed'
        """, (user_id,))
        spent = cursor.fetchone()["spent"]

        conn.close()
        return 500.0 + received - spent