"""
main.py
-------
Entry point for the Bus Reservation System.
Displays the main menu and routes to passenger or admin flows.

Run:
    python main.py

Default Admin Credentials:
    Username: admin
    Password: admin123
"""

import sys
import os

# Ensure the project root is in path
sys.path.insert(0, os.path.dirname(__file__))

from utils import (
    print_banner, print_header, print_subheader, print_success,
    print_error, print_warning, print_info, print_separator,
    get_menu_choice, press_enter, clear_screen
)


# ─────────────────────────────────────────────────────────────────────────────
# PASSENGER MENU
# ─────────────────────────────────────────────────────────────────────────────

def passenger_menu():
    """Main menu for passengers/users."""
    import passenger as pax_module
    import booking_manager as bkm
    import cancellation_manager as cxl
    import feedback as fb

    # Identify passenger (optional — they can still search without account)
    current_passenger = None

    while True:
        print_header("PASSENGER MENU")
        if current_passenger:
            print(f"  Logged in as: {current_passenger.name}  |  Loyalty Points: {current_passenger.loyalty_points}")
            print_separator()
        print("  1.  Search Buses")
        print("  2.  Book a Ticket")
        print("  3.  Check Seat Availability")
        print("  4.  View / Print Ticket")
        print("  5.  Cancel a Booking")
        print("  6.  My Booking History")
        print("  7.  My Profile")
        print("  8.  Submit Trip Feedback")
        print("  9.  Register as New Passenger")
        if not current_passenger:
            print(" 10.  Login (Find My Account)")
        print("  0.  Back to Main Menu")
        print()

        max_opt = 10 if not current_passenger else 9
        choice = get_menu_choice(max_opt)

        if choice == 1:
            _search_buses_only()
        elif choice == 2:
            bkm.book_ticket(current_passenger)
            # Refresh passenger data after booking
            if current_passenger:
                current_passenger = pax_module.find_by_id(current_passenger.passenger_id)
        elif choice == 3:
            bkm.check_availability()
        elif choice == 4:
            bkm.view_ticket_by_id()
        elif choice == 5:
            cxl.cancel_booking_flow()
            if current_passenger:
                current_passenger = pax_module.find_by_id(current_passenger.passenger_id)
        elif choice == 6:
            if current_passenger:
                pax_module.view_booking_history(current_passenger)
            else:
                print_warning("Please login first (option 10).")
                press_enter()
        elif choice == 7:
            if current_passenger:
                _profile_menu(current_passenger)
                current_passenger = pax_module.find_by_id(current_passenger.passenger_id)
            else:
                print_warning("Please login first (option 10).")
                press_enter()
        elif choice == 8:
            fb.submit_feedback(current_passenger)
        elif choice == 9:
            new_pax = pax_module.register_passenger()
            if new_pax and not current_passenger:
                current_passenger = new_pax
        elif choice == 10 and not current_passenger:
            current_passenger = _passenger_login()
        elif choice == 0:
            break


def _passenger_login():
    """Quick login by phone number."""
    import passenger as pax_module
    print_header("PASSENGER LOGIN")
    from utils import get_valid_phone
    phone = get_valid_phone()
    p = pax_module.find_by_phone(phone)
    if p:
        print_success(f"Welcome back, {p.name}!")
        press_enter()
        return p
    else:
        print_error("No account found. Use option 9 to register.")
        press_enter()
        return None


def _profile_menu(passenger):
    """Sub-menu for passenger profile management."""
    import passenger as pax_module
    while True:
        print_header("MY PROFILE")
        print("  1. View Profile")
        print("  2. Update Profile")
        print("  3. View Booking History")
        print("  0. Back")
        choice = get_menu_choice(3)
        if choice == 1:
            pax_module.view_profile(passenger)
        elif choice == 2:
            pax_module.update_profile(passenger)
            passenger = pax_module.find_by_id(passenger.passenger_id)
        elif choice == 3:
            pax_module.view_booking_history(passenger)
        elif choice == 0:
            break


def _search_buses_only():
    """Standalone bus search without booking."""
    import schedule_manager as sm
    from utils import get_valid_date, format_date, get_int_input
    from models import BusType

    print_header("SEARCH BUSES")
    source      = input("  From (City): ").strip()
    destination = input("  To   (City): ").strip()
    if not source or not destination:
        print_error("Source and destination are required.")
        press_enter()
        return

    journey_date = get_valid_date("Journey Date (YYYY-MM-DD)", future_only=True)

    print("\n  Optional Filters:")
    print("  Bus Types:")
    for i, bt in enumerate(BusType.ALL, 1):
        print(f"    {i}. {bt}")
    bt_input = input("  Select bus type (0 = any): ").strip()
    bus_type = BusType.ALL[int(bt_input) - 1] if bt_input.isdigit() and 1 <= int(bt_input) <= len(BusType.ALL) else None
    max_fare_str = input("  Max Fare ₹ (blank = any): ").strip()
    max_fare = float(max_fare_str) if max_fare_str.replace(".", "").isdigit() else None

    results = sm.search_schedules(source, destination, journey_date, bus_type, max_fare)
    sm.display_schedule_results(results)
    press_enter()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """Application entry point."""
    # Seed sample data on first run
    from seed_data import seed_all
    seed_all()

    import admin as adm

    while True:
        print_banner()
        print("  ┌─────────────────────────────────────────────┐")
        print("  │              MAIN MENU                      │")
        print("  ├─────────────────────────────────────────────┤")
        print("  │  1.  Passenger / User                       │")
        print("  │  2.  Admin Login                            │")
        print("  │  0.  Exit                                   │")
        print("  └─────────────────────────────────────────────┘")

        choice = get_menu_choice(2)

        if choice == 1:
            passenger_menu()
        elif choice == 2:
            admin = adm.admin_login()
            if admin:
                adm.admin_menu(admin)
        elif choice == 0:
            print()
            print("  Thank you for using Bus Reservation System!")
            print("  Have a safe journey. Goodbye! 👋")
            print()
            sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Interrupted. Exiting... Goodbye!\n")
        sys.exit(0)
