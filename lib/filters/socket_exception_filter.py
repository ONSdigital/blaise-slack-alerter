import logging
from lib.log_processor import ProcessedLogEntry


def socket_exception_filter(log_entry: ProcessedLogEntry) -> bool:

    if not isinstance(log_entry.severity, str):
        return False

    if not isinstance(log_entry.message, str):
        return False

    if log_entry.severity != "ERROR":
        return False

    if "Socket exception: Connection reset by peer (104)" not in log_entry.message:
        return False

    logging.info(f"Skipping socket exception alert")
    return True