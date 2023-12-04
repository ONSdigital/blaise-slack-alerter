import logging

from lib.log_processor import ProcessedLogEntry


def agent_connect_filter(log_entry: ProcessedLogEntry) -> bool:
    entry_data = log_entry.data

    if log_entry.platform != "gce_instance":
        return False

    if not isinstance(entry_data, dict) or "description" not in entry_data:
        return False

    if (
        "Agent connect error: The HTTP request timed out after 00:01:00.. Retrying until reconnected."
        not in entry_data["description"]
    ):
        return False

    logging.info(f"Skipping agent connect alert")
    return True
