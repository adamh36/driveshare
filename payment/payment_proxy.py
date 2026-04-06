"""
PROXY DESIGN PATTERN: Payment Processing
CIS 476 Term Project: DriveShare
 
This file simulates a payment system using the Proxy pattern.
PaymentService is the real subject that processes payments.
PaymentProxy wraps it, controls access, updates the database,
and sends notifications to both the owner and renter.
"""
 
from database import get_connection
 
 
# REAL SUBJECT
# this is the actual payment service — the thing doing the real work
# in a real app this would talk to Stripe, PayPal, etc.
# here we simulate it: we just print and return True to say it succeeded
class PaymentService:
 
    def processPayment(self, bookingId, amount):
        # simulate charging the renter
        # in production this would call an external payment API
        print(f"[PaymentService] Processing payment of ${amount:.2f} for booking #{bookingId}...")
        # simulate success — in real life this could return False on failure
        return True
 
 
# PROXY
# this wraps PaymentService and adds three extra responsibilities:
#   1. calls the real PaymentService to process the payment
#   2. updates the payments table in the db to 'completed' (or 'failed')
#   3. sends a message notification to both the owner and the renter
# the caller never touches PaymentService directly — it only talks to the proxy
class PaymentProxy:
 
    def __init__(self):
        # create the real service — the proxy holds a reference to it
        self._realService = PaymentService()
 
    def processPayment(self, bookingId, amount):
        # step 1: delegate to the real payment service
        success = self._realService.processPayment(bookingId, amount)
 
        # step 2: update the payment record in the database
        self._updatePaymentStatus(bookingId, amount, success)
 
        # step 3: notify owner and renter regardless of outcome
        self._sendNotifications(bookingId, success)
 
        return success
 
    def _updatePaymentStatus(self, bookingId, amount, success):
        # determine the status string based on whether payment succeeded
        status = "completed" if success else "failed"
 
        conn = get_connection()
        cursor = conn.cursor()
 
        # check if a payment record already exists for this booking
        cursor.execute("SELECT id FROM payments WHERE booking_id = ?", (bookingId,))
        existing = cursor.fetchone()
 
        if existing:
            # update the existing record
            cursor.execute("""
                UPDATE payments SET status = ? WHERE booking_id = ?
            """, (status, bookingId))
        else:
            # insert a fresh payment record
            cursor.execute("""
                INSERT INTO payments (booking_id, amount, status)
                VALUES (?, ?, ?)
            """, (bookingId, amount, status))
 
        conn.commit()
        conn.close()
 
        print(f"[PaymentProxy] Payment record for booking #{bookingId} set to '{status}'.")
 
    def _sendNotifications(self, bookingId, success):
        # look up the booking to find the renter and the owner of the car
        conn = get_connection()
        cursor = conn.cursor()
 
        cursor.execute("""
            SELECT b.renter_id, c.owner_id, b.total_price,
                   c.make, c.model, c.year
            FROM bookings b
            JOIN cars c ON b.car_id = c.id
            WHERE b.id = ?
        """, (bookingId,))
 
        booking = cursor.fetchone()
 
        if not booking:
            conn.close()
            print(f"[PaymentProxy] Booking #{bookingId} not found — skipping notifications.")
            return
 
        renterId  = booking["renter_id"]
        ownerId   = booking["owner_id"]
        amount    = booking["total_price"]
        carLabel  = f"{booking['year']} {booking['make']} {booking['model']}"
 
        if success:
            renterMsg = (
                f"Your payment of ${amount:.2f} for the {carLabel} (booking #{bookingId}) "
                f"was processed successfully. Enjoy your trip!"
            )
            ownerMsg = (
                f"Great news! A payment of ${amount:.2f} has been received for your "
                f"{carLabel} (booking #{bookingId})."
            )
        else:
            renterMsg = (
                f"Your payment of ${amount:.2f} for the {carLabel} (booking #{bookingId}) "
                f"failed. Please update your payment details and try again."
            )
            ownerMsg = (
                f"A payment of ${amount:.2f} for your {carLabel} (booking #{bookingId}) "
                f"failed. The renter has been notified."
            )
 
        # use sender_id = None to mark these as system notifications,
        # consistent with how the observer pattern sends notifications
        cursor.execute("""
            INSERT INTO messages (sender_id, receiver_id, content)
            VALUES (?, ?, ?)
        """, (None, renterId, renterMsg))
 
        cursor.execute("""
            INSERT INTO messages (sender_id, receiver_id, content)
            VALUES (?, ?, ?)
        """, (None, ownerId, ownerMsg))
 
        conn.commit()
        conn.close()
 
        print(f"[PaymentProxy] Notifications sent to renter #{renterId} and owner #{ownerId}.")