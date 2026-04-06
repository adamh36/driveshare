"""
CHAIN OF RESPONSIBILITY PATTERN: Password Recovery
CIS 476 Term Project: DriveShare

This file handles password recovery using the Chain of Responsibility pattern.

"""

import bcrypt
import streamlit as st
from abc import ABC, abstractmethod
from database import get_connection
from Patterns.auth.session import session


# ABSTRACT HANDLER
# this is the base class for every question in the chain
# it has two jobs:
# 1. setNext() — links this handler to the next one in the chain
# 2. handle() — checks the answer, if correct passes to the next handler
# every concrete handler inherits from this and overrides handle()
# the chain is built by linking handlers together: q1:> q2:> q3
class SecurityQuestionHandler(ABC):

    def __init__(self):
        # the next handler in the chain, starts as None
        # gets set when we build the chain
        self.nextHandler = None

    def setNext(self, handler):
        # link this handler to the next one and return it
        # returning it lets us chain the calls like: q1.setNext(q2).setNext(q3)
        self.nextHandler = handler
        return handler

    @abstractmethod
    def handle(self, answers, storedQuestions):
        # every concrete handler must implement this
        # answers = dict of what the user typed in
        # storedQuestions = list of questions/answers from the db for this user
        pass


# CONCRETE HANDLER 1
# handles the first security question
# if the answer matches what's in the db, pass it to the next handler
# if not, stop the chain right here and return False
class Question1Handler(SecurityQuestionHandler):

    def handle(self, answers, storedQuestions):
        # grab the stored answer for question 1 and compare it to what the user typed
        storedAnswer = storedQuestions[0]["answer"].strip().lower()
        userAnswer = answers.get("a1", "").strip().lower()

        # wrong answer — chain stops here, recovery denied
        if userAnswer != storedAnswer:
            return False

        # correct — pass it down to the next handler if there is one
        if self.nextHandler:
            return self.nextHandler.handle(answers, storedQuestions)

        # no next handler means we're done and everything passed
        return True


# CONCRETE HANDLER 2
# same idea as handler 1 but for question 2
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
# last handler in the chain — question 3
# if this one passes, the whole chain passed and recovery is approved
class Question3Handler(SecurityQuestionHandler):

    def handle(self, answers, storedQuestions):
        storedAnswer = storedQuestions[2]["answer"].strip().lower()
        userAnswer = answers.get("a3", "").strip().lower()

        if userAnswer != storedAnswer:
            return False

        if self.nextHandler:
            return self.nextHandler.handle(answers, storedQuestions)

        # this is the end of the chain — all three passed, we're good
        return True


# RECOVERY MANAGER
# this is the client: it builds the chain and runs it
# it also handles fetching the questions from the db and updating the password
# think of it as the one coordinating everything:
# get the questions, build the chain, run the answers through it,
# and if it all passes, let the user reset their password
class RecoveryManager:

    def getSecurityQuestions(self, email):
        # look up the user by email and grab their 3 security questions
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

        # returns a list of 3 rows, each with question and answer
        # returns empty list if email not found
        return questions

    def buildChain(self):
        # build the chain: q1:> q2:> q3
        # setNext() returns the next handler so we can chain it inline
        q1 = Question1Handler()
        q2 = Question2Handler()
        q3 = Question3Handler()

        q1.setNext(q2).setNext(q3)

        # return the first handler — that's where we start the chain
        return q1

    def verifyAnswers(self, answers, storedQuestions):
        # build the chain and run the answers through it
        # returns True if all three pass, False if any one fails
        chain = self.buildChain()
        return chain.handle(answers, storedQuestions)

    def resetPassword(self, email, newPassword):
        # hash the new password and update it in the db
        hashed = bcrypt.hashpw(newPassword.encode("utf-8"), bcrypt.gensalt())

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users SET password = ? WHERE email = ?
        """, (hashed, email))

        conn.commit()
        conn.close()


# PASSWORD RECOVERY PAGE
# streamlit UI for the recovery flow
#   user enters their email
#   we show them their 3 security questions
#   they answer all three
#   answers go through the chain — pass = reset password, fail = denied

st.title("Password Recovery")

manager = RecoveryManager()

# we use session state to track which step we're on
#   email entry
#   answer questions
#   set new password
if "recoveryStep" not in st.session_state:
    st.session_state.recoveryStep = 1

if "recoveryEmail" not in st.session_state:
    st.session_state.recoveryEmail = None

if "recoveryQuestions" not in st.session_state:
    st.session_state.recoveryQuestions = None


# enter email
if st.session_state.recoveryStep == 1:

    st.subheader("Step 1: Enter your email")
    email = st.text_input("Email")

    if st.button("Continue"):
        if not email:
            st.error("Please enter your email.")
        else:
            questions = manager.getSecurityQuestions(email)

            if not questions:
                # don't tell them the email doesn't exist — security reason
                st.error("No account found with that email.")
            else:
                # save email and questions and move to step 2
                st.session_state.recoveryEmail = email
                st.session_state.recoveryQuestions = questions
                st.session_state.recoveryStep = 2
                st.rerun()


# answer security questions
elif st.session_state.recoveryStep == 2:

    st.subheader("Step 2: Answer your security questions")
    questions = st.session_state.recoveryQuestions

    # show each question and collect the answers
    a1 = st.text_input(questions[0]["question"], key="a1")
    a2 = st.text_input(questions[1]["question"], key="a2")
    a3 = st.text_input(questions[2]["question"], key="a3")

    if st.button("Verify Answers"):
        answers = {"a1": a1, "a2": a2, "a3": a3}

        # run the answers through the chain of responsibility
        passed = manager.verifyAnswers(answers, questions)

        if passed:
            # all three passed — move to step 3
            st.session_state.recoveryStep = 3
            st.rerun()
        else:
            st.error("One or more answers are incorrect. Please try again.")


# set new password
elif st.session_state.recoveryStep == 3:

    st.subheader("Step 3: Set a new password")

    newPassword = st.text_input("New Password", type="password")
    confirmPassword = st.text_input("Confirm Password", type="password")

    if st.button("Reset Password"):
        if not newPassword or not confirmPassword:
            st.error("Please fill in both fields.")

        elif newPassword != confirmPassword:
            st.error("Passwords don't match.")

        else:
            manager.resetPassword(st.session_state.recoveryEmail, newPassword)
            st.success("Password reset successfully! You can now log in.")

            # clear recovery state so it resets if they come back
            st.session_state.recoveryStep = 1
            st.session_state.recoveryEmail = None
            st.session_state.recoveryQuestions = None