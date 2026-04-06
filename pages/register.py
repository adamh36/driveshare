import streamlit as st
import bcrypt
from database import get_connection
from auth.session import session 

st.title("Create an Account") 

name = st.text_input("Enter your Name: ")
email = st.text_input("Enter your email: ")
password = st.text_input("Enter a password: ", type="password")
role = st.selectbox("Select a role: ", ["owner", "renter", "both"])


SECURITY_QUESTIONS = [
    "What was the name of your first pet?",
    "What city were you born in?",
    "What is your mother's maiden name?",
    "What was the name of your elementary school?",
    "What was your childhood nickname?"
]

st.subheader("Security Questions")

q1 = st.selectbox("Question 1", SECURITY_QUESTIONS, key="q1")
a1 = st.text_input("Answer 1", key="a1")

q2 = st.selectbox("Question 2", SECURITY_QUESTIONS, key="q2")
a2 = st.text_input("Answer 2", key="a2")

q3 = st.selectbox("Question 3", SECURITY_QUESTIONS, key="q3")
a3 = st.text_input("Answer 3", key="a3")

if st.button("Register"):
    if name == "" or email =="" or password == "":
        st.write("Please fill all the fields")

    elif "@" not in email: 
        st.write("Invalid email")

    else:
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("INSERT INTO users(name, email, password, role) VALUES (?, ?, ?, ?)", 
                           (name, email, hashed, role)
                           )
            user_id = cursor.lastrowid # gives id just created 

            # insert 3 security questions using the user_id
            cursor.execute("INSERT INTO security_questions (user_id, question, answer) VALUES (?, ?, ?)",
                           (user_id, q1, a1)
                           )
            cursor.execute("INSERT INTO security_questions (user_id, question, answer) VALUES (?, ?, ?)",
                           (user_id, q2, a2)
                           )
            cursor.execute("INSERT INTO security_questions (user_id, question, answer) VALUES (?, ?, ?)",
                           (user_id, q3, a3)
                           )
            
            conn.commit()
            conn.close()

            session.login({"id": user_id, "name": name, "email": email, "role":role})
            st.success("Account created!")
            
        except Exception as e: 
            conn.close()
            st.error(f"Email already exists")


