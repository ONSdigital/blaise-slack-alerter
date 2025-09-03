import logging
from lib.log_processor import ProcessedLogEntry


def get_role_filter(log_entry: ProcessedLogEntry) -> bool:

    if not isinstance(log_entry.severity, str):
        return False

    if not isinstance(log_entry.message, str):
        return False

    if log_entry.severity != "ERROR":
        return False

    if "You don't have permission to get the role at" not in log_entry.message:
        return False

    logging.info(f"Skipping get role alert")
    return True
