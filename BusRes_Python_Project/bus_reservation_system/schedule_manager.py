"""
schedule_manager.py
-------------------
Manages bus schedules: assigning buses to routes on specific dates/times,
preventing conflicts, and supporting recurring schedules.
"""

from datetime import datetime, date, timedelta
from models import Schedule, JourneyStatus, generate_id
from utils import (
    print_header, print_subheader, print_success, print_error, print_warning,
    print_table, get_input, get_int_input, get_float_input,
    get_menu_choice, confirm, select_from_list, press_enter,
    get_valid_date, get_valid_time, format_date, today_str, truncate
)
import storage
import bus_manager
import route_manager


# ─────────────────────────────────────────────────────────────────────────────
# CRUD OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────

def add_schedule() -> Schedule:
    """Interactively create a new schedule."""
    print_header("ADD NEW SCHEDULE")

    # Pick bus
    print_subheader("Select Bus")
    bus = bus_manager._select_bus(active_only=True)
    if not bus:
        return None

    # Pick route
    print_subheader("Select Route")
    route = route_manager._select_route(active_only=True)
    if not route:
        return None

    journey_date   = get_valid_date("Journey Date (YYYY-MM-DD)", future_only=True)
    departure_time = get_valid_time("Departure Time (HH:MM)")
    arrival_time   = get_valid_time("Arrival Time (HH:MM)")

    # Check bus conflict: same bus on same date at overlapping time
    if _has_conflict(bus.bus_id, journey_date, departure_time, arrival_time):
        print_error("Conflict! This bus is already scheduled at an overlapping time on this date.")
        press_enter()
        return None

    fare_multiplier = get_float_input("Fare Multiplier (1.0 = base fare, 1.5 = 50% premium)", min_val=0.5)

    # Boarding / dropping points
    stop_names = route.get_stop_names()
    print(f"\n  Stops on this route: {', '.join(stop_names)}")
    boarding_points = []
    dropping_points = []
    print("  Enter boarding points (blank to use all route stops):")
    bp = input("    Boarding points (comma-separated, blank for all): ").strip()
    boarding_points = [x.strip() for x in bp.split(",") if x.strip()] if bp else stop_names[:-1]
    print("  Enter dropping points (blank to use all route stops):")
    dp = input("    Dropping points (comma-separated, blank for all): ").strip()
    dropping_points = [x.strip() for x in dp.split(",") if x.strip()] if dp else stop_names[1:]

    schedule = Schedule(
        schedule_id      = generate_id("SCH"),
        bus_id           = bus.bus_id,
        route_id         = route.route_id,
        journey_date     = journey_date,
        departure_time   = departure_time,
        arrival_time     = arrival_time,
        fare_multiplier  = fare_multiplier,
        booked_seats     = [],
        waitlist         = [],
        status           = JourneyStatus.UPCOMING,
        boarding_points  = boarding_points,
        dropping_points  = dropping_points
    )

    storage.upsert("schedules", "schedule_id", schedule.to_dict())
    print_success(f"Schedule created! ID: {schedule.schedule_id}")
    press_enter()
    return schedule


def add_recurring_schedules():
    """Add a schedule for multiple consecutive dates (e.g., weekly service)."""
    print_header("ADD RECURRING SCHEDULE")

    bus = bus_manager._select_bus(active_only=True)
    if not bus:
        return
    route = route_manager._select_route(active_only=True)
    if not route:
        return

    start_date     = get_valid_date("Start Date (YYYY-MM-DD)", future_only=True)
    num_days       = get_int_input("Number of days to repeat", 1, 90)
    departure_time = get_valid_time("Departure Time (HH:MM)")
    arrival_time   = get_valid_time("Arrival Time (HH:MM)")
    fare_multiplier = get_float_input("Fare Multiplier", min_val=0.5)

    stop_names = route.get_stop_names()
    created = 0
    skipped = 0
    d = datetime.strptime(start_date, "%Y-%m-%d").date()

    for _ in range(num_days):
        jdate = d.strftime("%Y-%m-%d")
        if not _has_conflict(bus.bus_id, jdate, departure_time, arrival_time):
            schedule = Schedule(
                schedule_id     = generate_id("SCH"),
                bus_id          = bus.bus_id,
                route_id        = route.route_id,
                journey_date    = jdate,
                departure_time  = departure_time,
                arrival_time    = arrival_time,
                fare_multiplier = fare_multiplier,
                booked_seats    = [],
                waitlist        = [],
                status          = JourneyStatus.UPCOMING,
                boarding_points = stop_names[:-1],
                dropping_points = stop_names[1:]
            )
            storage.upsert("schedules", "schedule_id", schedule.to_dict())
            created += 1
        else:
            skipped += 1
        d += timedelta(days=1)

    print_success(f"Created {created} schedules. Skipped {skipped} due to conflicts.")
    press_enter()


def cancel_schedule():
    """Cancel a scheduled trip."""
    print_header("CANCEL SCHEDULE")
    schedule = _select_schedule()
    if not schedule:
        return
    if schedule.booked_seats:
        print_warning(f"This schedule has {len(schedule.booked_seats)} booked seats. Cancelling will affect passengers.")
    if confirm("Cancel this schedule?"):
        schedule.status = JourneyStatus.CANCELLED
        storage.upsert("schedules", "schedule_id", schedule.to_dict())
        print_success("Schedule cancelled.")
    press_enter()


