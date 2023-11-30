from lib.log_processor import ProcessedLogEntry


def sandbox_filter(log_entry: ProcessedLogEntry) -> bool:
    if not log_entry.log_name:
        return False

    if "ons-blaise-v2-dev-jw09" in log_entry.log_name:
        return True
    return False
