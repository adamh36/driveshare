"""
models/car.py
CIS 476 Term Project: DriveShare

CarService handles car listing operations.
BookingService handles booking creation, payment, and cancellation.
"""

from db.database import get_connection
from Patterns.ui_singleton import SessionManager
from Patterns.listing_builder import FullCarListingBuilder, ListingDirector
from Patterns.payment_proxy import PaymentProxy
from Patterns.booking import BookingManager


class CarService:

    @staticmethod
    def search_cars(location, start_date, end_date, max_price=0.0):
        conn = get_connection()
        cursor = conn.cursor()

        price_filter = max_price if max_price and max_price > 0 else 999999

        cursor.execute("""
            SELECT c.*, u.name AS owner_name
            FROM cars c
            JOIN users u ON c.owner_id = u.id
            WHERE c.available = 1
            AND c.price_per_day <= ?
            AND (? = '' OR c.location LIKE ?)
            AND c.id NOT IN (
                SELECT car_id FROM bookings
                WHERE status NOT IN ('cancelled')
                AND start_date < ?
                AND end_date > ?
            )
        """, (price_filter, location, f"%{location}%", end_date, start_date))

        cars = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return cars

    @staticmethod
    def create_listing(make, model, year, mileage, location, price_per_day, description=None):
        user_id = SessionManager().user_id
        if not user_id:
            return False, "You must be logged in to list a car."

        if not all([make, model, year, mileage, location, price_per_day]):
            return False, "Please fill in all required fields."

        try:
            # Builder pattern: construct the listing step by step
            builder = FullCarListingBuilder(
                ownerId=user_id,
                make=make,
                model=model,
                year=int(year),
                mileage=int(mileage),
                location=location,
                pricePerDay=float(price_per_day),
                description=description
            )
            director = ListingDirector()
            director.constructFullListing(builder)
            builder.getResult().saveToDB()
            return True, f"{year} {make} {model} listed successfully."

        except Exception as e:
            return False, f"Failed to create listing: {e}"

    @staticmethod
    def get_owner_cars(user_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM cars WHERE owner_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        cars = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return cars

    @staticmethod
    def update_listing(car_id, price, available, description):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE cars SET price_per_day = ?, available = ?, description = ?
            WHERE id = ?
        """, (price, 1 if available else 0, description, car_id))
        conn.commit()
        conn.close()
        return True, "Listing updated."

    @staticmethod
    def watch_car(car_id, max_price=0.0):
        user_id = SessionManager().user_id
        if not user_id:
            return False, "You must be logged in to watch a car."

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM watched_cars WHERE user_id = ? AND car_id = ?",
            (user_id, car_id)
        )
        if cursor.fetchone():
            conn.close()
            return False, "You are already watching this car."

        cursor.execute(
            "INSERT INTO watched_cars (user_id, car_id, max_price) VALUES (?, ?, ?)",
            (user_id, car_id, max_price if max_price > 0 else 999999)
        )
        conn.commit()
        conn.close()
        return True, "You are now watching this car."


class BookingService:

    @staticmethod
    def create_booking(car_id, start_date, end_date):
        user_id = SessionManager().user_id
        if not user_id:
            return False, "You must be logged in.", None

        # use BookingManager which has the conflict prevention logic
        manager = BookingManager()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT price_per_day FROM cars WHERE id = ?", (car_id,))
        car = cursor.fetchone()
        conn.close()

        if not car:
            return False, "Car not found.", None

        from datetime import datetime
        try:
            days = (datetime.strptime(end_date, "%Y-%m-%d") -
                    datetime.strptime(start_date, "%Y-%m-%d")).days
        except ValueError:
            return False, "Invalid date format. Use YYYY-MM-DD.", None

        if days <= 0:
            return False, "End date must be after start date.", None

        total = days * car["price_per_day"]

        success = manager.createBooking(
            carId=car_id,
            renterId=user_id,
            startDate=start_date,
            endDate=end_date,
            totalPrice=total
        )

        if not success:
            return False, "This car is already booked for those dates.", None

        # get the booking id just created
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM bookings
            WHERE car_id = ? AND renter_id = ? AND start_date = ? AND end_date = ?
            ORDER BY created_at DESC LIMIT 1
        """, (car_id, user_id, start_date, end_date))
        booking = cursor.fetchone()
        conn.close()

        return True, f"Booking created for {days} day(s). Total: ${total:.2f}", booking["id"]

    @staticmethod
    def pay_booking(booking_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
        booking = cursor.fetchone()
        conn.close()

        if not booking:
            return False, "Booking not found."

        # Proxy pattern handles payment and sends notifications
        proxy = PaymentProxy()
        success = proxy.processPayment(booking_id, booking["total_price"])

        if success:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE bookings SET status = 'confirmed' WHERE id = ?",
                (booking_id,)
            )
            conn.commit()
            conn.close()
            return True, f"Payment of ${booking['total_price']:.2f} processed."

        return False, "Payment failed. Please try again."

    @staticmethod
    def cancel_booking(booking_id):
        manager = BookingManager()
        success = manager.cancelBooking(booking_id)
        if success:
            return True, "Booking cancelled."
        return False, "Booking not found."

    @staticmethod
    def get_user_bookings(user_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.*, c.make, c.model, c.year, c.location
            FROM bookings b
            JOIN cars c ON b.car_id = c.id
            WHERE b.renter_id = ?
            ORDER BY b.created_at DESC
        """, (user_id,))
        bookings = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return bookings