def get_all_schedules(future_only: bool = False) -> list:
    records = storage.load("schedules")
    schedules = [Schedule.from_dict(r) for r in records]
    if future_only:
        today = today_str()
        schedules = [s for s in schedules if s.journey_date >= today]
    return schedules


def get_schedule_by_id(schedule_id: str) -> Schedule:
    record = storage.find_by_id("schedules", "schedule_id", schedule_id)
    return Schedule.from_dict(record) if record else None


def search_schedules(source: str, destination: str, journey_date: str,
                     bus_type: str = None, max_fare: float = None) -> list:
    """
    Find schedules matching source → destination on a given date.
    Optionally filter by bus type and maximum fare.
    Returns list of dicts with enriched display info.
    """
    import route_manager as rm
    matching_routes = rm.find_routes(source, destination)
    if not matching_routes:
        return []

    route_ids = {r.route_id for r in matching_routes}
    all_schedules = get_all_schedules()

    results = []
    for s in all_schedules:
        if s.route_id not in route_ids:
            continue
        if s.journey_date != journey_date:
            continue
        if s.status == JourneyStatus.CANCELLED:
            continue

        bus = bus_manager.get_bus_by_id(s.bus_id)
        if not bus or not bus.is_active:
            continue

        route = rm.get_route_by_id(s.route_id)
        if not route:
            continue

        # Filter by bus type
        if bus_type and bus.bus_type != bus_type:
            continue

        effective_fare = route.base_fare * s.fare_multiplier

        # Filter by max fare
        if max_fare and effective_fare > max_fare:
            continue

        available = bus.total_seats - len(s.booked_seats)

        results.append({
            "schedule": s,
            "bus": bus,
            "route": route,
            "fare": effective_fare,
            "available_seats": available
        })

    # Sort by departure time
    results.sort(key=lambda x: x["schedule"].departure_time)
    return results


def display_schedule_results(results: list) -> int:
    """Display search results. Returns number of results."""
    if not results:
        print_error("No buses found for this route/date.")
        return 0

    print_subheader(f"  {len(results)} Bus(es) Found")
    for i, r in enumerate(results, 1):
        s   = r["schedule"]
        b   = r["bus"]
        rt  = r["route"]
        avail = r["available_seats"]
        status_tag = "AVAILABLE" if avail > 0 else "FULL"
        print(f"\n  [{i}] {b.bus_name}  ({b.bus_number})  |  {b.bus_type}")
        print(f"       Departs: {s.departure_time}  Arrives: {s.arrival_time}")
        print(f"       Fare: ₹{r['fare']:.2f}   Seats Available: {avail}  [{status_tag}]")
        print(f"       Amenities: {', '.join(b.amenities) if b.amenities else 'None'}")
        print(f"       Rating: {b.average_rating()}★   Schedule ID: {s.schedule_id[:12]}")
        print_separator()
    return len(results)


def list_schedules():
    """Admin: display all schedules."""
    print_header("ALL SCHEDULES")
    schedules = get_all_schedules()
    if not schedules:
        print_error("No schedules found.")
        press_enter()
        return

    rows = []
    for s in schedules:
        bus   = bus_manager.get_bus_by_id(s.bus_id)
        route = route_manager.get_route_by_id(s.route_id)
        if not bus or not route:
            continue
        total = bus.total_seats
        rows.append([
            s.schedule_id[:8],
            f"{route.source[:10]} →",
            route.destination[:10],
            format_date(s.journey_date),
            s.departure_time,
            f"{len(s.booked_seats)}/{total}",
            s.status[:8]
        ])
    print_table(
        ["ID", "From", "To", "Date", "Depart", "Seats", "Status"],
        rows
    )
    press_enter()


def _select_schedule() -> Schedule:
    schedules = get_all_schedules(future_only=False)
    if not schedules:
        print_error("No schedules available.")
        press_enter()
        return None
    def label(s):
        bus   = bus_manager.get_bus_by_id(s.bus_id)
        route = route_manager.get_route_by_id(s.route_id)
        bname = bus.bus_name if bus else s.bus_id
        route_str = f"{route.source} → {route.destination}" if route else s.route_id
        return f"{route_str}  |  {s.journey_date}  {s.departure_time}  |  {s.status[:8]}"
    return select_from_list(schedules, display_fn=label, prompt="Select Schedule")


def _has_conflict(bus_id: str, journey_date: str, dep_time: str, arr_time: str) -> bool:
    """Check if a bus is already booked on the same date at overlapping times."""
    schedules = storage.load("schedules")
    for s in schedules:
        if s["bus_id"] != bus_id:
            continue
        if s["journey_date"] != journey_date:
            continue
        if s["status"] == JourneyStatus.CANCELLED:
            continue
        # Simple overlap check: if departure falls within existing journey
        existing_dep = s["departure_time"]
        existing_arr = s["arrival_time"]
        # If new dep < existing arr AND new arr > existing dep → overlap
        if dep_time < existing_arr and arr_time > existing_dep:
            return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN SCHEDULE MENU
# ─────────────────────────────────────────────────────────────────────────────

def schedule_management_menu():
    while True:
        print_header("SCHEDULE MANAGEMENT")
        print("  1. Add Single Schedule")
        print("  2. Add Recurring Schedules")
        print("  3. Cancel a Schedule")
        print("  4. View All Schedules")
        print("  0. Back")
        choice = get_menu_choice(4)
        if choice == 1:
            add_schedule()
        elif choice == 2:
            add_recurring_schedules()
        elif choice == 3:
            cancel_schedule()
        elif choice == 4:
            list_schedules()
        elif choice == 0:
            break
