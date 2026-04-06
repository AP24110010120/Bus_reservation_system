"""
admin.py
--------
Admin authentication, admin management, audit logging,
promo code management, and admin dashboard.
"""

import hashlib
from models import AuditLog, PromoCode, generate_id
from utils import (
    print_header, print_subheader, print_success, print_error, print_warning,
    print_table, get_input, get_int_input, get_float_input,
    get_menu_choice, confirm, press_enter, now_str, today_str,
    format_datetime, format_currency, get_valid_date, select_from_list
)
import storage


# ─────────────────────────────────────────────────────────────────────────────
# PASSWORD HASHING
# ─────────────────────────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# AUTHENTICATION
# ─────────────────────────────────────────────────────────────────────────────

def admin_login() -> dict:
    """
    Authenticate admin. Returns admin record dict if successful, else None.
    Locks account after 3 failed attempts.
    """
    print_header("ADMIN LOGIN")
    admins = storage.load("admins")
    if not admins:
        print_warning("No admin accounts found. Creating default admin...")
        _create_default_admin()
        admins = storage.load("admins")

    username = get_input("Username")
    password = input("  Password: ")
    pw_hash  = _hash_password(password)

    for admin in admins:
        if admin["username"] == username:
            if admin.get("locked", False):
                print_error("Account is locked. Contact system administrator.")
                press_enter()
                return None
            if admin["password_hash"] == pw_hash:
                # Reset failed attempts
                admin["failed_attempts"] = 0
                storage.upsert("admins", "admin_id", admin)
                log_action(admin["admin_id"], "LOGIN", f"Admin '{username}' logged in.")
                print_success(f"Welcome, {admin.get('name', username)}!")
                press_enter()
                return admin
            else:
                admin["failed_attempts"] = admin.get("failed_attempts", 0) + 1
                if admin["failed_attempts"] >= 3:
                    admin["locked"] = True
                    print_error("Too many failed attempts. Account locked.")
                else:
                    remaining = 3 - admin["failed_attempts"]
                    print_error(f"Incorrect password. {remaining} attempt(s) remaining.")
                storage.upsert("admins", "admin_id", admin)
                press_enter()
                return None

    print_error("Admin username not found.")
    press_enter()
    return None


def _create_default_admin():
    """Create the default admin account on first run."""
    default = {
        "admin_id": generate_id("ADM"),
        "username": "admin",
        "password_hash": _hash_password("admin123"),
        "name": "System Administrator",
        "email": "admin@busres.com",
        "role": "superadmin",
        "failed_attempts": 0,
        "locked": False,
        "created_at": now_str()
    }
    storage.upsert("admins", "admin_id", default)
    print_info = lambda m: print(f"\n  ℹ  {m}")
    print_info("Default admin created. Username: admin | Password: admin123")
    print_info("Please change the password after first login.")


def change_admin_password(admin: dict):
    """Allow admin to change their own password."""
    print_header("CHANGE PASSWORD")
    current = input("  Current Password: ")
    if _hash_password(current) != admin["password_hash"]:
        print_error("Incorrect current password.")
        press_enter()
        return
    new_pw = input("  New Password: ")
    confirm_pw = input("  Confirm New Password: ")
    if new_pw != confirm_pw:
        print_error("Passwords do not match.")
        press_enter()
        return
    if len(new_pw) < 6:
        print_error("Password must be at least 6 characters.")
        press_enter()
        return
    admin["password_hash"] = _hash_password(new_pw)
    storage.upsert("admins", "admin_id", admin)
    log_action(admin["admin_id"], "PASSWORD_CHANGE", "Admin changed password.")
    print_success("Password changed successfully.")
    press_enter()


# ─────────────────────────────────────────────────────────────────────────────
# AUDIT LOG
# ─────────────────────────────────────────────────────────────────────────────

def log_action(admin_id: str, action: str, details: str):
    """Record an admin action in the audit log."""
    log = AuditLog(
        log_id    = generate_id("LOG"),
        admin_id  = admin_id,
        action    = action,
        details   = details,
        timestamp = now_str()
    )
    storage.upsert("audit_logs", "log_id", log.to_dict())


