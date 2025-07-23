from datetime import datetime, time, timezone


def is_in_weekly_maintenance_window(timestamp: datetime) -> bool:
    if not isinstance(timestamp, datetime):
        return False
    
    if timestamp.tzinfo is not None:
        utc_timestamp = timestamp.astimezone(timezone.utc)
    else:
        utc_timestamp = timestamp.replace(tzinfo=timezone.utc)
    
    # Weekly maintenance window - Friday around 01:30 AM UTC (±30 minutes)
    maintenance_start = time(1, 0) 
    maintenance_end = time(2, 0)   
    
    log_time = utc_timestamp.time()
    log_weekday = utc_timestamp.weekday()
    
    is_friday = log_weekday == 4
    is_maintenance_time = maintenance_start <= log_time <= maintenance_end
    
    return is_friday and is_maintenance_time
