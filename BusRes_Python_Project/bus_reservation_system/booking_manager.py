"""
booking_manager.py
------------------
Handles the complete seat booking workflow:
- Bus search
- Seat selection
- Promo codes
- Booking confirmation
- Ticket generation
- Waitlist management
"""

from datetime import datetime
from models import (
    Booking, BookingStatus, Schedule, generate_id
)
from utils import (
    print_header, print_subheader, print_success, print_error, print_warning,
    print_info, print_table, print_ticket_box, print_seat_layout, print_separator,
    get_input, get_int_input, get_menu_choice, confirm, press_enter, now_str,
    today_str, format_date, format_datetime, format_currency,
    get_valid_date, select_from_list, truncate, get_valid_phone
)
import storage
import bus_manager
import route_manager
import schedule_manager
import passenger as pax_module


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

LOYALTY_POINTS_PER_BOOKING = 10   # points earned per booking
LOYALTY_REDEMPTION_RATE    = 0.50 # ₹0.50 per point


# ─────────────────────────────────────────────────────────────────────────────
# MAIN BOOKING FLOW
# ─────────────────────────────────────────────────────────────────────────────

def book_ticket(passenger=None):
    """
    Full booking workflow:
    1. Identify passenger
    2. Search buses
    3. Select schedule
    4. Select seats
    5. Apply promo/loyalty
    6. Confirm & save
    7. Print ticket
    """
    print_header("BOOK A TICKET")

    # Step 1 – Identify passenger
    if not passenger:
        passenger = pax_module.get_or_create_passenger()
        if not passenger:
            return

    # Step 2 – Search buses
    print_subheader("SEARCH FOR BUSES")
    source      = input("  From (City): ").strip()
    destination = input("  To   (City): ").strip()

    if not source or not destination:
        print_error("Source and destination cannot be empty.")
        press_enter()
        return

    journey_date = get_valid_date("Journey Date (YYYY-MM-DD)", future_only=True)

    # Optional filters
    print("\n  Optional Filters (press Enter to skip):")
    bus_type_input = input("  Bus Type (blank = any): ").strip()
    bus_type = bus_type_input if bus_type_input else None
    max_fare_input = input("  Max Fare ₹ (blank = any): ").strip()
    max_fare = float(max_fare_input) if max_fare_input.replace(".", "").isdigit() else None

    results = schedule_manager.search_schedules(
        source, destination, journey_date, bus_type, max_fare
    )

    if not results:
        print_error(f"No buses found from {source} to {destination} on {format_date(journey_date)}.")
        # Suggest nearby dates
        print_info("Try searching for a different date.")
        press_enter()
        return

    # Step 3 – Select schedule
    count = schedule_manager.display_schedule_results(results)
    print(f"\n  Enter bus number (1-{count}) to continue or 0 to cancel:")
    choice = get_int_input("Your choice", 0, count)
    if choice == 0:
        return

    selected = results[choice - 1]
    schedule: Schedule = selected["schedule"]
    bus    = selected["bus"]
    route  = selected["route"]
    fare_per_seat = selected["fare"]

    available = bus.total_seats - len(schedule.booked_seats)
    if available == 0:
        if confirm("No seats available. Join waiting list?"):
            _add_to_waitlist(schedule, passenger)
        return

    # Step 4 – Show seat layout and select seats
    print_seat_layout(bus.total_seats, schedule.booked_seats, bus.bus_type)

    num_seats = get_int_input(f"How many seats to book? (1-{min(available, 6)})", 1, min(available, 6))

    selected_seats = []
    for i in range(num_seats):
        while True:
            seat_input = input(f"  Select seat {i+1} (1-{bus.total_seats}): ").strip()
            if not seat_input.isdigit():
                print_error("Enter a valid seat number.")
                continue
            seat_str = seat_input
            seat_num = int(seat_input)
            if seat_num < 1 or seat_num > bus.total_seats:
                print_error(f"Seat must be between 1 and {bus.total_seats}.")
                continue
            if seat_str in schedule.booked_seats:
                print_error(f"Seat {seat_str} is already booked. Choose another.")
                continue
            if seat_str in selected_seats:
                print_error(f"You already selected seat {seat_str}.")
                continue
            selected_seats.append(seat_str)
            break

    # Co-passengers (if more than 1 seat)
    co_passengers = []
    if num_seats > 1:
        print_subheader("CO-PASSENGER DETAILS")
        for i in range(1, num_seats):
            print(f"\n  Co-Passenger {i} (Seat {selected_seats[i]}):")
            cp_name   = get_input("  Name")
            cp_age    = get_int_input("  Age", 1, 120)
            print("  Gender: 1. Male  2. Female  3. Other")
            cp_g      = get_int_input("  Choice", 1, 3)
            cp_gender = ["Male", "Female", "Other"][cp_g - 1]
            co_passengers.append({
                "name": cp_name, "age": cp_age,
                "gender": cp_gender, "seat": selected_seats[i]
            })

    # Boarding / dropping point
    print_subheader("BOARDING & DROPPING POINTS")
    boarding_pts = schedule.boarding_points if schedule.boarding_points else route.get_stop_names()[:-1]
    dropping_pts = schedule.dropping_points if schedule.dropping_points else route.get_stop_names()[1:]

    print("  Boarding Points:")
    for i, bp in enumerate(boarding_pts, 1):
        print(f"    {i}. {bp}")
    bp_choice = get_int_input("Select Boarding Point", 1, len(boarding_pts))
    boarding_point = boarding_pts[bp_choice - 1]

    print("\n  Dropping Points:")
    for i, dp in enumerate(dropping_pts, 1):
        print(f"    {i}. {dp}")
    dp_choice = get_int_input("Select Dropping Point", 1, len(dropping_pts))
    dropping_point = dropping_pts[dp_choice - 1]

    # Step 5 – Fare calculation
    total_fare = fare_per_seat * num_seats
    discount   = 0.0
    promo_code = ""

    print_subheader("FARE SUMMARY")
    print(f"  Base Fare       : {format_currency(fare_per_seat)} × {num_seats} = {format_currency(total_fare)}")

    # Promo code
    if confirm("Do you have a promo code?"):
        code_input = input("  Enter Promo Code: ").strip().upper()
        discount, promo_code = _apply_promo(code_input, total_fare)
        if discount > 0:
            print_success(f"Promo applied! Discount: {format_currency(discount)}")
        else:
            print_error("Invalid or expired promo code.")

    # Loyalty points redemption
    if passenger.loyalty_points > 0:
        max_points_to_use = min(passenger.loyalty_points, int(total_fare / LOYALTY_REDEMPTION_RATE))
        if max_points_to_use > 0 and confirm(
            f"Redeem loyalty points? You have {passenger.loyalty_points} pts "
            f"(max usable: {max_points_to_use} = {format_currency(max_points_to_use * LOYALTY_REDEMPTION_RATE)})"
        ):
            pts = get_int_input(f"Points to redeem (0-{max_points_to_use})", 0, max_points_to_use)
            loyalty_discount = pts * LOYALTY_REDEMPTION_RATE
            discount += loyalty_discount
            print_success(f"Loyalty discount: {format_currency(loyalty_discount)}")

    net_fare = max(0.0, total_fare - discount)
    print(f"\n  Discount        : {format_currency(discount)}")
    print(f"  Total Payable   : {format_currency(net_fare)}")
    print()

    # Step 6 – Booking summary
    print_subheader("BOOKING SUMMARY")
    print(f"  Passenger       : {passenger.name}  ({passenger.phone})")
    print(f"  Bus             : {bus.bus_name}  ({bus.bus_number})")
    print(f"  Type            : {bus.bus_type}")
    print(f"  Route           : {route.source} → {route.destination}")
    print(f"  Date            : {format_date(journey_date)}")
    print(f"  Departure       : {schedule.departure_time}   Arrival: {schedule.arrival_time}")
    print(f"  Seats           : {', '.join(selected_seats)}")
    print(f"  Boarding Point  : {boarding_point}")
    print(f"  Dropping Point  : {dropping_point}")
    print(f"  Fare Payable    : {format_currency(net_fare)}")
    print()

    if not confirm("Confirm booking?"):
        print_warning("Booking cancelled.")
        press_enter()
        return

    # Step 7 – Save booking
    booking_id = generate_id("BKG")
    ticket_id  = _generate_ticket_id()

    booking = Booking(
        booking_id      = booking_id,
        ticket_id       = ticket_id,
        passenger_id    = passenger.passenger_id,
        schedule_id     = schedule.schedule_id,
        seat_numbers    = selected_seats,
        fare            = net_fare,
        boarding_point  = boarding_point,
        dropping_point  = dropping_point,
        status          = BookingStatus.CONFIRMED,
        promo_code      = promo_code,
        discount_amount = discount,
        created_at      = now_str(),
        co_passengers   = co_passengers
    )

    # Update schedule's booked seats
    for seat in selected_seats:
        if seat not in schedule.booked_seats:
            schedule.booked_seats.append(seat)
    storage.upsert("schedules", "schedule_id", schedule.to_dict())

    # Save booking
    storage.upsert("bookings", "booking_id", booking.to_dict())

    # Update passenger history
    pax_module.add_booking_to_history(passenger.passenger_id, booking_id)

    # Award loyalty points
    points_earned = LOYALTY_POINTS_PER_BOOKING * num_seats
    pax_module.add_loyalty_points(passenger.passenger_id, points_earned)

    # Update promo usage
    if promo_code:
        _increment_promo_usage(promo_code)

    print_success(f"Booking Confirmed!  Ticket ID: {ticket_id}")
    print_info(f"You earned {points_earned} loyalty points.")
    press_enter()

    # Print ticket
    print_ticket(booking, passenger, schedule, bus, route)


