"""
models.py
---------
Core data models for the Bus Reservation System.
All entities are represented as dataclasses with validation.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime
import uuid


# ─────────────────────────────────────────────────────────────────────────────
# ENUMERATIONS (simulated with constants for broad Python 3 compatibility)
# ─────────────────────────────────────────────────────────────────────────────

class BusType:
    AC_SLEEPER       = "AC Sleeper"
    NON_AC_SLEEPER   = "Non-AC Sleeper"
    AC_SEMI_SLEEPER  = "AC Semi-Sleeper"
    AC_SEATER        = "AC Seater"
    NON_AC_SEATER    = "Non-AC Seater"
    LUXURY           = "Luxury"
    ALL = [AC_SLEEPER, NON_AC_SLEEPER, AC_SEMI_SLEEPER, AC_SEATER, NON_AC_SEATER, LUXURY]


class SeatType:
    WINDOW = "Window"
    AISLE  = "Aisle"
    MIDDLE = "Middle"
    LOWER  = "Lower"
    UPPER  = "Upper"


class BookingStatus:
    CONFIRMED  = "Confirmed"
    CANCELLED  = "Cancelled"
    WAITLISTED = "Waitlisted"
    COMPLETED  = "Completed"


class JourneyStatus:
    UPCOMING   = "Upcoming"
    ACTIVE     = "Active"
    COMPLETED  = "Completed"
    CANCELLED  = "Cancelled"


class Gender:
    MALE   = "Male"
    FEMALE = "Female"
    OTHER  = "Other"


# ─────────────────────────────────────────────────────────────────────────────
# BUS MODEL
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Bus:
    """Represents a physical bus with its properties."""
    bus_id: str
    bus_number: str          # e.g. "TN01AB1234"
    bus_name: str            # e.g. "Sri Travels Volvo"
    bus_type: str            # BusType constant
    total_seats: int
    amenities: List[str]     # ["WiFi", "AC", "USB Charging", ...]
    is_active: bool = True
    operator_name: str = ""
    rating: float = 0.0
    total_ratings: int = 0

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict) -> "Bus":
        return cls(**data)

    def average_rating(self) -> float:
        if self.total_ratings == 0:
            return 0.0
        return round(self.rating / self.total_ratings, 1)


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE MODEL
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Stop:
    """A stop on a route with its arrival/departure offset in minutes."""
    name: str
    distance_from_origin: float   # km
    arrival_offset: int           # minutes from journey start
    departure_offset: int         # minutes from journey start


@dataclass
class Route:
    """Represents a bus route with source, destination, and stops."""
    route_id: str
    source: str
    destination: str
    distance_km: float
    duration_minutes: int
    stops: List[dict]             # list of Stop dicts
    base_fare: float
    is_active: bool = True

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict) -> "Route":
        return cls(**data)

    def get_stop_names(self) -> List[str]:
        names = [self.source]
        names += [s["name"] for s in self.stops]
        names.append(self.destination)
        return names


# ─────────────────────────────────────────────────────────────────────────────
# SCHEDULE MODEL
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Schedule:
    """Links a Bus to a Route on a specific date/time."""
    schedule_id: str
    bus_id: str
    route_id: str
    journey_date: str         # "YYYY-MM-DD"
    departure_time: str       # "HH:MM"
    arrival_time: str         # "HH:MM"
    fare_multiplier: float    # for dynamic pricing
    booked_seats: List[str]   # seat numbers booked
    waitlist: List[str]       # passenger IDs on waitlist
    status: str = JourneyStatus.UPCOMING
    boarding_points: List[str] = field(default_factory=list)
    dropping_points: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict) -> "Schedule":
        return cls(**data)

    def available_seats(self, total_seats: int) -> int:
        return total_seats - len(self.booked_seats)

    def is_seat_available(self, seat_number: str) -> bool:
        return seat_number not in self.booked_seats

    def occupancy_rate(self, total_seats: int) -> float:
        if total_seats == 0:
            return 0.0
        return round(len(self.booked_seats) / total_seats * 100, 1)


# ─────────────────────────────────────────────────────────────────────────────
# PASSENGER MODEL
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Passenger:
    """Stores details of a registered passenger."""
    passenger_id: str
    name: str
    age: int
    gender: str
    phone: str
    email: str
    id_proof: str = ""       # Aadhaar, PAN, Passport number
    loyalty_points: int = 0
    booking_history: List[str] = field(default_factory=list)  # booking IDs
    created_at: str = ""

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict) -> "Passenger":
        return cls(**data)


# ─────────────────────────────────────────────────────────────────────────────
# BOOKING MODEL
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Booking:
    """Represents a confirmed seat booking."""
    booking_id: str
    ticket_id: str
    passenger_id: str
    schedule_id: str
    seat_numbers: List[str]
    fare: float
    boarding_point: str
    dropping_point: str
    status: str = BookingStatus.CONFIRMED
    promo_code: str = ""
    discount_amount: float = 0.0
    created_at: str = ""
    co_passengers: List[dict] = field(default_factory=list)  # [{name, age, gender, seat}]

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict) -> "Booking":
        return cls(**data)

    def net_fare(self) -> float:
        return self.fare - self.discount_amount


# ─────────────────────────────────────────────────────────────────────────────
# CANCELLATION MODEL
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Cancellation:
    """Records a booking cancellation with refund details."""
    cancellation_id: str
    booking_id: str
    cancelled_at: str
    original_fare: float
    cancellation_charge: float
    refund_amount: float
    reason: str = "User Requested"

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict) -> "Cancellation":
        return cls(**data)


# ─────────────────────────────────────────────────────────────────────────────
# PROMO CODE MODEL
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PromoCode:
    """Discount coupon with usage rules."""
    code: str
    discount_percent: float
    max_discount: float
    min_fare: float
    valid_until: str         # "YYYY-MM-DD"
    max_uses: int
    used_count: int = 0
    is_active: bool = True

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict) -> "PromoCode":
        return cls(**data)

    def is_valid(self, fare: float, today: str) -> bool:
        if not self.is_active:
            return False
        if self.used_count >= self.max_uses:
            return False
        if today > self.valid_until:
            return False
        if fare < self.min_fare:
            return False
        return True

    def calculate_discount(self, fare: float) -> float:
        discount = fare * (self.discount_percent / 100)
        return min(discount, self.max_discount)


# ─────────────────────────────────────────────────────────────────────────────
# FEEDBACK MODEL
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Feedback:
    """Post-trip rating and feedback from a passenger."""
    feedback_id: str
    booking_id: str
    bus_id: str
    passenger_id: str
    rating: int           # 1-5
    comment: str
    submitted_at: str

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict) -> "Feedback":
        return cls(**data)


# ─────────────────────────────────────────────────────────────────────────────
# AUDIT LOG MODEL
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AuditLog:
    """Records all admin actions for accountability."""
    log_id: str
    admin_id: str
    action: str
    details: str
    timestamp: str

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict) -> "AuditLog":
        return cls(**data)


def generate_id(prefix: str = "") -> str:
    """Generate a short unique ID with optional prefix."""
    uid = str(uuid.uuid4()).replace("-", "").upper()[:10]
    return f"{prefix}{uid}" if prefix else uid
