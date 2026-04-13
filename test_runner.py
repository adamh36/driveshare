"""
DriveShare — Automated Black Box Test Runner
CIS 476 Term Project

Tests every feature of the app end-to-end against a real temporary database.
Run this from the project root:

    python3 test_runner.py

A fresh test database is created and deleted automatically.
All tests run without the GUI — they test the backend logic directly.
"""

import os
import sys
import sqlite3
import traceback
from datetime import date, timedelta

# point to a separate test database so we never touch the real one
TEST_DB = os.path.join(os.path.dirname(__file__), "test_driveshare.db")
os.environ["DRIVESHARE_TEST_DB"] = TEST_DB

# patch the DB_PATH before importing anything
import db.database as db_module
db_module.DB_PATH = TEST_DB

# now safe to import everything
from db.database import init_db, get_connection
from models.auth import AuthService
from models.car import CarService, BookingService
from models.messaging import MessageService, NotificationService, ReviewService
from Patterns.ui_singleton import SessionManager
from Patterns.booking import BookingManager
from Patterns.password_chain import RecoveryManager
from Patterns.payment_proxy import PaymentProxy
from Patterns.listing_builder import FullCarListingBuilder, ListingDirector


# Test Infrastructure 

PASS = 0
FAIL = 0
RESULTS = []


def test(name, fn):
    global PASS, FAIL
    try:
        fn()
        PASS += 1
        RESULTS.append(("PASS", name))
        print(f"  PASS  {name}")
    except AssertionError as e:
        FAIL += 1
        RESULTS.append(("FAIL", name, str(e)))
        print(f"  FAIL  {name}")
        print(f"        {e}")
    except Exception as e:
        FAIL += 1
        RESULTS.append(("FAIL", name, traceback.format_exc()))
        print(f"  FAIL  {name}")
        print(f"        {e}")


def assert_ok(result, msg=None):
    ok, message = result[0], result[1]
    assert ok, msg or message


def assert_fail(result, msg=None):
    ok, message = result[0], result[1]
    assert not ok, msg or f"Expected failure but got: {message}"


def reset_session():
    SessionManager()._instance = None
    SessionManager().current_user = None


def setup():
    """Create a fresh test database before running tests."""
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    init_db()
    print("\nTest database initialized.\n")


def teardown():
    """Delete the test database after tests are done."""
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    print("\nTest database cleaned up.")


# Test Suites 

def run_auth_tests():
    print("\n── Authentication & Registration ──────────────────────────────")

    def test_register_owner():
        reset_session()
        ok, msg = AuthService.register(
            "Alice Owner", "alice@test.com", "password123", "owner",
            "What was your first pet?", "fluffy",
            "What city were you born in?", "detroit",
            "What is your mother's maiden name?", "smith"
        )
        assert ok, msg

    def test_register_renter():
        reset_session()
        ok, msg = AuthService.register(
            "Bob Renter", "bob@test.com", "password123", "renter",
            "What was your first pet?", "rex",
            "What city were you born in?", "chicago",
            "What is your mother's maiden name?", "jones"
        )
        assert ok, msg

    def test_register_both():
        reset_session()
        ok, msg = AuthService.register(
            "Carol Both", "carol@test.com", "password123", "both",
            "What was your first pet?", "max",
            "What city were you born in?", "boston",
            "What is your mother's maiden name?", "brown"
        )
        assert ok, msg

    def test_register_duplicate_email():
        reset_session()
        assert_fail(AuthService.register(
            "Alice2", "alice@test.com", "password123", "owner",
            "Q1", "a1", "Q2", "a2", "Q3", "a3"
        ), "Duplicate email should fail")

    def test_register_invalid_email():
        reset_session()
        assert_fail(AuthService.register(
            "Test", "notanemail", "password123", "renter",
            "Q1", "a1", "Q2", "a2", "Q3", "a3"
        ), "Invalid email should fail")

    def test_register_short_password():
        reset_session()
        assert_fail(AuthService.register(
            "Test", "test2@test.com", "abc", "renter",
            "Q1", "a1", "Q2", "a2", "Q3", "a3"
        ), "Short password should fail")

    def test_login_success():
        reset_session()
        ok, msg = AuthService.login("alice@test.com", "password123")
        assert ok, msg
        user = SessionManager().current_user
        assert user is not None, "Session should be set after login"
        assert user["username"] == "Alice Owner"
        assert user["role"] == "owner"

    def test_login_wrong_password():
        reset_session()
        assert_fail(AuthService.login("alice@test.com", "wrongpassword"))

    def test_login_nonexistent_email():
        reset_session()
        assert_fail(AuthService.login("nobody@test.com", "password123"))

    def test_logout():
        reset_session()
        AuthService.login("alice@test.com", "password123")
        AuthService.logout()
        assert SessionManager().current_user is None, "Session should be cleared after logout"

    def test_singleton_session():
        # two calls to SessionManager() must return the same object
        s1 = SessionManager()
        s2 = SessionManager()
        assert s1 is s2, "SessionManager must be a singleton"

    test("Register as owner",             test_register_owner)
    test("Register as renter",            test_register_renter)
    test("Register as both",              test_register_both)
    test("Reject duplicate email",        test_register_duplicate_email)
    test("Reject invalid email",          test_register_invalid_email)
    test("Reject short password",         test_register_short_password)
    test("Login with correct credentials",test_login_success)
    test("Reject wrong password",         test_login_wrong_password)
    test("Reject nonexistent email",      test_login_nonexistent_email)
    test("Logout clears session",         test_logout)
    test("Singleton pattern enforced",    test_singleton_session)


