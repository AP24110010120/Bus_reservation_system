"""
seed_data.py
------------
Loads sample data for demonstration and testing.
Run this once to populate buses, routes, schedules, and promo codes.
"""

import storage
from models import Bus, Route, Schedule, PromoCode, JourneyStatus, BusType, generate_id
from utils import today_str
from datetime import date, timedelta


def seed_all():
    """Insert all sample data. Skips if data already exists."""
    print("\n  Loading sample data...")
    _seed_buses()
    _seed_routes()
    _seed_schedules()
    _seed_promo_codes()
    print("  ✔  Sample data loaded.\n")


def _seed_buses():
    if storage.load("buses"):
        return  # already seeded

    buses = [
        Bus(
            bus_id="BUSVLV001", bus_number="TN01AB1234",
            bus_name="Sri Murugan Volvo AC", bus_type=BusType.AC_SLEEPER,
            total_seats=40, amenities=["AC", "WiFi", "USB Charging", "Blanket", "Reading Light"],
            operator_name="Sri Murugan Travels", is_active=True, rating=0.0, total_ratings=0
        ),
        Bus(
            bus_id="BUSSEM001", bus_number="TN02CD5678",
            bus_name="Parvathi Semi-Sleeper", bus_type=BusType.AC_SEMI_SLEEPER,
            total_seats=45, amenities=["AC", "USB Charging", "Entertainment System"],
            operator_name="Parvathi Travels", is_active=True, rating=0.0, total_ratings=0
        ),
        Bus(
            bus_id="BUSNAC001", bus_number="KA03EF9012",
            bus_name="Karnataka Express", bus_type=BusType.NON_AC_SEATER,
            total_seats=50, amenities=["Fan", "Drinking Water"],
            operator_name="KSR Travels", is_active=True, rating=0.0, total_ratings=0
        ),
        Bus(
            bus_id="BUSLUX001", bus_number="MH04GH3456",
            bus_name="Mumbai Luxury Liner", bus_type=BusType.LUXURY,
            total_seats=30, amenities=["AC", "WiFi", "Mini Bar", "Recliner Seats", "Live TV"],
            operator_name="Premium Rides Pvt Ltd", is_active=True, rating=0.0, total_ratings=0
        ),
        Bus(
            bus_id="BUSSLP001", bus_number="AP05IJ7890",
            bus_name="Coastal Non-AC Sleeper", bus_type=BusType.NON_AC_SLEEPER,
            total_seats=36, amenities=["Fan", "Curtains", "Drinking Water"],
            operator_name="Coastal Transport", is_active=True, rating=0.0, total_ratings=0
        ),
    ]
    for b in buses:
        storage.upsert("buses", "bus_id", b.to_dict())


def _seed_routes():
    if storage.load("routes"):
        return

    routes = [
        Route(
            route_id="RTECBE001", source="Chennai", destination="Bengaluru",
            distance_km=350, duration_minutes=360,
            stops=[
                {"name": "Vellore", "distance_from_origin": 120, "arrival_offset": 90, "departure_offset": 100},
                {"name": "Krishnagiri", "distance_from_origin": 220, "arrival_offset": 180, "departure_offset": 190},
            ],
            base_fare=450.0, is_active=True
        ),
        Route(
            route_id="RTECMB001", source="Chennai", destination="Mumbai",
            distance_km=1338, duration_minutes=1320,
            stops=[
                {"name": "Nellore",    "distance_from_origin": 175, "arrival_offset": 180, "departure_offset": 195},
                {"name": "Vijayawada", "distance_from_origin": 435, "arrival_offset": 480, "departure_offset": 500},
                {"name": "Hyderabad",  "distance_from_origin": 750, "arrival_offset": 780, "departure_offset": 810},
                {"name": "Pune",       "distance_from_origin": 1200, "arrival_offset": 1200, "departure_offset": 1215},
            ],
            base_fare=1200.0, is_active=True
        ),
        Route(
            route_id="RTECOK001", source="Bengaluru", destination="Kochi",
            distance_km=560, duration_minutes=540,
            stops=[
                {"name": "Mysuru",  "distance_from_origin": 140, "arrival_offset": 150, "departure_offset": 160},
                {"name": "Kozhikode", "distance_from_origin": 450, "arrival_offset": 420, "departure_offset": 435},
            ],
            base_fare=600.0, is_active=True
        ),
        Route(
            route_id="RTEHYD001", source="Hyderabad", destination="Bengaluru",
            distance_km=575, duration_minutes=570,
            stops=[
                {"name": "Kurnool",    "distance_from_origin": 200, "arrival_offset": 210, "departure_offset": 220},
                {"name": "Anantapur", "distance_from_origin": 380, "arrival_offset": 390, "departure_offset": 400},
            ],
            base_fare=700.0, is_active=True
        ),
        Route(
            route_id="RTEMUM001", source="Mumbai", destination="Pune",
            distance_km=150, duration_minutes=180,
            stops=[
                {"name": "Khopoli", "distance_from_origin": 80, "arrival_offset": 90, "departure_offset": 95},
            ],
            base_fare=250.0, is_active=True
        ),
    ]
    for r in routes:
        storage.upsert("routes", "route_id", r.to_dict())


