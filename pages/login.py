import streamlit as st 
import bcrypt 
from db.database import get_connection
from Patterns.session import session

st.title("Login")

email = st.text_input("Enter your email: ")
password = st.text_input("Enter your password: ", type="password")


if st.button("Login"):
    if  email =="" or password == "":
        st.write("Please fill all the fields")

    elif "@" not in email: 
        st.write("Invalid email")

    else:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user is None:
            st.error("No account found with that email.")
    
        elif bcrypt.checkpw(password.encode("utf-8"), user["password"]):

            session.login({"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]})
            st.success(f"Welcome back {user['name']}!")
    
        else:
            st.error("Incorrect password.")
        
