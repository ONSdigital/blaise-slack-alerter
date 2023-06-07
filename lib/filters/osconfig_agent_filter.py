from lib.log_processor import ProcessedLogEntry


def osconfig_agent_filter(log_entry: ProcessedLogEntry):
    entry_data = log_entry.data

    if log_entry.platform != "gce_instance":
        return False

    if not isinstance(entry_data, dict) or "description" not in entry_data:
        return False

    if (
        "OSConfigAgent Error" not in entry_data["description"]
        and "unexpected end of JSON input" not in entry_data["description"]
    ):
        return False

    return True
