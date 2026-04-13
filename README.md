# DriveShare — Peer-to-Peer Car Rental Platform

A desktop car rental app built with Python and Tkinter, inspired by Turo. Car owners can list vehicles and set availability, renters can search, book, and pay. Built for CIS 476 at University of Michigan-Dearborn.

## Features
- Role-based registration (Owner / Renter / Both)
- Car listings with availability calendar
- Search, book, and pay for rentals
- In-app messaging between owners and renters
- Password recovery via security questions
- Booking conflict prevention
- Reviews and rental history

## Design Patterns Used
Singleton, Observer, Mediator, Builder, Proxy, Chain of Responsibility

## Setup

# 1. Clone the repo
git clone https://github.com/adamh36/driveshare.git
cd driveshare

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python3 app.py
\```

## Stack
Python 3.11 · Tkinter · SQLite · bcrypt · tkcalendar

## Team
Adam Hammoud · Karim Jomaa · Era Shkembi
