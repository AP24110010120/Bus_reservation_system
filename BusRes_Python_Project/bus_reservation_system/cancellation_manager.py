"""
cancellation_manager.py
-----------------------
Handles booking cancellations with tiered charges,
refund calculations, seat freeing, and waitlist promotion.
"""

from datetime import datetime, date
from models import Cancellation, BookingStatus, generate_id
from utils import (
    print_header, print_subheader, print_success, print_error, print_warning,
    print_table, print_separator, get_input, get_menu_choice, confirm,
    press_enter, now_str, today_str, format_date, format_datetime,
    format_currency, get_valid_phone
)
import storage
import booking_manager
import passenger as pax_module
import schedule_manager
import bus_manager
import route_manager


# ─────────────────────────────────────────────────────────────────────────────
# CANCELLATION CHARGE RULES
# Days before journey → charge % of fare
# ─────────────────────────────────────────────────────────────────────────────

CANCELLATION_TIERS = [
    (0,   100.0),   # same day — no refund
    (1,    50.0),   # 1 day before — 50% charge
    (3,    25.0),   # 2-3 days before — 25% charge
    (7,    10.0),   # 4-7 days before — 10% charge
    (9999,  5.0),   # more than 7 days — 5% charge
]


def calculate_cancellation_charge(journey_date: str, fare: float) -> tuple:
    """
    Returns (charge_amount, refund_amount, charge_percent)
    based on how far in advance the cancellation is made.
    """
    try:
        jdate = datetime.strptime(journey_date, "%Y-%m-%d").date()
        days_left = (jdate - date.today()).days
    except ValueError:
        days_left = 0

    charge_pct = 100.0  # default: no refund
    for threshold, pct in CANCELLATION_TIERS:
        if days_left <= threshold:
            charge_pct = pct
            break

    charge = round(fare * charge_pct / 100, 2)
    refund = round(fare - charge, 2)
    return charge, refund, charge_pct


# ─────────────────────────────────────────────────────────────────────────────
# MAIN CANCELLATION FLOW
# ─────────────────────────────────────────────────────────────────────────────

def cancel_booking_flow():
    """
    Complete cancellation flow:
    1. Find booking by ticket/booking ID or phone
    2. Show details + cancellation charges
    3. Confirm → process cancellation
    """
    print_header("CANCEL BOOKING")

    print("  Find your booking by:")
    print("  1. Ticket ID or Booking ID")
    print("  2. Phone Number")
    choice = get_menu_choice(2)

    booking = None
    if choice == 1:
        ref_id = get_input("Enter Ticket ID or Booking ID")
        records = storage.load("bookings")
        for r in records:
            if r["ticket_id"] == ref_id or r["booking_id"] == ref_id:
                from models import Booking
                booking = Booking.from_dict(r)
                break
        if not booking:
            print_error("Booking not found with this ID.")
            press_enter()
            return

    elif choice == 2:
        phone = get_valid_phone()
        bookings = booking_manager.get_bookings_by_phone(phone)
        active = [b for b in bookings if b.status == BookingStatus.CONFIRMED]
        if not active:
            print_error("No active bookings found for this phone number.")
            press_enter()
            return

        print_subheader("SELECT BOOKING TO CANCEL")
        from utils import select_from_list
        def booking_label(b):
            sched = schedule_manager.get_schedule_by_id(b.schedule_id)
            route = route_manager.get_route_by_id(sched.route_id) if sched else None
            route_str = f"{route.source} → {route.destination}" if route else "?"
            date_str  = format_date(sched.journey_date) if sched else "?"
            return f"Ticket: {b.ticket_id}  |  {route_str}  |  {date_str}  |  Seats: {', '.join(b.seat_numbers)}"
        booking = select_from_list(active, display_fn=booking_label, prompt="Select Booking")
        if not booking:
            return
    else:
        return

    # Already cancelled?
    if booking.status == BookingStatus.CANCELLED:
        print_warning("This booking is already cancelled.")
        press_enter()
        return

    # Load related data
    schedule = schedule_manager.get_schedule_by_id(booking.schedule_id)
    bus      = bus_manager.get_bus_by_id(schedule.bus_id) if schedule else None
    route    = route_manager.get_route_by_id(schedule.route_id) if schedule else None
    passenger = pax_module.find_by_id(booking.passenger_id)

    if not schedule or not bus or not route:
        print_error("Could not load booking details. Please contact support.")
        press_enter()
        return

    # Calculate charges
    charge, refund, pct = calculate_cancellation_charge(
        schedule.journey_date, booking.fare
    )

    # Display cancellation summary
    print_subheader("CANCELLATION DETAILS")
    print(f"  Ticket ID       : {booking.ticket_id}")
    print(f"  Booking ID      : {booking.booking_id}")
    print(f"  Passenger       : {passenger.name if passenger else '?'}")
    print(f"  Route           : {route.source} → {route.destination}")
    print(f"  Journey Date    : {format_date(schedule.journey_date)}")
    print(f"  Seats           : {', '.join(booking.seat_numbers)}")
    print(f"  Fare Paid       : {format_currency(booking.fare)}")
    print()
    print_separator()
    print(f"  Cancellation Charge : {pct:.0f}%  =  {format_currency(charge)}")
    print(f"  Refund Amount       : {format_currency(refund)}")
    print_separator()

    if refund == 0:
        print_warning("This cancellation will result in NO refund (same-day cancellation).")
    else:
        print(f"\n  Refund of {format_currency(refund)} will be processed within 5-7 business days.")

    reason = input("\n  Reason for cancellation (optional): ").strip() or "User Requested"

    if not confirm("Proceed with cancellation?"):
        print_warning("Cancellation aborted.")
        press_enter()
        return

    # Process cancellation
    _process_cancellation(booking, schedule, charge, refund, reason)

    print_success(f"Booking {booking.ticket_id} cancelled successfully.")
    if refund > 0:
        print_info(f"Refund of {format_currency(refund)} will be credited to your account.")
    press_enter()