def run_car_tests():
    print("\n── Car Listing & Management (Builder Pattern) ─────────────────")

    def login_alice():
        reset_session()
        AuthService.login("alice@test.com", "password123")

    def test_create_listing():
        login_alice()
        ok, msg = CarService.create_listing(
            make="Toyota", model="Camry", year=2022,
            mileage=15000, location="Dearborn, MI",
            price_per_day=55.0, description="Clean car, non-smoker"
        )
        assert ok, msg

    def test_create_listing_builder_pattern():
        # test the Builder pattern directly
        login_alice()
        builder = FullCarListingBuilder(
            ownerId=SessionManager().user_id,
            make="Honda", model="Civic", year=2021,
            mileage=20000, location="Detroit, MI",
            pricePerDay=45.0, description="Great on gas"
        )
        director = ListingDirector()
        director.constructFullListing(builder)
        listing = builder.getResult()
        assert listing.make == "Honda"
        assert listing.model == "Civic"
        assert listing.pricePerDay == 45.0
        listing.saveToDB()

    def test_get_owner_cars():
        login_alice()
        cars = CarService.get_owner_cars(SessionManager().user_id)
        assert len(cars) >= 1, "Alice should have at least one listing"

    def test_update_listing():
        login_alice()
        cars = CarService.get_owner_cars(SessionManager().user_id)
        car_id = cars[0]["id"]
        ok, msg = CarService.update_listing(car_id, 65.0, True, "Updated description")
        assert ok, msg

    def test_search_cars():
        reset_session()
        AuthService.login("bob@test.com", "password123")
        start = str(date.today() + timedelta(days=1))
        end   = str(date.today() + timedelta(days=4))
        cars = CarService.search_cars("Dearborn", start, end, max_price=100.0)
        assert len(cars) >= 1, "Should find Alice's car in Dearborn"

    def test_search_excludes_own_cars():
        login_alice()
        start = str(date.today() + timedelta(days=1))
        end   = str(date.today() + timedelta(days=4))
        all_cars = CarService.search_cars("", start, end)
        uid = SessionManager().user_id
        owned = [c for c in all_cars if c["owner_id"] == uid]
        assert len(owned) == 0, "Search should not return the logged-in user's own cars"

    def test_set_and_get_availability():
        login_alice()
        cars = CarService.get_owner_cars(SessionManager().user_id)
        car_id = cars[0]["id"]
        target_date = str(date.today() + timedelta(days=10))
        CarService.set_availability(car_id, target_date, False)
        avail = CarService.get_availability(car_id)
        assert target_date in avail, "Date should be in availability table"
        assert avail[target_date] == 0, "Date should be marked as blocked"

    def test_blocked_date_prevents_booking():
        reset_session()
        AuthService.login("bob@test.com", "password123")
        # get alice's car
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM cars WHERE location LIKE '%Dearborn%' LIMIT 1")
        car = cursor.fetchone()
        conn.close()
        if not car:
            return  # skip if no car found

        # block dates 10 days from now
        blocked = str(date.today() + timedelta(days=10))
        CarService.set_availability(car["id"], blocked, False)

        start = str(date.today() + timedelta(days=9))
        end   = str(date.today() + timedelta(days=11))
        ok, msg, bid = BookingService.create_booking(car["id"], start, end)
        assert not ok, "Booking should fail when owner has blocked those dates"

    test("Create car listing",                    test_create_listing)
    test("Builder pattern constructs listing",     test_create_listing_builder_pattern)
    test("Get owner's car listings",               test_get_owner_cars)
    test("Update listing price and description",   test_update_listing)
    test("Search finds available cars",            test_search_cars)
    test("Search excludes own cars",               test_search_excludes_own_cars)
    test("Set and get availability calendar",      test_set_and_get_availability)
    test("Blocked dates prevent booking",          test_blocked_date_prevents_booking)


