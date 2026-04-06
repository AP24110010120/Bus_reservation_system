"""
storage.py
----------
Handles all data persistence using JSON files.
Provides a clean interface for load/save operations.
"""

import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional

# ─────────────────────────────────────────────────────────────────────────────
# FILE PATHS
# ─────────────────────────────────────────────────────────────────────────────

DATA_DIR     = os.path.join(os.path.dirname(__file__), "data")
BACKUP_DIR   = os.path.join(os.path.dirname(__file__), "backups")

FILES = {
    "buses"         : os.path.join(DATA_DIR, "buses.json"),
    "routes"        : os.path.join(DATA_DIR, "routes.json"),
    "schedules"     : os.path.join(DATA_DIR, "schedules.json"),
    "passengers"    : os.path.join(DATA_DIR, "passengers.json"),
    "bookings"      : os.path.join(DATA_DIR, "bookings.json"),
    "cancellations" : os.path.join(DATA_DIR, "cancellations.json"),
    "promo_codes"   : os.path.join(DATA_DIR, "promo_codes.json"),
    "feedback"      : os.path.join(DATA_DIR, "feedback.json"),
    "audit_logs"    : os.path.join(DATA_DIR, "audit_logs.json"),
    "admins"        : os.path.join(DATA_DIR, "admins.json"),
}


def ensure_data_dir():
    """Create data and backup directories if they don't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)


def load(entity: str) -> List[dict]:
    """Load a list of records from a JSON file."""
    ensure_data_dir()
    path = FILES.get(entity)
    if not path:
        raise ValueError(f"Unknown entity: {entity}")
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def save(entity: str, records: List[dict]) -> bool:
    """Save a list of records to a JSON file."""
    ensure_data_dir()
    path = FILES.get(entity)
    if not path:
        raise ValueError(f"Unknown entity: {entity}")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"  [ERROR] Failed to save {entity}: {e}")
        return False


def find_by_id(entity: str, id_field: str, id_value: str) -> Optional[dict]:
    """Find a single record by its ID field."""
    records = load(entity)
    for record in records:
        if record.get(id_field) == id_value:
            return record
    return None


def find_all(entity: str, **filters) -> List[dict]:
    """Find all records matching given field=value filters."""
    records = load(entity)
    result = []
    for record in records:
        match = all(record.get(k) == v for k, v in filters.items())
        if match:
            result.append(record)
    return result


def upsert(entity: str, id_field: str, record: dict) -> bool:
    """Insert or update a record identified by id_field."""
    records = load(entity)
    for i, r in enumerate(records):
        if r.get(id_field) == record.get(id_field):
            records[i] = record
            return save(entity, records)
    records.append(record)
    return save(entity, records)


def delete_by_id(entity: str, id_field: str, id_value: str) -> bool:
    """Delete a record by its ID."""
    records = load(entity)
    new_records = [r for r in records if r.get(id_field) != id_value]
    if len(new_records) == len(records):
        return False  # not found
    return save(entity, new_records)


def backup_all():
    """Create a timestamped backup of all data files."""
    ensure_data_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}")
    os.makedirs(backup_path, exist_ok=True)
    count = 0
    for name, path in FILES.items():
        if os.path.exists(path):
            shutil.copy2(path, os.path.join(backup_path, f"{name}.json"))
            count += 1
    return backup_path, count


def restore_backup(backup_folder: str) -> bool:
    """Restore data from a backup folder."""
    if not os.path.isdir(backup_folder):
        return False
    ensure_data_dir()
    for name in FILES:
        src = os.path.join(backup_folder, f"{name}.json")
        if os.path.exists(src):
            shutil.copy2(src, FILES[name])
    return True


def list_backups() -> List[str]:
    """Return list of available backup folder names sorted by newest first."""
    if not os.path.exists(BACKUP_DIR):
        return []
    folders = [
        f for f in os.listdir(BACKUP_DIR)
        if os.path.isdir(os.path.join(BACKUP_DIR, f))
    ]
    return sorted(folders, reverse=True)


def get_data_stats() -> dict:
    """Return record counts for all entities."""
    stats = {}
    for name in FILES:
        records = load(name)
        stats[name] = len(records)
    return stats
