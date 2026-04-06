"""
report_manager.py
-----------------
Revenue reports: daily, weekly, monthly, total.
Route-wise and bus-wise analytics.
Occupancy rates, cancellation summaries, top routes.
"""

from datetime import datetime, date, timedelta
from typing import List, Dict
from utils import (
    print_header, print_subheader, print_success, print_error,
    print_table, print_separator, print_double_separator,
    get_menu_choice, press_enter, format_date, format_currency,
    get_valid_date, get_int_input, get_month_range, get_week_range, today_str
)
import storage
import bus_manager
import route_manager
import schedule_manager


# ─────────────────────────────────────────────────────────────────────────────
# CORE REVENUE AGGREGATION
# ─────────────────────────────────────────────────────────────────────────────

def _get_confirmed_bookings(start_date: str = None, end_date: str = None) -> list:
    """Return all confirmed (or completed) bookings within date range."""
    bookings = storage.load("bookings")
    result = []
    for b in bookings:
        if b["status"] not in ("Confirmed", "Completed"):
            continue
        if start_date or end_date:
            sched = schedule_manager.get_schedule_by_id(b["schedule_id"])
            if not sched:
                continue
            jdate = sched.journey_date
            if start_date and jdate < start_date:
                continue
            if end_date and jdate > end_date:
                continue
        result.append(b)
    return result


def _get_cancellations_in_range(start_date: str = None, end_date: str = None) -> list:
    """Return cancellations within date range (by cancellation date)."""
    records = storage.load("cancellations")
    result = []
    for c in records:
        c_date = c["cancelled_at"][:10]
        if start_date and c_date < start_date:
            continue
        if end_date and c_date > end_date:
            continue
        result.append(c)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# DAILY REPORT
# ─────────────────────────────────────────────────────────────────────────────

def daily_revenue_report(target_date: str = None):
    if not target_date:
        target_date = today_str()

    print_header(f"DAILY REVENUE REPORT — {format_date(target_date)}")
    bookings = _get_confirmed_bookings(target_date, target_date)
    cancels  = _get_cancellations_in_range(target_date, target_date)

    total_revenue   = sum(b["fare"] for b in bookings)
    total_tickets   = sum(len(b["seat_numbers"]) for b in bookings)
    total_bookings  = len(bookings)
    cancel_revenue  = sum(c["cancellation_charge"] for c in cancels)
    refund_amount   = sum(c["refund_amount"] for c in cancels)
    net_revenue     = total_revenue + cancel_revenue

    _print_summary_block(
        bookings=total_bookings,
        tickets=total_tickets,
        gross=total_revenue,
        cancel_charge=cancel_revenue,
        refunds=refund_amount,
        net=net_revenue,
        cancels=len(cancels)
    )
    press_enter()


# ─────────────────────────────────────────────────────────────────────────────
# WEEKLY REPORT
# ─────────────────────────────────────────────────────────────────────────────

def weekly_revenue_report():
    print_header("WEEKLY REVENUE REPORT")
    start, end = get_week_range()
    print(f"  Week: {format_date(start)} – {format_date(end)}\n")

    bookings = _get_confirmed_bookings(start, end)
    cancels  = _get_cancellations_in_range(start, end)

    # Group by day
    rows = []
    current = datetime.strptime(start, "%Y-%m-%d").date()
    end_date = datetime.strptime(end, "%Y-%m-%d").date()
    while current <= end_date:
        ds = current.strftime("%Y-%m-%d")
        day_bkgs = [b for b in bookings if _booking_journey_date(b) == ds]
        day_rev  = sum(b["fare"] for b in day_bkgs)
        day_tix  = sum(len(b["seat_numbers"]) for b in day_bkgs)
        rows.append([format_date(ds), len(day_bkgs), day_tix, format_currency(day_rev)])
        current += timedelta(days=1)

    print_table(["Date", "Bookings", "Tickets", "Revenue"], rows)

    total_revenue = sum(b["fare"] for b in bookings)
    cancel_charge = sum(c["cancellation_charge"] for c in cancels)
    _print_totals(len(bookings), total_revenue, cancel_charge, len(cancels))
    press_enter()


