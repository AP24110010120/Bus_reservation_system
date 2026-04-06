"""
utils.py
--------
Utility functions for console formatting, input validation,
date/time helpers, and display helpers.
"""

import re
import os
import sys
from datetime import datetime, date, timedelta
from typing import Any, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# CONSOLE DISPLAY HELPERS
# ─────────────────────────────────────────────────────────────────────────────

WIDTH = 70  # console width for borders

def clear_screen():
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title: str):
    """Print a prominent section header."""
    print()
    print("═" * WIDTH)
    padding = (WIDTH - len(title) - 2) // 2
    print(f"{'═' * padding} {title} {'═' * (WIDTH - padding - len(title) - 2)}")
    print("═" * WIDTH)


def print_subheader(title: str):
    """Print a sub-section header."""
    print()
    print("─" * WIDTH)
    print(f"  {title}")
    print("─" * WIDTH)


def print_separator():
    print("─" * WIDTH)


def print_double_separator():
    print("═" * WIDTH)


def print_success(msg: str):
    print(f"\n  ✔  {msg}")


def print_error(msg: str):
    print(f"\n  ✘  {msg}")


def print_warning(msg: str):
    print(f"\n  ⚠  {msg}")


def print_info(msg: str):
    print(f"\n  ℹ  {msg}")


def print_table(headers: List[str], rows: List[List[Any]], col_widths: Optional[List[int]] = None):
    """
    Print a formatted table with headers and rows.
    Automatically sizes columns if col_widths not provided.
    """
    if not rows and not headers:
        return

    if col_widths is None:
        col_widths = [len(str(h)) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))

    # Ensure max total width doesn't exceed console
    total = sum(col_widths) + len(col_widths) * 3 + 1
    while total > WIDTH and any(w > 8 for w in col_widths):
        max_idx = col_widths.index(max(col_widths))
        col_widths[max_idx] -= 1
        total -= 1

    sep = "+"
    for w in col_widths:
        sep += "-" * (w + 2) + "+"

    print(sep)
    header_row = "|"
    for h, w in zip(headers, col_widths):
        header_row += f" {str(h)[:w].ljust(w)} |"
    print(header_row)
    print(sep)

    for row in rows:
        line = "|"
        for i, (cell, w) in enumerate(zip(row, col_widths)):
            cell_str = str(cell)[:w]
            line += f" {cell_str.ljust(w)} |"
        print(line)
    print(sep)


def paginate(items: list, page_size: int = 10) -> list:
    """Paginate a list, prompting user to navigate pages. Returns current page."""
    if not items:
        return []
    total = len(items)
    pages = (total + page_size - 1) // page_size
    page = 0
    while True:
        start = page * page_size
        end   = min(start + page_size, total)
        for item in items[start:end]:
            print(item)
        print(f"\n  Page {page + 1}/{pages}  |  Showing {start+1}–{end} of {total}")
        if pages == 1:
            break
        nav = input("  [N]ext  [P]rev  [Q]uit  → ").strip().lower()
        if nav == "n" and page < pages - 1:
            page += 1
        elif nav == "p" and page > 0:
            page -= 1
        elif nav == "q":
            break
    return items


def print_ticket_box(lines: List[str]):
    """Print lines inside a decorative ticket border."""
    inner_width = WIDTH - 4
    print("┌" + "─" * (WIDTH - 2) + "┐")
    for line in lines:
        print(f"│  {str(line):<{inner_width}}  │")
    print("└" + "─" * (WIDTH - 2) + "┘")


def print_seat_layout(total_seats: int, booked_seats: List[str], bus_type: str):
    """
    Render a visual seat map in the console.
    Supports different layouts for sleeper vs seater.
    """
    print()
    print_subheader("SEAT MAP")
    print("  [A] = Available   [X] = Booked   [=] = Aisle\n")

    cols = 4  # seats per row (2+2 arrangement)
    if "Sleeper" in bus_type:
        cols = 3  # 1+2 for sleeper

    rows = (total_seats + cols - 1) // cols
    seat_num = 1

    for r in range(rows):
        line = "  "
        for c in range(cols):
            if seat_num > total_seats:
                line += "    "
            else:
                seat_str = str(seat_num)
                tag = "X" if seat_str in booked_seats else "A"
                line += f"[{seat_str:>2}{tag}]"
            seat_num += 1
            if c == 1 and cols == 4:   # aisle after 2nd seat
                line += " = "
            elif c == 0 and cols == 3: # aisle after 1st seat
                line += " = "
        print(line)
    print()