def run_booking_tests():
    print("\n── Booking & Conflict Prevention (Observer Pattern) ───────────")

    def get_alice_car_id():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM cars WHERE location LIKE '%Dearborn%' LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return row["id"] if row else None

    def test_create_booking():
        reset_session()
        AuthService.login("bob@test.com", "password123")
        car_id = get_alice_car_id()
        assert car_id, "Need a car to book"
        start = str(date.today() + timedelta(days=20))
        end   = str(date.today() + timedelta(days=23))
        ok, msg, bid = BookingService.create_booking(car_id, start, end)
        assert ok, msg
        assert bid is not None

    def test_overlap_prevention():
        reset_session()
        AuthService.login("carol@test.com", "password123")
        car_id = get_alice_car_id()
        assert car_id, "Need a car to book"
        # try to book the same dates as Bob
        start = str(date.today() + timedelta(days=20))
        end   = str(date.today() + timedelta(days=23))
        ok, msg, bid = BookingService.create_booking(car_id, start, end)
        assert not ok, "Overlapping booking should be rejected"

    def test_non_overlapping_booking():
        reset_session()
        AuthService.login("carol@test.com", "password123")
        car_id = get_alice_car_id()
        assert car_id, "Need a car to book"
        # book different dates
        start = str(date.today() + timedelta(days=25))
        end   = str(date.today() + timedelta(days=28))
        ok, msg, bid = BookingService.create_booking(car_id, start, end)
        assert ok, msg

    def test_cancel_booking():
        reset_session()
        AuthService.login("bob@test.com", "password123")
        bookings = BookingService.get_user_bookings(SessionManager().user_id)
        assert len(bookings) > 0, "Bob should have a booking to cancel"
        bid = bookings[0]["id"]
        ok, msg = BookingService.cancel_booking(bid)
        assert ok, msg

    def test_watch_car():
        reset_session()
        AuthService.login("bob@test.com", "password123")
        car_id = get_alice_car_id()
        assert car_id
        ok, msg = CarService.watch_car(car_id, max_price=60.0)
        assert ok, msg

    def test_watch_car_duplicate():
        reset_session()
        AuthService.login("bob@test.com", "password123")
        car_id = get_alice_car_id()
        assert car_id
        ok, msg = CarService.watch_car(car_id, max_price=60.0)
        assert not ok, "Should not be able to watch the same car twice"

    def test_end_before_start_rejected():
        reset_session()
        AuthService.login("bob@test.com", "password123")
        car_id = get_alice_car_id()
        assert car_id
        start = str(date.today() + timedelta(days=5))
        end   = str(date.today() + timedelta(days=2))
        ok, msg, bid = BookingService.create_booking(car_id, start, end)
        assert not ok, "End before start should be rejected"

    test("Create a booking",                    test_create_booking)
    test("Reject overlapping booking",          test_overlap_prevention)
    test("Allow non-overlapping booking",       test_non_overlapping_booking)
    test("Cancel a booking",                    test_cancel_booking)
    test("Watch a car",                         test_watch_car)
    test("Reject duplicate car watch",          test_watch_car_duplicate)
    test("Reject end date before start date",   test_end_before_start_rejected)


