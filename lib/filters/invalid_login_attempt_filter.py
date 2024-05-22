import logging
from datetime import datetime, timedelta
from lib.log_processor import ProcessedLogEntry

last_sent_alert = None


def invalid_login_attempt_filter(log_entry: ProcessedLogEntry) -> bool:

    global last_sent_alert
    timeout = 5

    if not isinstance(log_entry.severity, str):
        return False

    if not isinstance(log_entry.message, str):
        return False

    if log_entry.severity != "ERROR":
        return False

    if 'Required "container.clusters.list" permission(s)' not in log_entry.message:
        return False

    if last_sent_alert is None:
        last_sent_alert = datetime.now()
        return False

    if last_sent_alert <= datetime.now() - timedelta(minutes=timeout):
        last_sent_alert = datetime.now()
        return False

    logging.info(f"Skipping invalid login attempt alert")
    return True
