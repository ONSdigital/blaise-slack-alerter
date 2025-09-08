import logging

from lib.log_processor import ProcessedLogEntry


def ip_space_exhausted_filter(log_entry: ProcessedLogEntry) -> bool:
    if not isinstance(log_entry.platform, str):
        return False

    if log_entry.platform != "gce_instance":
        return False

    if not isinstance(log_entry.message, str):
        return False

    if ("IP_SPACE_EXHAUSTED" or "ip_space_exhausted") not in log_entry.message:
        return False

    logging.info("Skipping ip space exhausted alert")
    return True
