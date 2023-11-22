from lib.log_processor import ProcessedLogEntry


def ip_space_exhausted_filter(log_entry: ProcessedLogEntry) -> bool:
    entry_data = log_entry.data

    if log_entry.platform != "gce_instance":
        return False

    if not isinstance(entry_data, dict) or "description" not in entry_data:
        return False

    if "IP_SPACE_EXHAUSTED" not in entry_data["description"]:
        return False

    return True
