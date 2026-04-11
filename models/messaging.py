"""
models/messaging.py
CIS 476 Term Project: DriveShare

MessageService    — direct user-to-user messages
NotificationService — system notifications (sender_id = 1)
ReviewService     — reviews after completed bookings
"""

from db.database import get_connection
from Patterns.ui_singleton import SessionManager


class MessageService:

    @staticmethod
    def send_message(to_id, content):
        user_id = SessionManager().user_id
        if not user_id:
            return False, "You must be logged in."

        if not content or not content.strip():
            return False, "Message cannot be empty."

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO messages (sender_id, receiver_id, content, is_read)
            VALUES (?, ?, ?, 0)
        """, (user_id, to_id, content.strip()))
        conn.commit()
        conn.close()
        return True, "Message sent."

    @staticmethod
    def get_inbox(user_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.id, m.sender_id, m.receiver_id, m.content,
                   m.is_read, m.created_at AS sent_at,
                   u.name AS sender_name
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.receiver_id = ? AND m.sender_id != 1
            ORDER BY m.created_at DESC
        """, (user_id,))
        messages = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return messages

    @staticmethod
    def mark_read(message_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE messages SET is_read = 1 WHERE id = ?", (message_id,))
        conn.commit()
        conn.close()


class NotificationService:

    @staticmethod
    def get_notifications(user_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, content AS message, is_read, created_at
            FROM messages
            WHERE receiver_id = ? AND sender_id = 1
            ORDER BY created_at DESC
        """, (user_id,))
        notifs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return notifs

    @staticmethod
    def mark_all_read(user_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE messages SET is_read = 1
            WHERE receiver_id = ? AND sender_id = 1
        """, (user_id,))
        conn.commit()
        conn.close()


class ReviewService:

    @staticmethod
    def leave_review(booking_id, reviewee_id, rating, comment=""):
        user_id = SessionManager().user_id
        if not user_id:
            return False, "You must be logged in."

        if not 1 <= rating <= 5:
            return False, "Rating must be between 1 and 5."

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM reviews WHERE booking_id = ? AND reviewer_id = ?",
            (booking_id, user_id)
        )
        if cursor.fetchone():
            conn.close()
            return False, "You have already reviewed this booking."

        cursor.execute("""
            INSERT INTO reviews (booking_id, reviewer_id, reviewee_id, rating, comment)
            VALUES (?, ?, ?, ?, ?)
        """, (booking_id, user_id, reviewee_id, rating, comment))
        conn.commit()
        conn.close()
        return True, "Review submitted."

    @staticmethod
    def get_reviews_for_user(user_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.rating, r.comment, r.created_at,
                   u.name AS reviewer_name
            FROM reviews r
            JOIN users u ON r.reviewer_id = u.id
            WHERE r.reviewee_id = ?
            ORDER BY r.created_at DESC
        """, (user_id,))
        reviews = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return reviews