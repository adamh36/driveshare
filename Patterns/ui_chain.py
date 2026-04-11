"""
CHAIN OF RESPONSIBILITY: Password Recovery Service (Tkinter wrapper)
CIS 476 Term Project: DriveShare

Wraps the RecoveryManager from Patterns/password_chain.py and exposes
the interface the Tkinter ForgotPasswordFrame expects.
"""

import bcrypt
from db.database import get_connection
from Patterns.password_chain import RecoveryManager


class PasswordRecoveryService:

    def __init__(self):
        self._manager = RecoveryManager()

    def get_security_questions(self, email):
        """
        Returns a dict with question1/question2/question3 keys,
        or None if the email doesn't exist.
        """
        rows = self._manager.getSecurityQuestions(email)

        if not rows or len(rows) < 3:
            return None

        return {
            "question1": rows[0]["question"],
            "question2": rows[1]["question"],
            "question3": rows[2]["question"],
        }

    def verify_and_reset(self, email, a1, a2, a3, new_password):
        """
        Runs the answers through the chain of responsibility.
        Returns (True, message) or (False, error).
        """
        rows = self._manager.getSecurityQuestions(email)

        if not rows or len(rows) < 3:
            return False, "Account not found."

        answers = {"a1": a1, "a2": a2, "a3": a3}
        passed = self._manager.verifyAnswers(answers, rows)

        if not passed:
            return False, "One or more answers are incorrect."

        self._manager.resetPassword(email, new_password)
        return True, "Password reset successfully. You can now log in."