# ─────────────────────────────────────────────────────────────────────────────
# MONTHLY REPORT
# ─────────────────────────────────────────────────────────────────────────────

def monthly_revenue_report():
    print_header("MONTHLY REVENUE REPORT")
    today = date.today()
    year  = get_int_input(f"Year [{today.year}]", 2020, 2100) or today.year
    month = get_int_input(f"Month (1-12) [{today.month}]", 1, 12) or today.month

    # Fix: re-prompt since get_int_input doesn't support "blank = default"
    year_input  = input(f"  Year [{today.year}]: ").strip()
    month_input = input(f"  Month 1-12 [{today.month}]: ").strip()
    year  = int(year_input)  if year_input.isdigit()  else today.year
    month = int(month_input) if month_input.isdigit() else today.month

    start, end = get_month_range(year, month)
    print(f"\n  Period: {format_date(start)} – {format_date(end)}\n")

    bookings = _get_confirmed_bookings(start, end)
    cancels  = _get_cancellations_in_range(start, end)

    # Group by week
    rows = []
    week_start = datetime.strptime(start, "%Y-%m-%d").date()
    period_end = datetime.strptime(end, "%Y-%m-%d").date()
    wk = 1
    while week_start <= period_end:
        week_end = min(week_start + timedelta(days=6), period_end)
        ws = week_start.strftime("%Y-%m-%d")
        we = week_end.strftime("%Y-%m-%d")
        wk_bkgs = [b for b in bookings if ws <= _booking_journey_date(b) <= we]
        wk_rev  = sum(b["fare"] for b in wk_bkgs)
        wk_tix  = sum(len(b["seat_numbers"]) for b in wk_bkgs)
        rows.append([f"Week {wk}", f"{format_date(ws)}–{format_date(we)}", len(wk_bkgs), wk_tix, format_currency(wk_rev)])
        week_start += timedelta(days=7)
        wk += 1

    print_table(["Week", "Period", "Bookings", "Tickets", "Revenue"], rows)

    total_revenue = sum(b["fare"] for b in bookings)
    cancel_charge = sum(c["cancellation_charge"] for c in cancels)
    _print_totals(len(bookings), total_revenue, cancel_charge, len(cancels))
    press_enter()


# ─────────────────────────────────────────────────────────────────────────────
# TOTAL / ALL-TIME REPORT
# ─────────────────────────────────────────────────────────────────────────────

def total_revenue_report():
    print_header("TOTAL REVENUE REPORT — ALL TIME")
    bookings = _get_confirmed_bookings()
    cancels  = storage.load("cancellations")

    total_revenue = sum(b["fare"] for b in bookings)
    cancel_charge = sum(c["cancellation_charge"] for c in cancels)
    refunds       = sum(c["refund_amount"] for c in cancels)
    total_tickets = sum(len(b["seat_numbers"]) for b in bookings)
    net_revenue   = total_revenue + cancel_charge

    _print_summary_block(
        bookings=len(bookings),
        tickets=total_tickets,
        gross=total_revenue,
        cancel_charge=cancel_charge,
        refunds=refunds,
        net=net_revenue,
        cancels=len(cancels)
    )
    press_enter()


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE-WISE REPORT
# ─────────────────────────────────────────────────────────────────────────────

def route_revenue_report():
    print_header("REVENUE BY ROUTE")
    bookings = _get_confirmed_bookings()
    route_data: Dict[str, dict] = {}

    for b in bookings:
        sched = schedule_manager.get_schedule_by_id(b["schedule_id"])
        if not sched:
            continue
        route = route_manager.get_route_by_id(sched.route_id)
        if not route:
            continue
        key = f"{route.source} → {route.destination}"
        if key not in route_data:
            route_data[key] = {"revenue": 0.0, "tickets": 0, "bookings": 0}
        route_data[key]["revenue"]  += b["fare"]
        route_data[key]["tickets"]  += len(b["seat_numbers"])
        route_data[key]["bookings"] += 1

    if not route_data:
        print_error("No booking data available.")
        press_enter()
        return

    rows = sorted(route_data.items(), key=lambda x: x[1]["revenue"], reverse=True)
    table_rows = [
        [route, d["bookings"], d["tickets"], format_currency(d["revenue"])]
        for route, d in rows
    ]
    print_table(["Route", "Bookings", "Tickets", "Revenue"], table_rows)
    press_enter()


