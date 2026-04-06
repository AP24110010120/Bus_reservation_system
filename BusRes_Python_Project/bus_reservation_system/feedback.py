"""
feedback.py
-----------
Post-trip feedback and ratings submission from passengers.
"""

from models import Feedback, BookingStatus, generate_id
from utils import (
    print_header, print_subheader, print_success, print_error,
    get_input, get_int_input, get_menu_choice, press_enter, now_str
)
import storage
import passenger as pax_module
import booking_manager
import bus_manager
import schedule_manager


def submit_feedback(passenger=None):
    """Allow a passenger to submit feedback for a completed trip."""
    print_header("SUBMIT TRIP FEEDBACK")

    if not passenger:
        passenger = pax_module.get_or_create_passenger()
        if not passenger:
            return

    # Get completed bookings for this passenger
    all_bookings = storage.load("bookings")
    completed = [
        b for b in all_bookings
        if b["passenger_id"] == passenger.passenger_id
        and b["status"] in (BookingStatus.CONFIRMED, BookingStatus.COMPLETED)
    ]

    if not completed:
        print_error("No completed trips found for feedback.")
        press_enter()
        return

    # Check which ones already have feedback
    existing_feedback = {f["booking_id"] for f in storage.load("feedback")}
    eligible = [b for b in completed if b["booking_id"] not in existing_feedback]

    if not eligible:
        print_error("You have already submitted feedback for all your trips.")
        press_enter()
        return

    print_subheader("SELECT TRIP TO RATE")
    from utils import select_from_list
    from models import Booking

    def booking_label(b):
        sched = schedule_manager.get_schedule_by_id(b["schedule_id"])
        import route_manager
        route = route_manager.get_route_by_id(sched.route_id) if sched else None
        route_str = f"{route.source} → {route.destination}" if route else "?"
        date_str  = sched.journey_date if sched else "?"
        return f"Ticket: {b['ticket_id']}  |  {route_str}  |  {date_str}"

    selected = select_from_list(eligible, display_fn=booking_label, prompt="Select Trip")
    if not selected:
        return

    booking = Booking.from_dict(selected)
    sched   = schedule_manager.get_schedule_by_id(booking.schedule_id)
    bus     = bus_manager.get_bus_by_id(sched.bus_id) if sched else None

    print(f"\n  Rating for: {bus.bus_name if bus else 'Bus'}")
    print("  Rate your experience (1 = Poor, 5 = Excellent):")
    rating = get_int_input("Rating (1-5)", 1, 5)
    stars = "★" * rating + "☆" * (5 - rating)
    print(f"  Your rating: {stars}")

    comment = input("  Comments (optional): ").strip()

    feedback = Feedback(
        feedback_id  = generate_id("FBK"),
        booking_id   = booking.booking_id,
        bus_id       = sched.bus_id if sched else "",
        passenger_id = passenger.passenger_id,
        rating       = rating,
        comment      = comment,
        submitted_at = now_str()
    )

    storage.upsert("feedback", "feedback_id", feedback.to_dict())

    # Update bus average rating
    if bus:
        bus_manager.add_rating(bus.bus_id, rating)

    print_success("Thank you for your feedback!")
    press_enter()
