"""
bus_manager.py
--------------
Handles all bus-related operations: add, update, deactivate, list, search.
"""

from models import Bus, BusType, generate_id
from utils import (
    print_header, print_subheader, print_success, print_error,
    print_table, get_input, get_int_input, get_float_input,
    get_menu_choice, confirm, select_from_list, press_enter,
    print_separator, truncate
)
import storage


# ─────────────────────────────────────────────────────────────────────────────
# CRUD OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────

def add_bus() -> Bus:
    """Interactively add a new bus to the system."""
    print_header("ADD NEW BUS")

    bus_number = get_input("Bus Number (e.g. TN01AB1234)").upper()
    # Check duplicate
    existing = storage.load("buses")
    if any(b["bus_number"] == bus_number for b in existing):
        print_error(f"Bus with number {bus_number} already exists.")
        press_enter()
        return None

    bus_name     = get_input("Bus Name (e.g. Sri Travels Volvo)")
    operator     = get_input("Operator / Company Name")

    print("\n  Bus Types:")
    for i, bt in enumerate(BusType.ALL, 1):
        print(f"    {i}. {bt}")
    bt_choice = get_int_input("Select Bus Type", 1, len(BusType.ALL))
    bus_type  = BusType.ALL[bt_choice - 1]

    total_seats = get_int_input("Total Seats", 10, 60)

    print("\n  Amenities (enter each on a new line, blank line to stop):")
    amenities = []
    while True:
        a = input("    Amenity: ").strip()
        if not a:
            break
        amenities.append(a)

    bus = Bus(
        bus_id      = generate_id("BUS"),
        bus_number  = bus_number,
        bus_name    = bus_name,
        bus_type    = bus_type,
        total_seats = total_seats,
        amenities   = amenities,
        operator_name = operator,
        is_active   = True,
        rating      = 0.0,
        total_ratings = 0
    )

    storage.upsert("buses", "bus_id", bus.to_dict())
    print_success(f"Bus '{bus_name}' added successfully! ID: {bus.bus_id}")
    press_enter()
    return bus


def update_bus():
    """Update details of an existing bus."""
    print_header("UPDATE BUS")
    bus = _select_bus()
    if not bus:
        return

    print(f"\n  Updating: {bus.bus_name} ({bus.bus_number})")
    print("  Leave blank to keep existing value.\n")

    new_name  = input(f"  Bus Name [{bus.bus_name}]: ").strip() or bus.bus_name
    new_op    = input(f"  Operator [{bus.operator_name}]: ").strip() or bus.operator_name
    new_seats_str = input(f"  Total Seats [{bus.total_seats}]: ").strip()
    new_seats = int(new_seats_str) if new_seats_str.isdigit() else bus.total_seats

    print(f"\n  Current Amenities: {', '.join(bus.amenities)}")
    change_amenities = confirm("Change amenities?")
    if change_amenities:
        amenities = []
        print("  Enter amenities (blank line to stop):")
        while True:
            a = input("    Amenity: ").strip()
            if not a:
                break
            amenities.append(a)
    else:
        amenities = bus.amenities

    bus.bus_name     = new_name
    bus.operator_name = new_op
    bus.total_seats  = new_seats
    bus.amenities    = amenities

    storage.upsert("buses", "bus_id", bus.to_dict())
    print_success("Bus updated successfully.")
    press_enter()


def deactivate_bus():
    """Deactivate (soft-delete) a bus."""
    print_header("DEACTIVATE BUS")
    bus = _select_bus(active_only=True)
    if not bus:
        return
    if confirm(f"Deactivate '{bus.bus_name}'? It won't appear in searches."):
        bus.is_active = False
        storage.upsert("buses", "bus_id", bus.to_dict())
        print_success(f"Bus '{bus.bus_name}' deactivated.")
    press_enter()


def get_all_buses(active_only: bool = False) -> list:
    """Return Bus objects, optionally filtering inactive."""
    records = storage.load("buses")
    buses = [Bus.from_dict(r) for r in records]
    if active_only:
        buses = [b for b in buses if b.is_active]
    return buses


def get_bus_by_id(bus_id: str) -> Bus:
    """Fetch a single Bus by its ID."""
    record = storage.find_by_id("buses", "bus_id", bus_id)
    return Bus.from_dict(record) if record else None


def list_buses(active_only: bool = False):
    """Display all buses in a formatted table."""
    print_header("BUS LIST")
    buses = get_all_buses(active_only)
    if not buses:
        print_error("No buses found.")
        press_enter()
        return

    rows = []
    for b in buses:
        rows.append([
            b.bus_id[:8],
            b.bus_number,
            truncate(b.bus_name, 20),
            b.bus_type,
            b.total_seats,
            "Active" if b.is_active else "Inactive",
            f"{b.average_rating()}★"
        ])
    print_table(
        ["ID", "Bus No.", "Name", "Type", "Seats", "Status", "Rating"],
        rows
    )
    press_enter()


def _select_bus(active_only: bool = False) -> Bus:
    """Helper: show bus list and let admin select one."""
    buses = get_all_buses(active_only)
    if not buses:
        print_error("No buses available.")
        press_enter()
        return None
    return select_from_list(
        buses,
        display_fn=lambda b: f"{b.bus_number}  |  {b.bus_name}  |  {b.bus_type}  |  {b.total_seats} seats",
        prompt="Select Bus"
    )


def search_buses_by_type(bus_type: str) -> list:
    """Return buses of a specific type."""
    buses = get_all_buses(active_only=True)
    return [b for b in buses if b.bus_type == bus_type]


def add_rating(bus_id: str, rating: int):
    """Add a rating (1-5) to a bus."""
    bus = get_bus_by_id(bus_id)
    if bus:
        bus.rating += rating
        bus.total_ratings += 1
        storage.upsert("buses", "bus_id", bus.to_dict())


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN BUS MENU
# ─────────────────────────────────────────────────────────────────────────────

def bus_management_menu():
    """Sub-menu for admin bus management."""
    while True:
        print_header("BUS MANAGEMENT")
        print("  1. Add New Bus")
        print("  2. Update Bus Details")
        print("  3. Deactivate Bus")
        print("  4. View All Buses")
        print("  0. Back")
        choice = get_menu_choice(4)
        if choice == 1:
            add_bus()
        elif choice == 2:
            update_bus()
        elif choice == 3:
            deactivate_bus()
        elif choice == 4:
            list_buses()
        elif choice == 0:
            break
