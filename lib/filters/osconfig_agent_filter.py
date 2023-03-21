from lib.log_processor import ProcessedLogEntry


def osconfig_agent_filter(log_entry: ProcessedLogEntry):
    entry_data = log_entry.data

    # Skip "OSConfigAgent Error: unexpected end of JSON input" logs from GCE instances
    if log_entry.platform == "gce_instance":
        if (
            type(entry_data) is dict
            and "description" in entry_data
            and "OSConfigAgent Error" in entry_data["description"]
            and "unexpected end of JSON input" in entry_data["description"]
        ):
            return True
    return False