def _seed_schedules():
    if storage.load("schedules"):
        return

    today = date.today()
    days = [today + timedelta(days=i) for i in range(7)]

    # Bus-Route assignments for seeding
    assignments = [
        # (bus_id, route_id, dep_time, arr_time, multiplier)
        ("BUSVLV001", "RTECBE001", "21:00", "03:00", 1.0),
        ("BUSSEM001", "RTECBE001", "22:30", "04:30", 0.9),
        ("BUSSLP001", "RTECBE001", "23:00", "05:00", 0.8),
        ("BUSLUX001", "RTECMB001", "18:00", "18:00", 1.5),
        ("BUSVLV001", "RTECMB001", "20:00", "20:00", 1.2),
        ("BUSSEM001", "RTECOK001", "19:00", "04:00", 1.0),
        ("BUSNAC001", "RTECOK001", "21:00", "06:00", 0.7),
        ("BUSNAC001", "RTEHYD001", "08:00", "17:30", 1.0),
        ("BUSVLV001", "RTEHYD001", "22:00", "07:30", 1.1),
        ("BUSSEM001", "RTEMUM001", "07:00", "10:00", 1.0),
        ("BUSNAC001", "RTEMUM001", "15:00", "18:00", 0.9),
    ]

    # Get route stop names for boarding/dropping
    routes_data = {r.route_id: r for r in [Route.from_dict(d) for d in storage.load("routes")]}

    sched_count = 0
    for d in days:
        jdate = d.strftime("%Y-%m-%d")
        for bus_id, route_id, dep, arr, mult in assignments:
            route = routes_data.get(route_id)
            if not route:
                continue
            stop_names = route.get_stop_names()
            # Pre-book a few seats for realism
            import random
            bus_seats_map = {
                "BUSVLV001": 40, "BUSSEM001": 45, "BUSNAC001": 50,
                "BUSLUX001": 30, "BUSSLP001": 36
            }
            total = bus_seats_map.get(bus_id, 40)
            pre_booked = random.randint(0, total // 3)
            booked_seats = [str(s) for s in random.sample(range(1, total + 1), min(pre_booked, total))]

            sched = Schedule(
                schedule_id     = generate_id("SCH"),
                bus_id          = bus_id,
                route_id        = route_id,
                journey_date    = jdate,
                departure_time  = dep,
                arrival_time    = arr,
                fare_multiplier = mult,
                booked_seats    = booked_seats,
                waitlist        = [],
                status          = JourneyStatus.UPCOMING,
                boarding_points = stop_names[:-1],
                dropping_points = stop_names[1:]
            )
            storage.upsert("schedules", "schedule_id", sched.to_dict())
            sched_count += 1


def _seed_promo_codes():
    if storage.load("promo_codes"):
        return

    future_date = (date.today() + timedelta(days=90)).strftime("%Y-%m-%d")
    codes = [
        PromoCode("WELCOME10", 10, 100,   0,   future_date, 1000, 0, True),
        PromoCode("SAVE20",    20, 200, 500,   future_date,  500, 0, True),
        PromoCode("FLAT50",     5,  50, 200,   future_date, 2000, 0, True),
        PromoCode("LUXURY30",  30, 500, 1000,  future_date,  100, 0, True),
    ]
    for c in codes:
        storage.upsert("promo_codes", "code", c.to_dict())


if __name__ == "__main__":
    seed_all()
    print("Sample data seeded successfully!")
