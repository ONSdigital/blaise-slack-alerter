import logging
from lib.log_processor import ProcessedLogEntry
from lib.utilities.weekly_maintenance_window import is_in_weekly_maintenance_window
from lib.utilities.log_validation import validate_log_entry_fields


def fluent_bit_maintenance_filter(log_entry: ProcessedLogEntry) -> bool:
    """
    Filter fluent-bit related errors during weekly maintenance windows.
    These errors are expected during VM maintenance when connections are disrupted.
    Activates only on Fridays around 01:30 AM UTC (1:00-2:00 AM window).
    """

    if log_entry is None:
        return False

    if not validate_log_entry_fields(
        log_entry,
        required_platform="gce_instance",
        require_message=True,
        require_timestamp=True,
    ):
        return False

    if not isinstance(log_entry.severity, str) or log_entry.severity != "ERROR":
        return False

    if not log_entry.timestamp or not is_in_weekly_maintenance_window(
        log_entry.timestamp
    ):
        return False

    if not (log_entry.log_name and "ops-agent-fluent-bit" in log_entry.log_name):
        return False

    fluent_bit_maintenance_indicators = [
        "[error] [C:\\work\\submodules\\fluent-bit\\src\\tls\\openssl.c:",
        "[error] [tls] syscall error:",
        "[error] [http_client] broken connection to logging.googleapis.com:",
        "No error",
        "DH lib",
        "broken connection",
    ]

    message_matches = any(
        indicator in log_entry.message
        for indicator in fluent_bit_maintenance_indicators
    )

    if message_matches:
        logging.info(
            f"Skipping fluent-bit maintenance error for {log_entry.application}"
        )
        return True

    return False
