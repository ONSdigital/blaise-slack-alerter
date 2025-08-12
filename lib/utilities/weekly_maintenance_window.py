from datetime import datetime, time, timezone
import logging
import zoneinfo


def is_in_friday_maintenance_window(timestamp: datetime) -> bool:
    """
    Check if timestamp falls within weekly maintenance window for the production environment (Friday 01:25-01:35 UK time).
    During this window, GCP performs routine maintenance causing expected non-critical errors
    that should be filtered from alerts.

    The maintenance window is 01:25-01:35 UK time every Friday, which automatically handles:
    - GMT (winter): 01:25-01:35 UTC
    - BST (summer): 00:25-00:35 UTC
    """
    if not isinstance(timestamp, datetime):
        return False

    uk_tz = zoneinfo.ZoneInfo("Europe/London")

    if timestamp.tzinfo is not None:
        uk_timestamp = timestamp.astimezone(uk_tz)
    else:
        uk_timestamp = timestamp.replace(tzinfo=timezone.utc).astimezone(uk_tz)

    # Weekly maintenance window - Friday 01:25-01:35 UK time
    maintenance_start = time(14, 30)
    maintenance_end = time(15, 50)

    uk_time = uk_timestamp.time()
    uk_weekday = uk_timestamp.weekday()

    is_friday = uk_weekday == 4
    is_maintenance_time = maintenance_start <= uk_time <= maintenance_end

    return is_friday and is_maintenance_time
