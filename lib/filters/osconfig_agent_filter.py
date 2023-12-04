import logging

from lib.log_processor import ProcessedLogEntry


def osconfig_agent_filter(log_entry: ProcessedLogEntry) -> bool:
    if not isinstance(log_entry.platform, str):
        return False

    if log_entry.platform != "gce_instance":
        return False

    if not isinstance(log_entry.message, str):
        return False

    if "unexpected end of JSON input" not in log_entry.message:
        return False

    if not isinstance(log_entry.log_name, str):
        return False

    if (
        "OSConfigAgent Error" not in log_entry.message
        and "OSConfigAgent" not in log_entry.log_name
    ):
        return False

    logging.info(f"Skipping os config agent alert")
    return True
