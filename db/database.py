import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "driveshare.db")


def get_connection():
    # Return a connection to SQLite database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # allows us to access columns by name instead of index
    return conn


def init_db():
    # Creates all tables if they don't exist yet
    conn = get_connection()
    cursor = conn.cursor()

    # Users table - stores everyone who signs up
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email       TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            name        TEXT NOT NULL,
            role        TEXT NOT NULL CHECK(role IN ('owner', 'renter', 'both')),
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)

    # Security questions table - 3 questions per user for password recovery
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS security_questions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            question    TEXT NOT NULL,
            answer      TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Cars table - every vehicle listed on the platform
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cars (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id      INTEGER NOT NULL,
            make          TEXT NOT NULL,
            model         TEXT NOT NULL,
            year          INTEGER NOT NULL,
            mileage       INTEGER NOT NULL,
            location      TEXT NOT NULL,
            price_per_day REAL NOT NULL,
            description   TEXT,
            available     INTEGER DEFAULT 1,
            created_at    TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (owner_id) REFERENCES users(id)
        )
    """)

    # Availability table - owner marks specific dates as available or blocked
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS availability (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            car_id       INTEGER NOT NULL,
            date         TEXT NOT NULL,
            is_available INTEGER DEFAULT 1,
            FOREIGN KEY (car_id) REFERENCES cars(id),
            UNIQUE(car_id, date)
        )
    """)

    # Bookings table - a renter reserving a car for a date range
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            car_id      INTEGER NOT NULL,
            renter_id   INTEGER NOT NULL,
            start_date  TEXT NOT NULL,
            end_date    TEXT NOT NULL,
            status      TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'confirmed', 'cancelled', 'completed')),
            total_price REAL NOT NULL,
            created_at  TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (car_id) REFERENCES cars(id),
            FOREIGN KEY (renter_id) REFERENCES users(id)
        )
    """)

    # Messages table - direct chat between users, also used for system notifications
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id   INTEGER,
            receiver_id INTEGER NOT NULL,
            content     TEXT NOT NULL,
            is_read     INTEGER DEFAULT 0,
            created_at  TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (receiver_id) REFERENCES users(id)
        )
    """)

    # Watched cars table - renter watches a car to get notified on price/availability changes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watched_cars (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            car_id     INTEGER NOT NULL,
            max_price  REAL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (car_id) REFERENCES cars(id)
        )
    """)

    # Reviews table - left after a booking, works both ways
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id  INTEGER NOT NULL,
            reviewer_id INTEGER NOT NULL,
            reviewee_id INTEGER NOT NULL,
            rating      INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            comment     TEXT,
            created_at  TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (booking_id) REFERENCES bookings(id),
            FOREIGN KEY (reviewer_id) REFERENCES users(id),
            FOREIGN KEY (reviewee_id) REFERENCES users(id)
        )
    """)

    # Payments table - tracks payment status for each booking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            amount     REAL NOT NULL,
            status     TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'completed', 'failed')),
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (booking_id) REFERENCES bookings(id)
        )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")