# ─────────────────────────────────────────────────────────────────────────────
# INPUT VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

def get_input(prompt: str, allow_empty: bool = False) -> str:
    """Prompt user for input, re-prompting if empty (unless allowed)."""
    while True:
        value = input(f"  {prompt}: ").strip()
        if value or allow_empty:
            return value
        print("  Input cannot be empty. Please try again.")


def get_int_input(prompt: str, min_val: int = None, max_val: int = None) -> int:
    """Prompt for an integer with optional range validation."""
    while True:
        try:
            value = int(input(f"  {prompt}: ").strip())
            if min_val is not None and value < min_val:
                print(f"  Please enter a value ≥ {min_val}")
                continue
            if max_val is not None and value > max_val:
                print(f"  Please enter a value ≤ {max_val}")
                continue
            return value
        except ValueError:
            print("  Invalid input. Please enter a whole number.")


def get_float_input(prompt: str, min_val: float = 0.0) -> float:
    """Prompt for a float value."""
    while True:
        try:
            value = float(input(f"  {prompt}: ").strip())
            if value < min_val:
                print(f"  Please enter a value ≥ {min_val}")
                continue
            return value
        except ValueError:
            print("  Invalid input. Please enter a decimal number.")


def get_choice(prompt: str, choices: List[str]) -> str:
    """Prompt user to pick from a list of choices (case-insensitive)."""
    choices_lower = [c.lower() for c in choices]
    while True:
        value = input(f"  {prompt} [{'/'.join(choices)}]: ").strip().lower()
        if value in choices_lower:
            return choices[choices_lower.index(value)]
        print(f"  Invalid choice. Options: {', '.join(choices)}")


def get_menu_choice(max_option: int) -> int:
    """Get a menu selection between 0 and max_option."""
    while True:
        try:
            choice = int(input("\n  Enter your choice: ").strip())
            if 0 <= choice <= max_option:
                return choice
            print(f"  Please enter a number between 0 and {max_option}.")
        except ValueError:
            print("  Invalid input. Please enter a number.")


def confirm(prompt: str = "Are you sure?") -> bool:
    """Ask for Y/N confirmation."""
    answer = input(f"\n  {prompt} [Y/N]: ").strip().upper()
    return answer == "Y"


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATION FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def validate_phone(phone: str) -> bool:
    """Validate a 10-digit Indian phone number."""
    return bool(re.match(r"^[6-9]\d{9}$", phone))


def validate_email(email: str) -> bool:
    """Validate email format."""
    return bool(re.match(r"^[\w.\-+]+@[\w\-]+\.[a-zA-Z]{2,}$", email))


