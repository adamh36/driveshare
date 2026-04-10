"""
CHAIN OF RESPONSIBILITY PATTERN: Password Recovery
CIS 476 Term Project: DriveShare

This file handles password recovery using the Chain of Responsibility pattern.
The UI for this lives in gui/auth_frames.py (ForgotPasswordFrame).
"""

import bcrypt
from abc import ABC, abstractmethod
from db.database import get_connection


# ABSTRACT HANDLER
# base class for every question in the chain
# setNext() links handlers together, handle() checks the answer
class SecurityQuestionHandler(ABC):

    def __init__(self):
        self.nextHandler = None

    def setNext(self, handler):
        # returns the handler so we can chain: q1.setNext(q2).setNext(q3)
        self.nextHandler = handler
        return handler

    @abstractmethod
    def handle(self, answers, storedQuestions):
        pass


# CONCRETE HANDLER 1
class Question1Handler(SecurityQuestionHandler):

    def handle(self, answers, storedQuestions):
        storedAnswer = storedQuestions[0]["answer"].strip().lower()
        userAnswer = answers.get("a1", "").strip().lower()

        if userAnswer != storedAnswer:
            return False

        if self.nextHandler:
            return self.nextHandler.handle(answers, storedQuestions)

        return True


# CONCRETE HANDLER 2
class Question2Handler(SecurityQuestionHandler):

    def handle(self, answers, storedQuestions):
        storedAnswer = storedQuestions[1]["answer"].strip().lower()
        userAnswer = answers.get("a2", "").strip().lower()

        if userAnswer != storedAnswer:
            return False

        if self.nextHandler:
            return self.nextHandler.handle(answers, storedQuestions)

        return True


# CONCRETE HANDLER 3
class Question3Handler(SecurityQuestionHandler):

    def handle(self, answers, storedQuestions):
        storedAnswer = storedQuestions[2]["answer"].strip().lower()
        userAnswer = answers.get("a3", "").strip().lower()

        if userAnswer != storedAnswer:
            return False

        if self.nextHandler:
            return self.nextHandler.handle(answers, storedQuestions)

        return True


# RECOVERY MANAGER
# builds the chain and coordinates the full recovery flow
class RecoveryManager:

    def getSecurityQuestions(self, email):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sq.question, sq.answer
            FROM security_questions sq
            JOIN users u ON sq.user_id = u.id
            WHERE u.email = ?
            ORDER BY sq.id ASC
        """, (email,))
        questions = cursor.fetchall()
        conn.close()
        return questions

    def buildChain(self):
        q1 = Question1Handler()
        q2 = Question2Handler()
        q3 = Question3Handler()
        q1.setNext(q2).setNext(q3)
        return q1

    def verifyAnswers(self, answers, storedQuestions):
        chain = self.buildChain()
        return chain.handle(answers, storedQuestions)

    def resetPassword(self, email, newPassword):
        hashed = bcrypt.hashpw(newPassword.encode("utf-8"), bcrypt.gensalt())
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = ? WHERE email = ?", (hashed, email))
        conn.commit()
        conn.close()