# ─────────────────────────────────────────────────────────────────────────────
# TICKET GENERATION
# ─────────────────────────────────────────────────────────────────────────────

def print_ticket(booking: Booking, passenger, schedule: Schedule, bus, route):
    """Render a formatted text ticket to the console."""
    print_header("YOUR TICKET")
    lines = [
        "★  BUS RESERVATION SYSTEM  ★",
        "",
        f"  TICKET ID   : {booking.ticket_id}",
        f"  BOOKING ID  : {booking.booking_id}",
        "",
        f"  Passenger   : {passenger.name}",
        f"  Age/Gender  : {passenger.age} / {passenger.gender}",
        f"  Phone       : {passenger.phone}",
        "",
        "  ─────────────────────────────────────────────────",
        f"  Bus         : {bus.bus_name}  ({bus.bus_number})",
        f"  Bus Type    : {bus.bus_type}",
        f"  Route       : {route.source}  →  {route.destination}",
        f"  Journey Date: {format_date(schedule.journey_date)}",
        f"  Departure   : {schedule.departure_time}     Arrival: {schedule.arrival_time}",
        "  ─────────────────────────────────────────────────",
        f"  Seat(s)     : {', '.join(booking.seat_numbers)}",
        f"  Boarding At : {booking.boarding_point}",
        f"  Dropping At : {booking.dropping_point}",
        "  ─────────────────────────────────────────────────",
    ]

    if booking.co_passengers:
        lines.append("  CO-PASSENGERS:")
        for cp in booking.co_passengers:
            lines.append(f"    • {cp['name']} ({cp['age']}, {cp['gender']}) - Seat {cp['seat']}")
        lines.append("  ─────────────────────────────────────────────────")

    lines += [
        f"  Fare Paid   : {format_currency(booking.fare)}",
    ]
    if booking.discount_amount > 0:
        lines.append(f"  Discount    : {format_currency(booking.discount_amount)}")
    if booking.promo_code:
        lines.append(f"  Promo Code  : {booking.promo_code}")

    lines += [
        "",
        f"  Booked On   : {format_datetime(booking.created_at)}",
        "",
        "  ✔  Have a safe journey!",
        "  Amenities: " + (", ".join(bus.amenities) if bus.amenities else "Standard"),
    ]

    print_ticket_box(lines)
    press_enter()


