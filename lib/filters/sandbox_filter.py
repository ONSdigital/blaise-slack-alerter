from lib.log_processor import ProcessedLogEntry


def sandbox_filter(log_entry: ProcessedLogEntry) -> bool:
    if log_entry.data["resource"]["labels"]["project_id"] == "ons-blaise-v2-dev-jw09":
        return True
    return False
