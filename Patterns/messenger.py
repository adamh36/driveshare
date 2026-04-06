"""
MESSAGING LOGIC
CIS 476 Term Project: DriveShare
 
Functions to send messages between users and fetch conversation history.
Messages are stored in the messages table:
    sender_id, receiver_id, content, is_read, created_at
"""
 
from db.database import get_connection
 
 
def sendMessage(senderId, receiverId, content):
    """
    Insert a new message from senderId to receiverId into the messages table.
    Returns True on success, False on failure.
    """
    if not content or not content.strip():
        return False
 
    conn = get_connection()
    cursor = conn.cursor()
 
    cursor.execute("""
        INSERT INTO messages (sender_id, receiver_id, content, is_read)
        VALUES (?, ?, ?, 0)
    """, (senderId, receiverId, content.strip()))
 
    conn.commit()
    conn.close()
 
    return True
 
 
def getConversation(userId, otherId):
    """
    Fetch all messages exchanged between userId and otherId,
    ordered oldest to newest.
    Also marks any unread messages sent TO userId as read.
    Returns a list of Row objects with all message columns.
    """
    conn = get_connection()
    cursor = conn.cursor()
 
    # mark messages sent to the current user as read
    cursor.execute("""
        UPDATE messages
        SET is_read = 1
        WHERE sender_id = ? AND receiver_id = ? AND is_read = 0
    """, (otherId, userId))
 
    # fetch the full conversation in chronological order
    cursor.execute("""
        SELECT m.id, m.sender_id, m.receiver_id, m.content, m.is_read, m.created_at,
               s.name AS sender_name
        FROM messages m
        LEFT JOIN users s ON m.sender_id = s.id
        WHERE (m.sender_id = ? AND m.receiver_id = ?)
           OR (m.sender_id = ? AND m.receiver_id = ?)
        ORDER BY m.created_at ASC
    """, (userId, otherId, otherId, userId))
 
    messages = cursor.fetchall()
    conn.commit()
    conn.close()
 
    return messages
 
 
def getAllUsers(excludeId):
    """
    Return all users except the one currently logged in.
    Used to populate the recipient selector in the UI.
    """
    conn = get_connection()
    cursor = conn.cursor()
 
    cursor.execute("""
        SELECT id, name, email FROM users WHERE id != ?
        ORDER BY name ASC
    """, (excludeId,))
 
    users = cursor.fetchall()
    conn.close()
 
    return users
 
 
def getUnreadCount(userId):
    """
    Return the number of unread messages for a given user.
    Useful for showing a badge/count in the UI.
    """
    conn = get_connection()
    cursor = conn.cursor()
 
    cursor.execute("""
        SELECT COUNT(*) AS count FROM messages
        WHERE receiver_id = ? AND is_read = 0
    """, (userId,))
 
    row = cursor.fetchone()
    conn.close()
 
    return row["count"] if row else 0