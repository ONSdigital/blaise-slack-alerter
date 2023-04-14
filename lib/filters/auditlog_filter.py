from lib.log_processor import ProcessedLogEntry


def auditlog_filter(log_entry: ProcessedLogEntry) -> bool:
    if type(log_entry.data) is not dict:
        return False

    if (
        log_entry.data.get("@type") == "type.googleapis.com/google.cloud.audit.AuditLog"
        and log_entry.data.get("methodName", "").startswith("storage.")
    ):
        return True

    return False