def view_audit_log():
    """Display recent audit log entries."""
    print_header("AUDIT LOG")
    records = storage.load("audit_logs")
    if not records:
        print_error("No audit log entries.")
        press_enter()
        return
    # Show most recent 50
    recent = sorted(records, key=lambda x: x["timestamp"], reverse=True)[:50]
    rows = [
        [r["log_id"][:8], r["action"][:20], r["details"][:35], format_datetime(r["timestamp"])[:16]]
        for r in recent
    ]
    print_table(["Log ID", "Action", "Details", "Timestamp"], rows)
    press_enter()


# ─────────────────────────────────────────────────────────────────────────────
# PROMO CODE MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

def add_promo_code():
    """Create a new promo code."""
    print_header("ADD PROMO CODE")
    code      = get_input("Promo Code (e.g. SAVE20)").upper()

    # Check duplicate
    existing = storage.load("promo_codes")
    if any(p["code"] == code for p in existing):
        print_error("Promo code already exists.")
        press_enter()
        return

    disc_pct  = get_float_input("Discount Percentage (e.g. 20 for 20%)", min_val=1)
    max_disc  = get_float_input("Maximum Discount Amount ₹", min_val=1)
    min_fare  = get_float_input("Minimum Fare to Apply ₹", min_val=0)
    valid_until = get_valid_date("Valid Until (YYYY-MM-DD)", future_only=True)
    max_uses    = get_int_input("Maximum number of uses", 1, 100000)

    promo = PromoCode(
        code             = code,
        discount_percent = disc_pct,
        max_discount     = max_disc,
        min_fare         = min_fare,
        valid_until      = valid_until,
        max_uses         = max_uses,
        used_count       = 0,
        is_active        = True
    )
    storage.upsert("promo_codes", "code", promo.to_dict())
    print_success(f"Promo code '{code}' created successfully.")
    press_enter()


def list_promo_codes():
    """Display all promo codes."""
    print_header("PROMO CODES")
    records = storage.load("promo_codes")
    if not records:
        print_error("No promo codes found.")
        press_enter()
        return
    rows = [
        [
            r["code"],
            f"{r['discount_percent']}%",
            format_currency(r["max_discount"]),
            format_currency(r["min_fare"]),
            r["valid_until"],
            f"{r['used_count']}/{r['max_uses']}",
            "Active" if r["is_active"] else "Inactive"
        ]
        for r in records
    ]
    print_table(
        ["Code", "Discount", "Max Off", "Min Fare", "Valid Until", "Uses", "Status"],
        rows
    )
    press_enter()


def deactivate_promo_code():
    """Deactivate a promo code."""
    print_header("DEACTIVATE PROMO CODE")
    records = storage.load("promo_codes")
    active = [PromoCode.from_dict(r) for r in records if r["is_active"]]
    if not active:
        print_error("No active promo codes.")
        press_enter()
        return
    promo = select_from_list(
        active,
        display_fn=lambda p: f"{p.code}  |  {p.discount_percent}%  |  Valid: {p.valid_until}",
        prompt="Select Code"
    )
    if promo and confirm(f"Deactivate '{promo.code}'?"):
        promo.is_active = False
        storage.upsert("promo_codes", "code", promo.to_dict())
        print_success("Promo code deactivated.")
    press_enter()


# ─────────────────────────────────────────────────────────────────────────────
# BACKUP & RESTORE
# ─────────────────────────────────────────────────────────────────────────────

def backup_data(admin: dict):
    """Create a timestamped backup of all data files."""
    print_header("BACKUP DATA")
    if confirm("Create a full data backup now?"):
        path, count = storage.backup_all()
        log_action(admin["admin_id"], "BACKUP", f"Backed up {count} files to {path}")
        print_success(f"Backup created: {path}  ({count} files)")
    press_enter()


