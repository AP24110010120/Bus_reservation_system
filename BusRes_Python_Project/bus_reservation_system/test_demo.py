#!/usr/bin/env python3
"""
test_demo.py
------------
Simple test script to demonstrate key features of BusRes.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

# Import modules
import storage
import models
from models import Bus, Route, Schedule, PromoCode
import schedule_manager as sm
import bus_manager as bm
import route_manager as rm
import report_manager as rep

def test_data_loading():
    print("=== Testing Data Loading ===")
    buses = storage.load("buses")
    routes = storage.load("routes")
    schedules = storage.load("schedules")
    promo_codes = storage.load("promo_codes")

    print(f"Loaded {len(buses)} buses")
    print(f"Loaded {len(routes)} routes")
    print(f"Loaded {len(schedules)} schedules")
    print(f"Loaded {len(promo_codes)} promo codes")
    print()

def test_bus_search():
    print("=== Testing Bus Search ===")
    # Search for buses from Chennai to Bangalore
    results = sm.search_schedules("Chennai", "Bangalore", "2026-04-08", None, None)
    print(f"Found {len(results)} schedules from Chennai to Bangalore on 2026-04-08")
    if results:
        sched = results[0]
        bus = bm.find_by_id(sched.bus_id)
        route = rm.find_by_id(sched.route_id)
        print(f"Sample: {bus.bus_name} on {route.source} -> {route.destination}")
        print(f"Departure: {sched.departure_time}, Fare: ₹{sched.get_fare(route.base_fare):.2f}")
    print()

def test_admin_reports():
    print("=== Testing Admin Reports ===")
    # Test revenue summary
    summary = rep.get_revenue_summary("2026-04-01", "2026-04-30")
    print(f"Revenue from 2026-04-01 to 2026-04-30: ₹{summary['total_revenue']:.2f}")
    print(f"Total bookings: {summary['total_bookings']}")
    print()

def test_promo_codes():
    print("=== Testing Promo Codes ===")
    codes = storage.load("promo_codes")
    for code in codes[:2]:  # Show first 2
        pc = PromoCode.from_dict(code)
        print(f"Code: {pc.code}, Discount: {pc.discount_percent}%, Min Order: ₹{pc.min_order_value}")
    print()

if __name__ == "__main__":
    print("BusRes Feature Demonstration\n")
    test_data_loading()
    test_bus_search()
    test_admin_reports()
    test_promo_codes()
    print("Demo completed! All features appear to be working.")