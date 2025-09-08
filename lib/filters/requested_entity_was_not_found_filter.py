import logging

from lib.log_processor import ProcessedLogEntry


def requested_entity_was_not_found_filter(log_entry: ProcessedLogEntry) -> bool:

    if not isinstance(log_entry.severity, str):
        return False

    if not isinstance(log_entry.message, str):
        return False

    if log_entry.severity != "ERROR":
        return False

    if "generic::not_found: Requested entity was not found." not in log_entry.message:
        return False

    logging.info("Skipping requested entity was not found alert")
    return True