def restore_data(admin: dict):
    """Restore from a backup."""
    print_header("RESTORE DATA")
    backups = storage.list_backups()
    if not backups:
        print_error("No backups available.")
        press_enter()
        return
    print("  Available Backups:")
    for i, b in enumerate(backups, 1):
        print(f"  {i:>3}. {b}")
    choice = get_int_input("Select backup (0 to cancel)", 0, len(backups))
    if choice == 0:
        return
    selected = backups[choice - 1]
    import os
    folder = os.path.join(storage.BACKUP_DIR, selected)
    if confirm(f"Restore from '{selected}'? Current data will be overwritten."):
        if storage.restore_backup(folder):
            log_action(admin["admin_id"], "RESTORE", f"Restored from backup: {selected}")
            print_success(f"Data restored from: {selected}")
        else:
            print_error("Restore failed.")
    press_enter()


# ─────────────────────────────────────────────────────────────────────────────
# FEEDBACK MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

def view_feedback():
    """Admin: view all trip feedback."""
    print_header("PASSENGER FEEDBACK")
    records = storage.load("feedback")
    if not records:
        print_error("No feedback submitted yet.")
        press_enter()
        return
    rows = []
    for f in records:
        import bus_manager as bm
        bus = bm.get_bus_by_id(f["bus_id"])
        rows.append([
            f["feedback_id"][:8],
            bus.bus_name[:15] if bus else "?",
            "★" * f["rating"] + "☆" * (5 - f["rating"]),
            f["comment"][:30],
            f["submitted_at"][:10]
        ])
    print_table(["ID", "Bus", "Rating", "Comment", "Date"], rows)
    press_enter()


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN MENU
# ─────────────────────────────────────────────────────────────────────────────

def admin_menu(admin: dict):
    """Main admin interface."""
    import bus_manager as bm
    import route_manager as rm
    import schedule_manager as sm
    import report_manager as rep
    import booking_manager as bkm
    import cancellation_manager as cxl
    import passenger as pax

    while True:
        rep.admin_dashboard_summary()
        print("  ─── MANAGEMENT ────────────────────────────────────")
        print("  1.  Bus Management")
        print("  2.  Route Management")
        print("  3.  Schedule Management")
        print("  4.  View All Bookings")
        print("  5.  View All Passengers")
        print("  6.  Cancellation Records")
        print("  ─── FINANCIAL ──────────────────────────────────────")
        print("  7.  Revenue Reports")
        print("  8.  Promo Codes")
        print("  ─── SYSTEM ─────────────────────────────────────────")
        print("  9.  View Audit Log")
        print(" 10.  View Feedback")
        print(" 11.  Backup Data")
        print(" 12.  Restore Data")
        print(" 13.  Change Password")
        print("  0.  Logout")
        choice = get_menu_choice(13)

        if choice == 1:
            log_action(admin["admin_id"], "BUS_MGMT", "Opened bus management")
            bm.bus_management_menu()
        elif choice == 2:
            log_action(admin["admin_id"], "ROUTE_MGMT", "Opened route management")
            rm.route_management_menu()
        elif choice == 3:
            log_action(admin["admin_id"], "SCHED_MGMT", "Opened schedule management")
            sm.schedule_management_menu()
        elif choice == 4:
            bkm.list_all_bookings()
        elif choice == 5:
            pax.list_all_passengers()
        elif choice == 6:
            cxl.list_cancellations()
        elif choice == 7:
            rep.report_menu()
        elif choice == 8:
            _promo_menu(admin)
        elif choice == 9:
            view_audit_log()
        elif choice == 10:
            view_feedback()
        elif choice == 11:
            backup_data(admin)
        elif choice == 12:
            restore_data(admin)
        elif choice == 13:
            change_admin_password(admin)
        elif choice == 0:
            log_action(admin["admin_id"], "LOGOUT", f"Admin '{admin['username']}' logged out.")
            print_success("Logged out successfully.")
            press_enter()
            break


def _promo_menu(admin: dict):
    while True:
        print_header("PROMO CODE MANAGEMENT")
        print("  1. Add Promo Code")
        print("  2. View All Promo Codes")
        print("  3. Deactivate Promo Code")
        print("  0. Back")
        choice = get_menu_choice(3)
        if choice == 1:
            add_promo_code()
            log_action(admin["admin_id"], "PROMO_ADD", "Added promo code")
        elif choice == 2:
            list_promo_codes()
        elif choice == 3:
            deactivate_promo_code()
            log_action(admin["admin_id"], "PROMO_DEACTIVATE", "Deactivated promo code")
        elif choice == 0:
            break