def validate_date(date_str: str) -> bool:
    """Validate YYYY-MM-DD date format."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_time(time_str: str) -> bool:
    """Validate HH:MM time format."""
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False


def validate_future_date(date_str: str) -> bool:
    """Ensure date is today or in the future."""
    if not validate_date(date_str):
        return False
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    return d >= date.today()


def get_valid_phone(prompt: str = "Phone Number (10 digits)") -> str:
    """Prompt until a valid phone number is entered."""
    while True:
        phone = get_input(prompt)
        if validate_phone(phone):
            return phone
        print("  Invalid phone number. Must be 10 digits starting with 6-9.")


def get_valid_email(prompt: str = "Email Address") -> str:
    """Prompt until a valid email is entered."""
    while True:
        email = get_input(prompt)
        if validate_email(email):
            return email
        print("  Invalid email format. Example: user@example.com")


def get_valid_date(prompt: str = "Date (YYYY-MM-DD)", future_only: bool = False) -> str:
    """Prompt until a valid date is entered."""
    while True:
        d = get_input(prompt)
        if future_only:
            if validate_future_date(d):
                return d
            print("  Date must be today or a future date (YYYY-MM-DD).")
        else:
            if validate_date(d):
                return d
            print("  Invalid date format. Use YYYY-MM-DD.")


def get_valid_time(prompt: str = "Time (HH:MM)") -> str:
    """Prompt until a valid time is entered."""
    while True:
        t = get_input(prompt)
        if validate_time(t):
            return t
        print("  Invalid time format. Use HH:MM (24-hour).")


# ─────────────────────────────────────────────────────────────────────────────
# DATE / TIME UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def today_str() -> str:
    return date.today().strftime("%Y-%m-%d")


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_datetime(dt_str: str) -> str:
    """Format ISO datetime string to human-readable."""
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return dt_str


def format_date(date_str: str) -> str:
    """Format YYYY-MM-DD to human-readable."""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return d.strftime("%d %b %Y")
    except Exception:
        return date_str


def minutes_to_hhmm(minutes: int) -> str:
    """Convert total minutes to HH:MM string."""
    h = minutes // 60
    m = minutes % 60
    return f"{h}h {m:02d}m"


def get_week_range(ref_date: str = None) -> Tuple[str, str]:
    """Return start and end of the week containing ref_date."""
    d = datetime.strptime(ref_date, "%Y-%m-%d").date() if ref_date else date.today()
    start = d - timedelta(days=d.weekday())
    end   = start + timedelta(days=6)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def get_month_range(year: int = None, month: int = None) -> Tuple[str, str]:
    """Return start and end of a given month."""
    today = date.today()
    y = year or today.year
    m = month or today.month
    start = date(y, m, 1)
    if m == 12:
        end = date(y + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(y, m + 1, 1) - timedelta(days=1)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


# ─────────────────────────────────────────────────────────────────────────────
# MISC UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def press_enter():
    """Pause and wait for user to press Enter."""
    input("\n  Press ENTER to continue...")


def format_currency(amount: float) -> str:
    """Format amount as Indian Rupees."""
    return f"₹{amount:,.2f}"


def truncate(text: str, max_len: int) -> str:
    """Truncate a string with ellipsis."""
    return text[:max_len - 3] + "..." if len(text) > max_len else text


def capitalize_words(text: str) -> str:
    return " ".join(w.capitalize() for w in text.split())


def select_from_list(items: List[Any], display_fn=None, prompt: str = "Select") -> Optional[Any]:
    """
    Display a numbered list and let the user pick one.
    display_fn(item) is called to format each item for display.
    Returns the selected item or None if cancelled.
    """
    if not items:
        print_error("No items to select from.")
        return None
    for i, item in enumerate(items, 1):
        label = display_fn(item) if display_fn else str(item)
        print(f"  {i:>3}. {label}")
    print(f"  {0:>3}. Cancel / Go Back")
    choice = get_int_input(prompt, min_val=0, max_val=len(items))
    if choice == 0:
        return None
    return items[choice - 1]


def print_banner():
    """Print the application banner."""
    clear_screen()
    print()
    print("  " + "═" * (WIDTH - 4))
    print()
    print("        ██████╗ ██╗   ██╗███████╗    ██████╗ ███████╗███████╗")
    print("        ██╔══██╗██║   ██║██╔════╝    ██╔══██╗██╔════╝██╔════╝")
    print("        ██████╔╝██║   ██║███████╗    ██████╔╝█████╗  ███████╗")
    print("        ██╔══██╗██║   ██║╚════██║    ██╔══██╗██╔══╝  ╚════██║")
    print("        ██████╔╝╚██████╔╝███████║    ██║  ██║███████╗███████║")
    print("        ╚═════╝  ╚═════╝ ╚══════╝    ╚═╝  ╚═╝╚══════╝╚══════╝")
    print()
    print("              R E S E R V A T I O N   S Y S T E M")
    print("                  Version 1.0  |  Python Console")
    print()
    print("  " + "═" * (WIDTH - 4))
    print()