# ─────────────────────────────────────────────────────────────────────────────
# BUS-WISE REPORT
# ─────────────────────────────────────────────────────────────────────────────

def bus_revenue_report():
    print_header("REVENUE BY BUS")
    bookings = _get_confirmed_bookings()
    bus_data: Dict[str, dict] = {}

    for b in bookings:
        sched = schedule_manager.get_schedule_by_id(b["schedule_id"])
        if not sched:
            continue
        bus = bus_manager.get_bus_by_id(sched.bus_id)
        if not bus:
            continue
        key = bus.bus_name
        if key not in bus_data:
            bus_data[key] = {"revenue": 0.0, "tickets": 0, "bookings": 0, "bus_no": bus.bus_number}
        bus_data[key]["revenue"]  += b["fare"]
        bus_data[key]["tickets"]  += len(b["seat_numbers"])
        bus_data[key]["bookings"] += 1

    if not bus_data:
        print_error("No booking data available.")
        press_enter()
        return

    rows = sorted(bus_data.items(), key=lambda x: x[1]["revenue"], reverse=True)
    table_rows = [
        [name[:20], d["bus_no"], d["bookings"], d["tickets"], format_currency(d["revenue"])]
        for name, d in rows
    ]
    print_table(["Bus Name", "Reg No", "Bookings", "Tickets", "Revenue"], table_rows)
    press_enter()


# ─────────────────────────────────────────────────────────────────────────────
# OCCUPANCY REPORT
# ─────────────────────────────────────────────────────────────────────────────

def occupancy_report():
    print_header("BUS OCCUPANCY RATES")
    schedules = schedule_manager.get_all_schedules()
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
        total   = bus.total_seats
        booked  = len(s.booked_seats)
        occ_pct = s.occupancy_rate(total)
        bar = "█" * int(occ_pct / 10) + "░" * (10 - int(occ_pct / 10))
        rows.append([
            f"{route.source[:8]}→{route.destination[:8]}",
            format_date(s.journey_date),
            s.departure_time,
            f"{booked}/{total}",
            f"{bar} {occ_pct}%"
        ])
    print_table(["Route", "Date", "Depart", "Seats", "Occupancy"], rows)
    press_enter()


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN DASHBOARD SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

def admin_dashboard_summary():
    """Quick overview for admin home screen."""
    print_header("ADMIN DASHBOARD")
    stats  = storage.get_data_stats()
    today  = today_str()
    today_bookings = _get_confirmed_bookings(today, today)
    today_revenue  = sum(b["fare"] for b in today_bookings)
    all_bookings   = _get_confirmed_bookings()
    total_revenue  = sum(b["fare"] for b in all_bookings)
    cancels        = storage.load("cancellations")

    print(f"\n  {'BUSES':<22}: {stats.get('buses', 0)}")
    print(f"  {'ROUTES':<22}: {stats.get('routes', 0)}")
    print(f"  {'SCHEDULES':<22}: {stats.get('schedules', 0)}")
    print(f"  {'PASSENGERS':<22}: {stats.get('passengers', 0)}")
    print(f"  {'TOTAL BOOKINGS':<22}: {stats.get('bookings', 0)}")
    print(f"  {'CANCELLATIONS':<22}: {len(cancels)}")
    print_separator()
    print(f"  {'TODAY\'S BOOKINGS':<22}: {len(today_bookings)}")
    print(f"  {'TODAY\'S REVENUE':<22}: {format_currency(today_revenue)}")
    print(f"  {'ALL-TIME REVENUE':<22}: {format_currency(total_revenue)}")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# EXPORT
