"""
passenger.py
------------
Passenger registration, lookup, booking history, and loyalty points.
"""

from models import Passenger, generate_id
from utils import (
    print_header, print_subheader, print_success, print_error,
    print_table, get_input, get_int_input,
    get_menu_choice, confirm, press_enter, now_str,
    get_valid_phone, get_valid_email, format_date, format_datetime,
    select_from_list, truncate, format_currency
)
import storage


# ─────────────────────────────────────────────────────────────────────────────
# CRUD OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────

def register_passenger() -> Passenger:
    """Register a new passenger interactively."""
    print_header("PASSENGER REGISTRATION")

    name   = get_input("Full Name")
    phone  = get_valid_phone()

    # Check duplicate phone
    existing = storage.load("passengers")
    if any(p["phone"] == phone for p in existing):
        print_error("A passenger with this phone number already exists.")
        p = find_by_phone(phone)
        if p:
            print_success(f"Found existing: {p.name}  (ID: {p.passenger_id})")
        press_enter()
        return None

    email  = get_valid_email()
    age    = get_int_input("Age", min_val=1, max_val=120)

    print("\n  Gender:")
    print("  1. Male  2. Female  3. Other")
    g = get_int_input("Choice", 1, 3)
    gender = ["Male", "Female", "Other"][g - 1]

    id_proof = input("  ID Proof Number (optional, press Enter to skip): ").strip()

    passenger = Passenger(
        passenger_id    = generate_id("PAX"),
        name            = name,
        age             = age,
        gender          = gender,
        phone           = phone,
        email           = email,
        id_proof        = id_proof,
        loyalty_points  = 0,
        booking_history = [],
        created_at      = now_str()
    )

    storage.upsert("passengers", "passenger_id", passenger.to_dict())
    print_success(f"Registered! Your Passenger ID: {passenger.passenger_id}")
    press_enter()
    return passenger


def find_by_phone(phone: str) -> Passenger:
    """Look up a passenger by phone number."""
    records = storage.load("passengers")
    for r in records:
        if r["phone"] == phone:
            return Passenger.from_dict(r)
    return None


def find_by_id(passenger_id: str) -> Passenger:
    record = storage.find_by_id("passengers", "passenger_id", passenger_id)
    return Passenger.from_dict(record) if record else None


def get_or_create_passenger() -> Passenger:
    """
    Ask user for phone number; if found return existing passenger,
    otherwise offer to register.
    """
    print_subheader("PASSENGER IDENTIFICATION")
    phone = get_valid_phone("Your Phone Number")
    passenger = find_by_phone(phone)
    if passenger:
        print_success(f"Welcome back, {passenger.name}!  (Loyalty Points: {passenger.loyalty_points})")
        press_enter()
        return passenger
    else:
        print_error("No account found with this phone number.")
        if confirm("Register as a new passenger?"):
            # Pre-fill phone
            print_header("PASSENGER REGISTRATION")
            name   = get_input("Full Name")
            email  = get_valid_email()
            age    = get_int_input("Age", min_val=1, max_val=120)
            print("\n  Gender: 1. Male  2. Female  3. Other")
            g      = get_int_input("Choice", 1, 3)
            gender = ["Male", "Female", "Other"][g - 1]
            id_proof = input("  ID Proof Number (optional): ").strip()

            passenger = Passenger(
                passenger_id    = generate_id("PAX"),
                name            = name,
                age             = age,
                gender          = gender,
                phone           = phone,
                email           = email,
                id_proof        = id_proof,
                loyalty_points  = 0,
                booking_history = [],
                created_at      = now_str()
            )
            storage.upsert("passengers", "passenger_id", passenger.to_dict())
            print_success(f"Registered! Your Passenger ID: {passenger.passenger_id}")
            press_enter()
            return passenger
    return None


