"""
BOOKING SYSTEM + OBSERVER PATTERN
CIS 476 Term Project: DriveShare

This file handles two things:
1. Booking logic: taking a car, a renter, and a date range and creating a booking
   while making sure no two bookings overlap (conflict prevention)
2. Observer pattern: notifying renters when a car they're watching
   becomes available or drops in price
"""

from abc import ABC, abstractmethod
from db.database import get_connection



# OBSERVER PATTERN


# OBSERVER (abstract)
# this is just the interface: it doesn't do anything on its own
# it just forces every concrete observer (renter/user) to implement update()
# think of it as a contract: if you want to watch a car, you MUST
# have an update() method so the car knows how to reach you
class RenterObserver(ABC):

    @abstractmethod
    def update(self, carId, eventType, message): pass
    # eventType will be something like "available" or "price_drop"
    # message is the actual text the renter will see


# CONCRETE OBSERVER
# this is the actual renter: the one who clicked "select/watch car"
# when the car (subject) calls notify(), it ends up here
# update() is where the real reaction happens:
# we go into the database and store a notification for this renter

class Renter(RenterObserver):

    def __init__(self, renterId, renterEmail):
        # who this renter is: we need the id for the db and email for display
        self.renterId = renterId
        self.renterEmail = renterEmail

    def update(self, carId, eventType, message):
        # this fires whenever the car we're watching has news for us
        # we just save it to the db as a notification: the UI will show it later
        print(f"Notifying {self.renterEmail}: {message}")

        conn = get_connection()
        cursor = conn.cursor()

        # store the notification so the renter sees it when they log in
        cursor.execute("""
            INSERT INTO messages (sender_id, receiver_id, content)
            VALUES (?, ?, ?)
        """, (
            None,       # no sender, this is a system notification
            self.renterId,
            message
        ))

        conn.commit()
        conn.close()


# SUBJECT
# this is the car: the thing being watched
# it holds the list of all renters (observers/subscribers) who are watching it
# and it's responsible for notifying them when something changes
# three jobs: subscribe (add a watcher), unsubscribe (remove a watcher), notify (alert everyone)
# the subject doesn't care who is watching or what they'll do:

class CarSubject:

    def __init__(self, carId):
        self.carId = carId
        # this is the list of renters watching this car
        # each entry is a RenterObserver (a Renter object)
        self.observers = []

    def subscribe(self, observer):
        # renter clicked "watch this car": add them to the list
        self.observers.append(observer)
        print(f"Renter {observer.renterEmail} is now watching car {self.carId}")

    def unsubscribe(self, observer):
        # renter stopped watching: remove them from the list
        self.observers.remove(observer)
        print(f"Renter {observer.renterEmail} stopped watching car {self.carId}")

    def notify(self, eventType, message):
        # something happened to the car: loop through every watcher and tell them
        # each observer handles the notification in their own update() method
        for observer in self.observers:
            observer.update(self.carId, eventType, message)



# BOOKING LOGIC


