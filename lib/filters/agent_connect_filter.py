from lib.log_processor import ProcessedLogEntry


def agent_connect_filter(log_entry: ProcessedLogEntry) -> bool:
    entry_data = log_entry.data

    if log_entry.platform != "gce_instance":
        return False

    if (
        type(entry_data) is dict
        and "description" in entry_data
        and "Agent connect error" in entry_data["description"]
    ):
        return True

    return False
