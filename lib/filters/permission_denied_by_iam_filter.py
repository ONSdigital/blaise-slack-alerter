import logging
from lib.log_processor import ProcessedLogEntry


def permission_denied_by_iam_filter(log_entry: ProcessedLogEntry) -> bool:

    if not isinstance(log_entry.severity, str):
        return False

    if not isinstance(log_entry.message, str):
        return False

    if log_entry.severity != "ERROR":
        return False

    if (
        log_entry is None
        or not isinstance(log_entry.data, dict)
        or not isinstance(log_entry.data.get("requestMetadata"), dict)
        or not isinstance(
            log_entry.data.get("requestMetadata", {}).get("callerSuppliedUserAgent"),
            str,
        )
        or "Fuzz Faster U Fool"
        not in log_entry.data.get("requestMetadata", {}).get(
            "callerSuppliedUserAgent", ""
        )
    ):
        return False

    if "[AuditLog] permission denied by IAM" not in log_entry.message:
        return False

    logging.info(f"Skipping permission denied by IAM alert")
    return True