def _process_cancellation(booking, schedule, charge: float, refund: float, reason: str):
    """Internal: execute the cancellation and update all records."""
    from models import Booking

    # 1. Mark booking as cancelled
    booking.status = BookingStatus.CANCELLED
    storage.upsert("bookings", "booking_id", booking.to_dict())

    # 2. Free seats in schedule
    for seat in booking.seat_numbers:
        if seat in schedule.booked_seats:
            schedule.booked_seats.remove(seat)

    # 3. Promote from waitlist if available
    if schedule.waitlist:
        next_pax_id = schedule.waitlist.pop(0)
        # Notify (console message simulation)
        next_pax = pax_module.find_by_id(next_pax_id)
        if next_pax:
            print_info(
                f"Waitlisted passenger {next_pax.name} ({next_pax.phone}) "
                "has been notified — a seat is now available!"
            )

    storage.upsert("schedules", "schedule_id", schedule.to_dict())

    # 4. Record cancellation
    cancellation = Cancellation(
        cancellation_id   = generate_id("CXL"),
        booking_id        = booking.booking_id,
        cancelled_at      = now_str(),
        original_fare     = booking.fare,
        cancellation_charge = charge,
        refund_amount     = refund,
        reason            = reason
    )
    storage.upsert("cancellations", "cancellation_id", cancellation.to_dict())

    # 5. Deduct loyalty points earned from this booking (if any)
    from booking_manager import LOYALTY_POINTS_PER_BOOKING
    points_to_deduct = LOYALTY_POINTS_PER_BOOKING * len(booking.seat_numbers)
    pax_module.deduct_loyalty_points(booking.passenger_id, points_to_deduct)


# ─────────────────────────────────────────────────────────────────────────────
# VIEW / LIST CANCELLATIONS
# ─────────────────────────────────────────────────────────────────────────────

def list_cancellations():
    """Admin: show all cancellations."""
    print_header("CANCELLATION RECORDS")
    records = storage.load("cancellations")
    if not records:
        print_error("No cancellations recorded.")
        press_enter()
        return
    rows = []
    for c in records:
        rows.append([
            c["cancellation_id"][:10],
            c["booking_id"][:10],
            format_datetime(c["cancelled_at"])[:16],
            format_currency(c["original_fare"]),
            format_currency(c["cancellation_charge"]),
            format_currency(c["refund_amount"])
        ])
    print_table(
        ["Cancellation ID", "Booking ID", "Cancelled At", "Orig Fare", "Charge", "Refund"],
        rows
    )
    press_enter()
