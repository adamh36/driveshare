"""
OBSERVER PATTERN: Car Watch Notifications
CIS 476 Term Project: DriveShare

When a car's price drops or it becomes available, all renters watching
that car get an in-app notification via the messages table.

Pattern roles:
  Subject      → CarSubject (the car being watched)
  Observer     → WatcherObserver (each renter watching the car)
  ConcreteSubject → CarSubject.notify_watchers()
"""

from db.database import get_connection


class WatcherObserver:
    """
    Represents a single renter watching a car.
    Holds the watcher's user_id and their max acceptable price.
    """

    def __init__(self, user_id, max_price):
        self.user_id = user_id
        self.max_price = max_price

    def should_notify(self, car_price, car_available):
        # notify if the car is available AND the price is within the renter's budget
        return car_available == 1 and car_price <= self.max_price


class CarSubject:
    """
    The subject — represents a car that renters can watch.
    When something changes (price drop, availability), it notifies all observers.
    """

    def __init__(self, car_id):
        self.car_id = car_id

    def get_watchers(self):
        # pull all renters watching this car from the database
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id, max_price FROM watched_cars WHERE car_id = ?
        """, (self.car_id,))

        rows = cursor.fetchall()
        conn.close()

        # wrap each row in a WatcherObserver object
        return [WatcherObserver(row["user_id"], row["max_price"]) for row in rows]

    def notify_watchers(self):
        """
        Check all watchers for this car. If a watcher's criteria is met,
        send them an in-app notification through the messages table.
        sender_id = 1 is the system account (no real user, just a convention).
        """
        conn = get_connection()
        cursor = conn.cursor()

        # get the car's current state
        cursor.execute("SELECT * FROM cars WHERE id = ?", (self.car_id,))
        car = cursor.fetchone()

        if not car:
            conn.close()
            return

        car_label = f"{car['year']} {car['make']} {car['model']}"
        watchers = self.get_watchers()

        for watcher in watchers:
            if watcher.should_notify(car["price_per_day"], car["available"]):
                msg = (
                    f"The {car_label} you're watching is now available "
                    f"at ${car['price_per_day']:.2f}/day — within your budget of "
                    f"${watcher.max_price:.2f}/day. Book it before it's gone!"
                )
                cursor.execute("""
                    INSERT INTO messages (sender_id, receiver_id, content)
                    VALUES (1, ?, ?)
                """, (watcher.user_id, msg))

        conn.commit()
        conn.close()


def notify_car_watchers(car_id):
    """
    Convenience function — call this whenever a car's price or
    availability changes to trigger the observer notification chain.
    """
    subject = CarSubject(car_id)
    subject.notify_watchers()