def view_ticket_by_id():
    """Let a passenger retrieve and reprint their ticket."""
    print_header("VIEW TICKET")
    ticket_id = get_input("Enter Ticket ID or Booking ID")
    booking_record = None

    # Try ticket_id first
    records = storage.load("bookings")
    for r in records:
        if r["ticket_id"] == ticket_id or r["booking_id"] == ticket_id:
            booking_record = r
            break

    if not booking_record:
        print_error("Ticket not found. Please check the ID.")
        press_enter()
        return

    booking   = Booking.from_dict(booking_record)
    passenger = pax_module.find_by_id(booking.passenger_id)
    schedule  = schedule_manager.get_schedule_by_id(booking.schedule_id)
    bus       = bus_manager.get_bus_by_id(schedule.bus_id) if schedule else None
    route     = route_manager.get_route_by_id(schedule.route_id) if schedule else None

    if not all([passenger, schedule, bus, route]):
        print_error("Could not load all ticket details.")
        press_enter()
        return

    if booking.status == BookingStatus.CANCELLED:
        print_warning(f"This booking was cancelled. Ticket ID: {ticket_id}")
        press_enter()
        return

    print_ticket(booking, passenger, schedule, bus, route)


# ─────────────────────────────────────────────────────────────────────────────
# AVAILABILITY CHECK
# ─────────────────────────────────────────────────────────────────────────────

