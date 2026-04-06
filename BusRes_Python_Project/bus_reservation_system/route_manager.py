"""
route_manager.py
----------------
Handles bus routes: creation, listing, updating, and stop management.
"""

from models import Route, generate_id
from utils import (
    print_header, print_subheader, print_success, print_error,
    print_table, get_input, get_int_input, get_float_input,
    get_menu_choice, confirm, select_from_list, press_enter,
    truncate, capitalize_words
)
import storage


# ─────────────────────────────────────────────────────────────────────────────
# CRUD OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────

def add_route() -> Route:
    """Interactively create a new route."""
    print_header("ADD NEW ROUTE")

    source      = capitalize_words(get_input("Source City"))
    destination = capitalize_words(get_input("Destination City"))

    # Check duplicate
    existing = storage.load("routes")
    if any(r["source"] == source and r["destination"] == destination for r in existing):
        print_error(f"Route {source} → {destination} already exists.")
        press_enter()
        return None

    distance = get_float_input("Total Distance (km)", min_val=1)
    duration = get_int_input("Estimated Duration (minutes)", min_val=1)
    base_fare = get_float_input("Base Fare (₹)", min_val=1)

    print("\n  Add intermediate stops (blank name to stop):")
    stops = []
    dist_so_far = 0.0
    time_so_far = 0
    while True:
        name = input("    Stop Name (blank to finish): ").strip()
        if not name:
            break
        name = capitalize_words(name)
        stop_dist  = get_float_input(f"  Distance from {source} (km)", min_val=dist_so_far + 1)
        arrive_off = get_int_input(f"  Arrival offset from start (minutes)", min_val=time_so_far + 1)
        depart_off = get_int_input(f"  Departure offset from start (minutes)", min_val=arrive_off)
        stops.append({
            "name": name,
            "distance_from_origin": stop_dist,
            "arrival_offset": arrive_off,
            "departure_offset": depart_off
        })
        dist_so_far = stop_dist
        time_so_far = depart_off

    route = Route(
        route_id    = generate_id("RTE"),
        source      = source,
        destination = destination,
        distance_km = distance,
        duration_minutes = duration,
        stops       = stops,
        base_fare   = base_fare,
        is_active   = True
    )

    storage.upsert("routes", "route_id", route.to_dict())
    print_success(f"Route {source} → {destination} added. ID: {route.route_id}")
    press_enter()
    return route


def update_route():
    """Update an existing route."""
    print_header("UPDATE ROUTE")
    route = _select_route()
    if not route:
        return

    print(f"\n  Updating: {route.source} → {route.destination}")
    new_dist = input(f"  Distance [{route.distance_km}km]: ").strip()
    new_dur  = input(f"  Duration [{route.duration_minutes} min]: ").strip()
    new_fare = input(f"  Base Fare [₹{route.base_fare}]: ").strip()

    if new_dist:
        try:
            route.distance_km = float(new_dist)
        except ValueError:
            pass
    if new_dur:
        try:
            route.duration_minutes = int(new_dur)
        except ValueError:
            pass
    if new_fare:
        try:
            route.base_fare = float(new_fare)
        except ValueError:
            pass

    storage.upsert("routes", "route_id", route.to_dict())
    print_success("Route updated successfully.")
    press_enter()


def deactivate_route():
    """Deactivate a route."""
    print_header("DEACTIVATE ROUTE")
    route = _select_route(active_only=True)
    if not route:
        return
    if confirm(f"Deactivate '{route.source} → {route.destination}'?"):
        route.is_active = False
        storage.upsert("routes", "route_id", route.to_dict())
        print_success("Route deactivated.")
    press_enter()


def get_all_routes(active_only: bool = False) -> list:
    records = storage.load("routes")
    routes = [Route.from_dict(r) for r in records]
    if active_only:
        routes = [r for r in routes if r.is_active]
    return routes


def get_route_by_id(route_id: str) -> Route:
    record = storage.find_by_id("routes", "route_id", route_id)
    return Route.from_dict(record) if record else None


def list_routes(active_only: bool = False):
    """Display routes in a formatted table."""
    print_header("ROUTE LIST")
    routes = get_all_routes(active_only)
    if not routes:
        print_error("No routes found.")
        press_enter()
        return

    rows = []
    for r in routes:
        stops_str = " → ".join(r.get_stop_names())
        rows.append([
            r.route_id[:8],
            r.source,
            r.destination,
            f"{r.distance_km:.0f} km",
            f"{r.duration_minutes // 60}h {r.duration_minutes % 60}m",
            f"₹{r.base_fare:.0f}",
            "Active" if r.is_active else "Off"
        ])
    print_table(
        ["ID", "From", "To", "Distance", "Duration", "Fare", "Status"],
        rows
    )
    press_enter()


def find_routes(source: str, destination: str) -> list:
    """Find active routes between source and destination (case-insensitive)."""
    routes = get_all_routes(active_only=True)
    src = source.lower()
    dst = destination.lower()
    return [
        r for r in routes
        if r.source.lower() == src and r.destination.lower() == dst
    ]


def _select_route(active_only: bool = False) -> Route:
    routes = get_all_routes(active_only)
    if not routes:
        print_error("No routes available.")
        press_enter()
        return None
    return select_from_list(
        routes,
        display_fn=lambda r: f"{r.source:15} →  {r.destination:15}  |  {r.distance_km:.0f}km  |  ₹{r.base_fare:.0f}",
        prompt="Select Route"
    )


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN ROUTE MENU
# ─────────────────────────────────────────────────────────────────────────────

def route_management_menu():
    while True:
        print_header("ROUTE MANAGEMENT")
        print("  1. Add New Route")
        print("  2. Update Route")
        print("  3. Deactivate Route")
        print("  4. View All Routes")
        print("  0. Back")
        choice = get_menu_choice(4)
        if choice == 1:
            add_route()
        elif choice == 2:
            update_route()
        elif choice == 3:
            deactivate_route()
        elif choice == 4:
            list_routes()
        elif choice == 0:
            break
