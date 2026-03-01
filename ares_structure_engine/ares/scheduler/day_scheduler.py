"""
ARES STRUCTURE ENGINE v1.0 — Day Scheduler

Automatically detects the day of the week and selects the appropriate content type.
Supports manual override via FORCE_DAY environment variable.
"""

import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from ares.utils.constants import CONTENT_SCHEDULE, CONTENT_LABELS_EN, TIMEZONE
from ares.utils.logger import get_logger

log = get_logger("ares.scheduler")


def get_today_info(force_day: int = None) -> dict:
    """
    Determine today's content type based on day of week.

    Args:
        force_day: Override day (1=Mon, 7=Sun). If None, uses env or auto-detect.

    Returns:
        {
            day_number: int (1-7),
            day_name: str,
            content_type: str,
            content_label: str,
            date_str: str (YYYY-MM-DD)
        }
    """
    # Check for override
    if force_day is None:
        env_day = os.getenv("FORCE_DAY", "").strip()
        if env_day:
            force_day = int(env_day)

    # Get current datetime in configured timezone
    try:
        tz = ZoneInfo(TIMEZONE)
    except Exception:
        tz = timezone.utc

    now = datetime.now(tz)

    if force_day is not None:
        day_number = max(1, min(7, force_day))
    else:
        day_number = now.isoweekday()  # Monday=1, Sunday=7

    day_names = {
        1: "Monday", 2: "Tuesday", 3: "Wednesday",
        4: "Thursday", 5: "Friday", 6: "Saturday", 7: "Sunday",
    }

    content_type = CONTENT_SCHEDULE[day_number]
    content_label = CONTENT_LABELS_EN[content_type]
    date_str = now.strftime("%Y-%m-%d")

    result = {
        "day_number": day_number,
        "day_name": day_names[day_number],
        "content_type": content_type,
        "content_label": content_label,
        "date_str": date_str,
    }

    log.info(
        f"Scheduler: Day {day_number} ({result['day_name']}) → "
        f"{content_label} [{content_type}]"
    )
    return result


def get_full_week_schedule() -> list:
    """Return the full 7-day content rotation schedule."""
    schedule = []
    for day in range(1, 8):
        ct = CONTENT_SCHEDULE[day]
        day_names = {
            1: "Monday", 2: "Tuesday", 3: "Wednesday",
            4: "Thursday", 5: "Friday", 6: "Saturday", 7: "Sunday",
        }
        schedule.append({
            "day_number": day,
            "day_name": day_names[day],
            "content_type": ct,
            "content_label": CONTENT_LABELS_EN[ct],
        })
    return schedule