def check_availability():
    """Public function to check seat availability for a route/date."""
    print_header("CHECK SEAT AVAILABILITY")

    source      = input("  From (City): ").strip()
    destination = input("  To   (City): ").strip()
    journey_date = get_valid_date("Journey Date (YYYY-MM-DD)", future_only=True)

    results = schedule_manager.search_schedules(source, destination, journey_date)

    if not results:
        print_error("No buses found for this search.")
        press_enter()
        return

    print_subheader(f"AVAILABILITY — {source} → {destination}  |  {format_date(journey_date)}")

    for r in results:
        s     = r["schedule"]
        b     = r["bus"]
        avail = r["available_seats"]
        total = b.total_seats
        booked = total - avail
        bar_filled = int(booked / total * 20) if total else 0
        bar = "█" * bar_filled + "░" * (20 - bar_filled)
        status = "FULL" if avail == 0 else ("FEW LEFT" if avail <= 5 else "AVAILABLE")
        print(f"\n  {b.bus_name[:25]:<25}  |  Departs {s.departure_time}")
        print(f"  [{bar}]  {booked}/{total} booked  |  {avail} seats free  [{status}]")
        print(f"  Fare: {format_currency(r['fare'])}   ID: {s.schedule_id[:12]}")
        print_separator()

    press_enter()


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _generate_ticket_id() -> str:
    """Generate a human-readable ticket number."""
    import random
    prefix = "BRS"
    number = random.randint(100000, 999999)
    return f"{prefix}{number}"


def _apply_promo(code: str, fare: float):
    """
    Validate promo code and return (discount_amount, code) or (0, '').
    """
    from models import PromoCode
    records = storage.load("promo_codes")
    for r in records:
        promo = PromoCode.from_dict(r)
        if promo.code == code:
            if promo.is_valid(fare, today_str()):
                discount = promo.calculate_discount(fare)
                return discount, code
            else:
                return 0.0, ""
    return 0.0, ""


def _increment_promo_usage(code: str):
    """Increment the used_count for a promo code."""
    from models import PromoCode
    records = storage.load("promo_codes")
    for i, r in enumerate(records):
        if r["code"] == code:
            records[i]["used_count"] = r.get("used_count", 0) + 1
            storage.save("promo_codes", records)
            return


def _add_to_waitlist(schedule: Schedule, passenger):
    """Add a passenger to the waitlist for a schedule."""
    if passenger.passenger_id not in schedule.waitlist:
        schedule.waitlist.append(passenger.passenger_id)
        storage.upsert("schedules", "schedule_id", schedule.to_dict())
        print_success(
            f"Added to waitlist. Position: {len(schedule.waitlist)}. "
            "You'll be notified when a seat becomes available."
        )
    else:
        print_info("You are already on the waitlist for this journey.")
    press_enter()


def get_booking_by_id(booking_id: str) -> Booking:
    r = storage.find_by_id("bookings", "booking_id", booking_id)
    return Booking.from_dict(r) if r else None


def get_bookings_by_phone(phone: str) -> list:
    """Get all bookings for a passenger identified by phone."""
    p = pax_module.find_by_phone(phone)
    if not p:
        return []
    return [
        Booking.from_dict(b)
        for b in storage.load("bookings")
        if b["passenger_id"] == p.passenger_id
    ]


def list_all_bookings():
    """Admin: list all bookings."""
    print_header("ALL BOOKINGS")
    records = storage.load("bookings")
    if not records:
        print_error("No bookings found.")
        press_enter()
        return
    rows = []
    for b in records:
        sched = schedule_manager.get_schedule_by_id(b["schedule_id"])
        pax   = pax_module.find_by_id(b["passenger_id"])
        rows.append([
            b["booking_id"][:10],
            b["ticket_id"],
            truncate(pax.name if pax else "?", 14),
            format_date(sched.journey_date) if sched else "?",
            ", ".join(b["seat_numbers"]),
            format_currency(b["fare"]),
            b["status"]
        ])
    print_table(
        ["Booking ID", "Ticket", "Passenger", "Date", "Seats", "Fare", "Status"],
        rows
    )
    press_enter()
