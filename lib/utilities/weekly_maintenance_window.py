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

    This implementation correctly handles DST transitions by calculating the actual UTC times
    for the UK maintenance window on each specific Friday.
    """
    if not isinstance(timestamp, datetime):
        return False

    uk_tz = zoneinfo.ZoneInfo("Europe/London")

    # Convert input timestamp to UTC for comparison
    if timestamp.tzinfo is not None:
        utc_timestamp = timestamp.astimezone(timezone.utc)
    else:
        utc_timestamp = timestamp.replace(tzinfo=timezone.utc)

    # Convert to UK time to determine the day
    uk_timestamp = utc_timestamp.astimezone(uk_tz)

    # Check if it's Friday in UK time
    if uk_timestamp.weekday() != 4:  # 4 = Friday
        return False

    # Create UK maintenance window times for this specific date
    # This handles DST transitions correctly by using the actual date
    uk_date = uk_timestamp.date()

    # Create datetime objects for 01:25 and 01:35 UK time on this specific Friday
    maintenance_start_uk = datetime.combine(uk_date, time(13, 15)).replace(tzinfo=uk_tz)
    maintenance_end_uk = datetime.combine(uk_date, time(13, 35)).replace(tzinfo=uk_tz)

    # Convert UK maintenance times to UTC for accurate comparison
    maintenance_start_utc = maintenance_start_uk.astimezone(timezone.utc)
    maintenance_end_utc = maintenance_end_uk.astimezone(timezone.utc)

    return maintenance_start_utc <= utc_timestamp <= maintenance_end_utc
