import logging

from lib.log_processor import ProcessedLogEntry


def auditlog_filter(log_entry: ProcessedLogEntry) -> bool:
    if not isinstance(log_entry.data, dict):
        return False

    if log_entry.data.get("@type") != "type.googleapis.com/google.cloud.audit.AuditLog":
        return False

    if not log_entry.data.get("methodName", "").startswith("storage."):
        return False

    logging.info("Skipping audit log alert")
    return True