def view_profile(passenger: Passenger):
    """Display full passenger profile."""
    print_header("MY PROFILE")
    print(f"  Name         : {passenger.name}")
    print(f"  Passenger ID : {passenger.passenger_id}")
    print(f"  Phone        : {passenger.phone}")
    print(f"  Email        : {passenger.email}")
    print(f"  Age / Gender : {passenger.age} / {passenger.gender}")
    print(f"  Loyalty Pts  : {passenger.loyalty_points} pts")
    if passenger.id_proof:
        print(f"  ID Proof     : {passenger.id_proof}")
    print(f"  Member Since : {format_datetime(passenger.created_at)}")
    press_enter()


def update_profile(passenger: Passenger):
    """Allow passenger to update their details."""
    print_header("UPDATE PROFILE")
    print("  Leave blank to keep existing value.\n")

    new_email = input(f"  Email [{passenger.email}]: ").strip()
    new_id    = input(f"  ID Proof [{passenger.id_proof}]: ").strip()

    if new_email:
        from utils import validate_email
        if validate_email(new_email):
            passenger.email = new_email
        else:
            print_error("Invalid email. Not updated.")
    if new_id:
        passenger.id_proof = new_id

    storage.upsert("passengers", "passenger_id", passenger.to_dict())
    print_success("Profile updated.")
    press_enter()


def view_booking_history(passenger: Passenger):
    """Display all bookings for this passenger."""
    print_header(f"BOOKING HISTORY — {passenger.name}")

    if not passenger.booking_history:
        print_error("No bookings found.")
        press_enter()
        return

    bookings = storage.load("bookings")
    rows = []
    for b in bookings:
        if b["booking_id"] in passenger.booking_history:
            import schedule_manager, route_manager, bus_manager
            sched = schedule_manager.get_schedule_by_id(b["schedule_id"])
            if not sched:
                continue
            route = route_manager.get_route_by_id(sched.route_id)
            bus   = bus_manager.get_bus_by_id(sched.bus_id)
            route_str = f"{route.source[:8]}→{route.destination[:8]}" if route else "?"
            bus_name  = bus.bus_name[:15] if bus else "?"
            rows.append([
                b["booking_id"][:10],
                b["ticket_id"][:10],
                route_str,
                format_date(sched.journey_date) if sched else "?",
                sched.departure_time if sched else "?",
                ", ".join(b["seat_numbers"]),
                format_currency(b["fare"]),
                b["status"]
            ])

    if rows:
        print_table(
            ["Booking ID", "Ticket", "Route", "Date", "Time", "Seats", "Fare", "Status"],
            rows
        )
    else:
        print_error("Booking records not found.")
    press_enter()


def add_loyalty_points(passenger_id: str, points: int):
    """Add loyalty points to a passenger's account."""
    p = find_by_id(passenger_id)
    if p:
        p.loyalty_points += points
        storage.upsert("passengers", "passenger_id", p.to_dict())


def deduct_loyalty_points(passenger_id: str, points: int) -> bool:
    """Deduct loyalty points; returns False if insufficient."""
    p = find_by_id(passenger_id)
    if p and p.loyalty_points >= points:
        p.loyalty_points -= points
        storage.upsert("passengers", "passenger_id", p.to_dict())
        return True
    return False


def add_booking_to_history(passenger_id: str, booking_id: str):
    """Record a booking ID in the passenger's history."""
    p = find_by_id(passenger_id)
    if p:
        if booking_id not in p.booking_history:
            p.booking_history.append(booking_id)
            storage.upsert("passengers", "passenger_id", p.to_dict())


def list_all_passengers():
    """Admin: show all passengers."""
    print_header("ALL PASSENGERS")
    records = storage.load("passengers")
    if not records:
        print_error("No passengers registered.")
        press_enter()
        return
    rows = []
    for p in records:
        rows.append([
            p["passenger_id"][:10],
            truncate(p["name"], 18),
            p["phone"],
            p["age"],
            p["gender"],
            len(p.get("booking_history", [])),
            p.get("loyalty_points", 0)
        ])
    print_table(
        ["ID", "Name", "Phone", "Age", "Gender", "Bookings", "Pts"],
        rows
    )
    press_enter()