# ─────────────────────────────────────────────────────────────────────────────

def export_revenue_report():
    """Export revenue report to a text file."""
    import os
    print_header("EXPORT REVENUE REPORT")
    bookings  = _get_confirmed_bookings()
    cancels   = storage.load("cancellations")
    filename  = f"revenue_report_{today_str()}.txt"
    filepath  = os.path.join(os.path.dirname(__file__), filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"BUS RESERVATION SYSTEM — REVENUE REPORT\n")
        f.write(f"Generated: {today_str()}\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Total Bookings   : {len(bookings)}\n")
        f.write(f"Total Tickets    : {sum(len(b['seat_numbers']) for b in bookings)}\n")
        f.write(f"Gross Revenue    : {format_currency(sum(b['fare'] for b in bookings))}\n")
        f.write(f"Cancellations    : {len(cancels)}\n")
        f.write(f"Cancellation Fees: {format_currency(sum(c['cancellation_charge'] for c in cancels))}\n")
        f.write(f"Refunds          : {format_currency(sum(c['refund_amount'] for c in cancels))}\n")
        f.write(f"Net Revenue      : {format_currency(sum(b['fare'] for b in bookings) + sum(c['cancellation_charge'] for c in cancels))}\n")
        f.write("\n\nBOOKINGS LIST\n" + "-" * 60 + "\n")
        for b in bookings:
            sched = schedule_manager.get_schedule_by_id(b["schedule_id"])
            f.write(f"  {b['ticket_id']}  |  {sched.journey_date if sched else '?'}  |  {format_currency(b['fare'])}\n")

    print_success(f"Report exported to: {filepath}")
    press_enter()


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _booking_journey_date(booking: dict) -> str:
    sched = schedule_manager.get_schedule_by_id(booking["schedule_id"])
    return sched.journey_date if sched else ""


def _print_summary_block(bookings, tickets, gross, cancel_charge, refunds, net, cancels):
    print(f"\n  {'Total Bookings':<28}: {bookings}")
    print(f"  {'Total Tickets Sold':<28}: {tickets}")
    print(f"  {'Total Cancellations':<28}: {cancels}")
    print_separator()
    print(f"  {'Gross Revenue (fares)':<28}: {format_currency(gross)}")
    print(f"  {'Cancellation Fees Collected':<28}: {format_currency(cancel_charge)}")
    print(f"  {'Refunds Issued':<28}: {format_currency(refunds)}")
    print_separator()
    print(f"  {'NET INCOME':<28}: {format_currency(net)}")
    print()


def _print_totals(bookings, revenue, cancel_charge, cancels):
    print()
    print_separator()
    print(f"  Total Bookings    : {bookings}")
    print(f"  Total Cancels     : {cancels}")
    print(f"  Gross Revenue     : {format_currency(revenue)}")
    print(f"  Cancel Fees       : {format_currency(cancel_charge)}")
    print(f"  Net Revenue       : {format_currency(revenue + cancel_charge)}")


# ─────────────────────────────────────────────────────────────────────────────
# REPORT MENU
# ─────────────────────────────────────────────────────────────────────────────

def report_menu():
    while True:
        print_header("REVENUE & REPORTS")
        print("  1. Today's Revenue")
        print("  2. Weekly Revenue")
        print("  3. Monthly Revenue")
        print("  4. All-Time Revenue")
        print("  5. Revenue by Route")
        print("  6. Revenue by Bus")
        print("  7. Occupancy Report")
        print("  8. Export Report to File")
        print("  0. Back")
        choice = get_menu_choice(8)
        if choice == 1:
            daily_revenue_report()
        elif choice == 2:
            weekly_revenue_report()
        elif choice == 3:
            monthly_revenue_report()
        elif choice == 4:
            total_revenue_report()
        elif choice == 5:
            route_revenue_report()
        elif choice == 6:
            bus_revenue_report()
        elif choice == 7:
            occupancy_report()
        elif choice == 8:
            export_revenue_report()
        elif choice == 0:
            break
