"""
MESSAGING PAGE
CIS 476 Term Project: DriveShare
 
Streamlit UI: lets a logged-in user pick another user and
view/send messages in a chat-style conversation.
"""
 
import streamlit as st
from Patterns.session import session
from Patterns.messenger import sendMessage, getConversation, getAllUsers, getUnreadCount
 
# --- Auth gate ---
if not session.is_logged_in():
    st.warning("Please log in to view your messages.")
    st.stop()
 
currentUser = session.get_user()
currentId   = currentUser["id"]
currentName = currentUser["name"]
 
# --- Page header ---
st.title("💬 Messages")
 
unread = getUnreadCount(currentId)
if unread > 0:
    st.info(f"You have **{unread}** unread message{'s' if unread != 1 else ''}.")
 
# --- User selector ---
allUsers = getAllUsers(excludeId=currentId)
 
if not allUsers:
    st.write("No other users are registered yet.")
    st.stop()
 
# build a label → id map for the selectbox
userOptions = {f"{u['name']} ({u['email']})": u["id"] for u in allUsers}
userLabels  = list(userOptions.keys())
 
selectedLabel = st.selectbox("Select a user to message:", userLabels)
selectedId    = userOptions[selectedLabel]
selectedName  = selectedLabel.split(" (")[0]
 
st.divider()
 
# --- Conversation history ---
st.subheader(f"Conversation with {selectedName}")
 
messages = getConversation(userId=currentId, otherId=selectedId)
 
if not messages:
    st.write("No messages yet. Say hello! 👋")
else:
    for msg in messages:
        if msg["sender_id"] == currentId:
            # messages sent by the current user
            with st.chat_message("user"):
                st.write(msg["content"])
                st.caption(f"You · {msg['created_at']}")
        else:
            # messages received from the other user
            with st.chat_message("assistant"):
                st.write(msg["content"])
                st.caption(f"{msg['sender_name']} · {msg['created_at']}")
 
st.divider()
 
# --- Send message form ---
st.subheader("Send a message")
 
messageText = st.text_area("Your message", placeholder=f"Write something to {selectedName}...", height=100)
 
if st.button("Send", type="primary"):
    if not messageText.strip():
        st.error("Message cannot be empty.")
    else:
        ok = sendMessage(senderId=currentId, receiverId=selectedId, content=messageText)
        if ok:
            st.success("Message sent!")
            st.rerun()
        else:
            st.error("Something went wrong. Please try again.")