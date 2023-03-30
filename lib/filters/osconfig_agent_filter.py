from lib.log_processor import ProcessedLogEntry


def osconfig_agent_filter(log_entry: ProcessedLogEntry):
    entry_data = log_entry.data
    print(log_entry)

    if log_entry.platform != "gce_instance":
        return False

    # TODO: Remove after BLAIS5-3705 concludes
    if (log_entry.message and "context deadline exceeded" in log_entry.message) or (
        type(entry_data) is dict
        and "description" in entry_data
        and "OSConfigAgent Error" in entry_data["description"]
        and "context deadline exceeded" in entry_data["description"]
    ):
        return True

    if (
        type(entry_data) is dict
        and "description" in entry_data
        and "OSConfigAgent Error" in entry_data["description"]
        and "unexpected end of JSON input" in entry_data["description"]
    ):
        return True

    return False
