"""
SEARCH PAGE

This is the renter's search page: where they can look for available cars
based on location, date range, and max price.
It also lets them watch a car, which hooks into the Observer pattern in booking.py
"""

import streamlit as st
from db.database import get_connection
from Patterns.session import session
# Booking Folder
from Patterns.booking import BookingManager

# make sure the user is logged in before they can search
# if not, kick them back to register :)
if not session.is_logged_in():
    st.switch_page("pages/register.py")

user = session.get_user()

st.title("Search for a Car")

# search filters: renter fills these in to narrow down results
location = st.text_input("Location (city, state)")
startDate = st.date_input("Start Date")
endDate = st.date_input("End Date")
maxPrice = st.number_input("Max Price Per Day ($)", min_value=0.0, value=200.0, step=5.0)

# hitting search triggers the query below
if st.button("Search"):

    # make sure dates actually make sense before querying
    if startDate >= endDate:
        st.error("End date must be after start date.")
    else:
        conn = get_connection()
        cursor = conn.cursor()

        # grab all cars that:
        # 1. match the location (partial match so "Dearborn" matches "Dearborn, MI")
        # 2. are within the price range
        # 3. are marked as available
        # 4. don't have a confirmed/pending booking that overlaps with the requested dates
        # that last check is the conflict prevention: same logic as in booking.py
        cursor.execute("""
            SELECT c.*, u.name AS ownerName
            FROM cars c
            JOIN users u ON c.owner_id = u.id
            WHERE c.location LIKE ?
            AND c.price_per_day <= ?
            AND c.available = 1
            AND c.id NOT IN (
                SELECT car_id FROM bookings
                WHERE status NOT IN ('cancelled')
                AND start_date < ?
                AND end_date > ?
            )
        """, (
            f"%{location}%",
            maxPrice,
            str(endDate),
            str(startDate)
        ))

        results = cursor.fetchall()
        conn.close()

        # show results or tell the renter nothing matched
        if not results:
            st.warning("No cars found matching your search.")
        else:
            st.success(f"{len(results)} car(s) found!")

            # loop through each result and show a card for it
            for car in results:
                # each car gets its own little expandable section
                with st.expander(f"{car['year']} {car['make']} {car['model']}: ${car['price_per_day']}/day"):

                    st.write(f"Location: {car['location']}")
                    st.write(f"Mileage: {car['mileage']} miles")
                    st.write(f"Owner: {car['ownerName']}")

                    if car['description']:
                        st.write(f"Notes: {car['description']}")

                    # calculate total price based on number of days
                    numDays = (endDate - startDate).days
                    totalPrice = numDays * car['price_per_day']
                    st.write(f"Total for {numDays} day(s): ${totalPrice:.2f}")

                    # two actions the renter can take: book it or watch it
                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("Book", key=f"book_{car['id']}"):
                            manager = BookingManager()
                            success = manager.createBooking(
                                carId=car['id'],
                                renterId=user['id'],
                                startDate=str(startDate),
                                endDate=str(endDate),
                                totalPrice=totalPrice
                            )

                            if success:
                                st.success("Booking created successfully!")
                            else:
                                # this happens if someone else booked it between search and click
                                st.error("This car is no longer available for those dates.")

                    with col2:
                        # watch button: hooks into the observer pattern
                        # renter gets added to this car's observer list
                        watchPrice = st.number_input(
                            "Notify me if price drops below ($)",
                            min_value=0.0,
                            value=float(car['price_per_day']),
                            step=5.0,
                            key=f"watchprice_{car['id']}"
                        )

                        if st.button("Watch Car", key=f"watch_{car['id']}"):
                            manager = BookingManager()
                            manager.watchCar(
                                carId=car['id'],
                                renterId=user['id'],
                                renterEmail=user['email'],
                                maxPrice=watchPrice
                            )
                            st.success("You are now watching this car!")