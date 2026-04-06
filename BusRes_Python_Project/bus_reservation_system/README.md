# 🚌 BusRes — Bus Reservation System

> A production-style, console-based Bus Reservation System built in Python.
> Designed to simulate real-world bus booking platforms with full CRUD, booking,
> cancellation, revenue reporting, admin management, promo codes, loyalty points,
> and more.

---

## 📌 Project Overview

**BusRes** is a complete terminal application that manages the end-to-end lifecycle
of bus reservations — from route creation and scheduling to seat booking, ticket
generation, cancellation, and financial reporting.

This project demonstrates strong Python OOP design, modular architecture,
file-based persistence (JSON), input validation, and a professional console UX.

---

## 🌟 Key Features

### Passenger Features
- 🔍 **Search buses** by source, destination, date, bus type, and max fare
- 💺 **Interactive seat layout** with visual grid showing available/booked seats
- 🎫 **Seat booking** with co-passenger details, boarding/dropping point selection
- 🎟️ **Ticket generation** — formatted ticket printed to console
- ❌ **Cancellation** with tiered refund rules (5%–100% charge based on timing)
- 🎁 **Promo codes** — apply discount coupons at checkout
- 🏆 **Loyalty points** — earn and redeem points per booking
- 📋 **Booking history** and profile management
- ⏳ **Waitlist** support when buses are fully booked
- ⭐ **Trip feedback** and bus ratings

### Admin Features
- 🔐 **Secure admin login** with SHA-256 password hashing and account lockout
- 🚌 **Bus management** — add, update, deactivate buses
- 🗺️ **Route management** — create routes with intermediate stops
- 📅 **Schedule management** — single and recurring schedules, conflict detection
- 📊 **Revenue reports** — daily, weekly, monthly, all-time
- 📈 **Analytics** — route-wise revenue, bus-wise revenue, occupancy rates
- 🎟️ **Promo code management** — create, list, deactivate codes
- 🔍 **Audit log** — all admin actions tracked
- 💾 **Backup & restore** — timestamped data backups
- 📤 **Export reports** to text file

---

## 🗂️ Folder Structure

```
bus_reservation_system/
│
├── main.py                  # Entry point, main menu
├── models.py                # All data classes (Bus, Route, Booking, etc.)
├── storage.py               # JSON file persistence layer
├── utils.py                 # Console formatting, input validation, helpers
│
├── bus_manager.py           # Bus CRUD operations
├── route_manager.py         # Route management
├── schedule_manager.py      # Schedule management + conflict detection
├── booking_manager.py       # Full booking workflow + ticket generation
├── cancellation_manager.py  # Cancellation + refund calculation
├── report_manager.py        # Revenue and analytics reports
├── passenger.py             # Passenger registration + profile
├── admin.py                 # Admin auth + promo codes + audit log
├── feedback.py              # Post-trip ratings
├── seed_data.py             # Sample data loader
│
└── data/                    # Auto-created on first run
    ├── buses.json
    ├── routes.json
    ├── schedules.json
    ├── passengers.json
    ├── bookings.json
    ├── cancellations.json
    ├── promo_codes.json
    ├── feedback.json
    ├── audit_logs.json
    └── admins.json
```

---

## ▶️ How to Run

### Requirements
- Python 3.7+
- No external libraries required (uses only stdlib)

### Steps

```bash
# Clone or download the project
cd bus_reservation_system

# Run the application
python main.py
```

On first run, sample buses, routes, schedules, and promo codes are automatically loaded.

### Default Admin Credentials
```
Username : admin
Password : admin123
```
> ⚠️ Change the password after first login via Admin → Change Password.

---

## 🚀 Demo Flow

### Book a Ticket
1. Select **1. Passenger / User** → **2. Book a Ticket**
2. Register or login with your phone number
3. Enter: `Chennai` → `Bengaluru`, date = tomorrow
4. Select a bus from results
5. View the seat map → pick seats
6. Apply promo code: `WELCOME10` (10% off)
7. Confirm → ticket printed

### Cancel a Booking
1. **5. Cancel a Booking** → enter Ticket ID or phone number
2. See the refund calculation
3. Confirm cancellation

### Check Availability
1. **3. Check Seat Availability**
2. Enter route and date → visual occupancy bar shown

### Revenue Report (Admin)
1. Login as admin → **7. Revenue Reports** → **Today's Revenue**

---

## 🏷️ Sample Promo Codes

| Code       | Discount | Max Off | Min Fare |
|------------|----------|---------|----------|
| WELCOME10  | 10%      | ₹100    | None     |
| SAVE20     | 20%      | ₹200    | ₹500     |
| FLAT50     | 5%       | ₹50     | ₹200     |
| LUXURY30   | 30%      | ₹500    | ₹1000    |

---

## 📐 Cancellation Policy

| Days Before Journey | Cancellation Charge |
|---------------------|---------------------|
| Same day (0 days)   | 100% (no refund)    |
| 1 day               | 50%                 |
| 2-3 days            | 25%                 |
| 4-7 days            | 10%                 |
| 8+ days             | 5%                  |

---

## 🏗️ OOP Design

| Class           | Responsibility                        |
|-----------------|---------------------------------------|
| `Bus`           | Bus properties, ratings               |
| `Route`         | Source/destination/stops/fare         |
| `Schedule`      | Bus on route on date/time             |
| `Passenger`     | Profile, history, loyalty points      |
| `Booking`       | Seat reservation record               |
| `Cancellation`  | Refund and charge record              |
| `PromoCode`     | Discount coupon with validation       |
| `Feedback`      | Post-trip rating                      |
| `AuditLog`      | Admin action tracking                 |

---

## 🔮 Future Scope (Version 2)

- [ ] SQLite backend for better query performance
- [ ] Email/SMS notification integration
- [ ] Multi-admin roles (operator vs superadmin)
- [ ] Online payment gateway simulation
- [ ] Boarding pass QR code (ASCII art)
- [ ] Multi-language support (Hindi, Tamil, Telugu)
- [ ] Seat preference tagging (window/aisle/lower/upper)
- [ ] Dynamic pricing engine (demand-based fare)
- [ ] REST API layer (FastAPI) for mobile app integration
- [ ] Curses-based TUI for better navigation

---

## 📌 Assumptions

1. A "journey date" is the date the bus departs (not arrives).
2. Fare = `route.base_fare × schedule.fare_multiplier`
3. Loyalty points are 10 per seat booked; 1 point = ₹0.50 off.
4. Seats are numbered 1–N (no alphabetic row/column encoding).
5. Cancellation refund is deposited outside the system (bank transfer).

---

## 👨‍💻 Built With

- **Python 3.7+** — core language
- **JSON** — lightweight persistence
- **hashlib** — password hashing (SHA-256)
- **uuid** — unique ID generation
- **datetime** — date/time calculations
- **Standard Library only** — no pip install needed

---

*BusRes v1.0 — A Python Portfolio Project*
