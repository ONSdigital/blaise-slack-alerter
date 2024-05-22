import logging
from datetime import datetime, timedelta
from lib.log_processor import ProcessedLogEntry


def invalid_login_attempt_filter(log_entry: ProcessedLogEntry) -> bool:

    if not isinstance(log_entry.severity, str):
        return False

    if not isinstance(log_entry.message, str):
        return False

    if log_entry.severity != "ERROR":
        return False

    if 'Required "container.clusters.list" permission(s)' not in log_entry.message:
        return False

    logging.info(f"Skipping invalid login attempt alert")
    return True