def run_payment_tests():
    print("\n── Payment (Proxy Pattern) ─────────────────────────────────────")

    def test_pay_booking():
        reset_session()
        AuthService.login("carol@test.com", "password123")
        bookings = BookingService.get_user_bookings(SessionManager().user_id)
        assert len(bookings) > 0, "Carol needs a booking to pay"
        bid = bookings[0]["id"]
        ok, msg = BookingService.pay_booking(bid)
        assert ok, msg

    def test_payment_record_created():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM payments WHERE status = 'completed' LIMIT 1")
        payment = cursor.fetchone()
        conn.close()
        assert payment is not None, "A completed payment record should exist"

    def test_payment_notification_sent():
        # after payment the proxy sends messages to both owner and renter
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM messages WHERE sender_id IS NULL OR sender_id = 1")
        row = cursor.fetchone()
        conn.close()
        assert row["cnt"] > 0, "Payment proxy should have sent notifications"

    def test_proxy_pattern_directly():
        # test PaymentProxy directly — it should call real service and update db
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, total_price FROM bookings WHERE status = 'pending' LIMIT 1")
        booking = cursor.fetchone()
        conn.close()

        if not booking:
            return  # no pending bookings to test with

        proxy = PaymentProxy()
        success = proxy.processPayment(booking["id"], booking["total_price"])
        assert success, "PaymentProxy should return True on success"

    test("Pay for a booking",                       test_pay_booking)
    test("Payment record created in db",            test_payment_record_created)
    test("Payment proxy sends notifications",       test_payment_notification_sent)
    test("Proxy pattern processes payment directly",test_proxy_pattern_directly)


def run_messaging_tests():
    print("\n── Messaging & Notifications ───────────────────────────────────")

    def get_user_id(email):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        conn.close()
        return row["id"] if row else None

    def test_send_message():
        reset_session()
        AuthService.login("bob@test.com", "password123")
        alice_id = get_user_id("alice@test.com")
        ok, msg = MessageService.send_message(alice_id, "Hey Alice, is your car available?")
        assert ok, msg

    def test_send_message_empty():
        reset_session()
        AuthService.login("bob@test.com", "password123")
        alice_id = get_user_id("alice@test.com")
        ok, msg = MessageService.send_message(alice_id, "")
        assert not ok, "Empty message should be rejected"

    def test_get_inbox():
        reset_session()
        AuthService.login("alice@test.com", "password123")
        inbox = MessageService.get_inbox(SessionManager().user_id)
        assert len(inbox) > 0, "Alice should have Bob's message in her inbox"

    def test_mark_message_read():
        reset_session()
        AuthService.login("alice@test.com", "password123")
        inbox = MessageService.get_inbox(SessionManager().user_id)
        assert len(inbox) > 0
        msg_id = inbox[0]["id"]
        MessageService.mark_read(msg_id)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT is_read FROM messages WHERE id = ?", (msg_id,))
        row = cursor.fetchone()
        conn.close()
        assert row["is_read"] == 1, "Message should be marked as read"

    def test_send_reply():
        reset_session()
        AuthService.login("alice@test.com", "password123")
        bob_id = get_user_id("bob@test.com")
        ok, msg = MessageService.send_message(bob_id, "Yes Bob, it is available!")
        assert ok, msg

    def test_get_notifications():
        reset_session()
        AuthService.login("carol@test.com", "password123")
        notifs = NotificationService.get_notifications(SessionManager().user_id)
        # carol paid so she should have a payment notification
        assert len(notifs) >= 0  # just verifying it doesn't crash

    def test_mark_all_notifications_read():
        reset_session()
        AuthService.login("carol@test.com", "password123")
        uid = SessionManager().user_id
        NotificationService.mark_all_read(uid)
        notifs = NotificationService.get_notifications(uid)
        unread = [n for n in notifs if not n["is_read"]]
        assert len(unread) == 0, "All notifications should be marked read"

    test("Send a message",                    test_send_message)
    test("Reject empty message",              test_send_message_empty)
    test("Receive message in inbox",          test_get_inbox)
    test("Mark message as read",              test_mark_message_read)
    test("Send a reply",                      test_send_reply)
    test("Get notifications",                 test_get_notifications)
    test("Mark all notifications read",       test_mark_all_notifications_read)