# BOOKING MANAGER
# this handles creating bookings and checking for conflicts
# before creating any booking, we check the database to see if the car is already booked
# for any overlapping dates. if it is, we reject the booking entirely.
# after a successful booking, it also fires the observer notification
# so any renters watching that car know it just got booked
class BookingManager:

    def __init__(self):
        # each car gets its own CarSubject to manage its watchers
        # key = carId, value = CarSubject
        # we load watchers from the db when a car subject is first created
        self.carSubjects = {}

    def getCarSubject(self, carId):
        # if we haven't created a subject for this car yet, make one
        # and load all its watchers from the watched_cars table
        if carId not in self.carSubjects:
            self.carSubjects[carId] = CarSubject(carId)
            self.loadWatchers(carId)
        return self.carSubjects[carId]

    def loadWatchers(self, carId):
        # grab everyone who is watching this car from the db
        # and subscribe them to the car's subject
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT u.id, u.email
            FROM watched_cars wc
            JOIN users u ON wc.user_id = u.id
            WHERE wc.car_id = ?
        """, (carId,))

        watchers = cursor.fetchall()
        conn.close()

        # create a Renter observer for each watcher and subscribe them
        for watcher in watchers:
            renter = Renter(renterId=watcher["id"], renterEmail=watcher["email"])
            self.carSubjects[carId].subscribe(renter)

    def checkOverlap(self, carId, startDate, endDate):
        # this is the conflict prevention check
        # we look in the bookings table for any existing booking on this car
        # where the dates overlap with what's being requested
        # the overlap condition: existing booking starts before our end
        # AND existing booking ends after our start
        # if both are true, the dates clash and we reject the booking
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id FROM bookings
            WHERE car_id = ?
            AND status NOT IN ('cancelled')
            AND start_date < ?
            AND end_date > ?
        """, (carId, endDate, startDate))

        conflict = cursor.fetchone()
        conn.close()

        # returns True if there's a conflict, False if the car is free
        return conflict is not None

    def createBooking(self, carId, renterId, startDate, endDate, totalPrice):
        # step 1: check for overlapping bookings: reject if conflict found
        if self.checkOverlap(carId, startDate, endDate):
            print(f"Booking rejected: car {carId} is already booked for those dates.")
            return False

        # step 2: no conflict, so go ahead and insert the booking
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO bookings (car_id, renter_id, start_date, end_date, total_price, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        """, (carId, renterId, startDate, endDate, totalPrice))

        conn.commit()
        conn.close()

        print(f"Booking created for car {carId} from {startDate} to {endDate}.")

        # step 3: notify all watchers that this car just got booked
        # so they know it's no longer available for those dates
        subject = self.getCarSubject(carId)
        subject.notify(
            eventType="booked",
            message=f"A car you are watching (car #{carId}) has just been booked from {startDate} to {endDate}."
        )

        return True

    def cancelBooking(self, bookingId):
        # cancel a booking and notify watchers that the car is available again
        conn = get_connection()
        cursor = conn.cursor()

        # grab the car id before we cancel so we can notify watchers
        cursor.execute("SELECT car_id, start_date, end_date FROM bookings WHERE id = ?", (bookingId,))
        booking = cursor.fetchone()

        if not booking:
            print(f"Booking {bookingId} not found.")
            conn.close()
            return False

        # flip the status to cancelled
        cursor.execute("UPDATE bookings SET status = 'cancelled' WHERE id = ?", (bookingId,))
        conn.commit()
        conn.close()

        print(f"Booking {bookingId} cancelled.")

        # notify all watchers: the car is free again!
        subject = self.getCarSubject(booking["car_id"])
        subject.notify(
            eventType="available",
            message=f"Good news! A car you are watching (car #{booking['car_id']}) just became available from {booking['start_date']} to {booking['end_date']}."
        )

        return True

    def watchCar(self, carId, renterId, renterEmail, maxPrice=None):
        # renter wants to watch a car: save it to watched_cars table
        # and subscribe them to the car's subject so they get notified
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO watched_cars (user_id, car_id, max_price)
            VALUES (?, ?, ?)
        """, (renterId, carId, maxPrice))

        conn.commit()
        conn.close()

        # create a Renter observer and subscribe them to this car's subject
        renter = Renter(renterId=renterId, renterEmail=renterEmail)
        subject = self.getCarSubject(carId)
        subject.subscribe(renter)

        print(f"Renter {renterEmail} is now watching car {carId}.")


# MAIN: just for debugging purposes
if __name__ == "__main__":

    manager = BookingManager()

    # try to create a booking
    manager.createBooking(
        carId=1,
        renterId=2,
        startDate="2026-04-10",
        endDate="2026-04-15",
        totalPrice=275.00
    )

    # try to create an overlapping booking: should get rejected
    manager.createBooking(
        carId=1,
        renterId=3,
        startDate="2026-04-12",
        endDate="2026-04-18",
        totalPrice=330.00
    )

    # cancel the first booking: watchers should get notified
    manager.cancelBooking(bookingId=1)