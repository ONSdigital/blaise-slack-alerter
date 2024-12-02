import logging
from lib.log_processor import ProcessedLogEntry


def generic_not_found_filter(log_entry: ProcessedLogEntry) -> bool:

    if not isinstance(log_entry.severity, str):
        return False

    if not isinstance(log_entry.message, str):
        return False

    if log_entry.severity != "ERROR":
        return False

    if (
        'generic::not_found: Failed to fetch "latest' not in log_entry.message
        and 'generic::not_found: Failed to fetch "version_' not in log_entry.message
    ):
        return False

    logging.info(f"Skipping generic not found alert")
    return True