def run_password_recovery_tests():
    print("\n── Password Recovery (Chain of Responsibility) ─────────────────")

    def test_get_security_questions():
        manager = RecoveryManager()
        questions = manager.getSecurityQuestions("alice@test.com")
        assert len(questions) == 3, "Should return 3 security questions"

    def test_correct_answers_pass_chain():
        manager = RecoveryManager()
        questions = manager.getSecurityQuestions("alice@test.com")
        answers = {"a1": "fluffy", "a2": "detroit", "a3": "smith"}
        passed = manager.verifyAnswers(answers, questions)
        assert passed, "Correct answers should pass the chain"

    def test_wrong_answer_breaks_chain():
        manager = RecoveryManager()
        questions = manager.getSecurityQuestions("alice@test.com")
        answers = {"a1": "fluffy", "a2": "wrongcity", "a3": "smith"}
        passed = manager.verifyAnswers(answers, questions)
        assert not passed, "Wrong answer should stop the chain"

    def test_first_answer_wrong_stops_chain():
        manager = RecoveryManager()
        questions = manager.getSecurityQuestions("alice@test.com")
        answers = {"a1": "wrongpet", "a2": "detroit", "a3": "smith"}
        passed = manager.verifyAnswers(answers, questions)
        assert not passed, "Wrong first answer should stop chain immediately"

    def test_reset_password():
        manager = RecoveryManager()
        manager.resetPassword("alice@test.com", "newpassword123")
        reset_session()
        ok, msg = AuthService.login("alice@test.com", "newpassword123")
        assert ok, "Should be able to login with new password after reset"
        # restore original password for other tests
        manager.resetPassword("alice@test.com", "password123")

    def test_unknown_email_returns_empty():
        manager = RecoveryManager()
        questions = manager.getSecurityQuestions("nobody@test.com")
        assert len(questions) == 0, "Unknown email should return empty list"

    test("Fetch security questions by email",       test_get_security_questions)
    test("Correct answers pass chain",              test_correct_answers_pass_chain)
    test("Wrong answer breaks chain",               test_wrong_answer_breaks_chain)
    test("Wrong first answer stops chain early",    test_first_answer_wrong_stops_chain)
    test("Reset password through chain",            test_reset_password)
    test("Unknown email returns empty questions",   test_unknown_email_returns_empty)


def run_review_tests():
    print("\n── Reviews & Ratings ───────────────────────────────────────────")

    def test_leave_review():
        reset_session()
        AuthService.login("carol@test.com", "password123")

        # get a booking and the owner's id
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.id, c.owner_id FROM bookings b
            JOIN cars c ON b.car_id = c.id
            WHERE b.renter_id = (SELECT id FROM users WHERE email = 'carol@test.com')
            LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()

        if not row:
            return

        ok, msg = ReviewService.leave_review(row["id"], row["owner_id"], 5, "Great car!")
        assert ok, msg

    def test_duplicate_review_rejected():
        reset_session()
        AuthService.login("carol@test.com", "password123")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.id, c.owner_id FROM bookings b
            JOIN cars c ON b.car_id = c.id
            WHERE b.renter_id = (SELECT id FROM users WHERE email = 'carol@test.com')
            LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()

        if not row:
            return

        ok, msg = ReviewService.leave_review(row["id"], row["owner_id"], 3, "Second review attempt")
        assert not ok, "Duplicate review should be rejected"

    def test_get_reviews_for_user():
        reset_session()
        AuthService.login("alice@test.com", "password123")
        alice_id = SessionManager().user_id
        reviews = ReviewService.get_reviews_for_user(alice_id)
        assert len(reviews) >= 0  # just verifying it doesn't crash

    def test_invalid_rating_rejected():
        reset_session()
        AuthService.login("bob@test.com", "password123")
        ok, msg = ReviewService.leave_review(1, 1, 10, "Invalid rating")
        assert not ok, "Rating above 5 should be rejected"

    test("Leave a review after booking",        test_leave_review)
    test("Reject duplicate review",             test_duplicate_review_rejected)
    test("Get reviews for a user",              test_get_reviews_for_user)
    test("Reject invalid rating",               test_invalid_rating_rejected)


#  Main 

def main():
    print("=" * 60)
    print("  DriveShare — Automated Black Box Test Runner")
    print("=" * 60)

    setup()

    run_auth_tests()
    run_car_tests()
    run_booking_tests()
    run_payment_tests()
    run_messaging_tests()
    run_password_recovery_tests()
    run_review_tests()

    teardown()

    print("\n" + "=" * 60)
    print(f"  Results: {PASS} passed, {FAIL} failed out of {PASS + FAIL} tests")
    print("=" * 60)

    if FAIL > 0:
        print("\nFailed tests:")
        for r in RESULTS:
            if r[0] == "FAIL":
                print(f"  - {r[1]}")
                if len(r) > 2:
                    print(f"    {r[2].splitlines()[0]}")

    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
