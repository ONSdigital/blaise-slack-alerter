from datetime import datetime
from typing import Optional
from lib.log_processor import ProcessedLogEntry


def validate_log_entry_fields(
    log_entry: ProcessedLogEntry,
    required_platform: Optional[str] = None,
    require_message: bool = False,
    require_log_name: bool = False,
    require_timestamp: bool = False,
) -> bool:
    if required_platform is not None:
        if not isinstance(log_entry.platform, str):
            return False
        if log_entry.platform != required_platform:
            return False

    if require_message:
        if not isinstance(log_entry.message, str):
            return False

    if require_log_name:
        if not isinstance(log_entry.log_name, str):
            return False

    if require_timestamp:
        if not isinstance(log_entry.timestamp, datetime):
            return False

    return True


def validate_gce_instance_log_entry(log_entry: ProcessedLogEntry) -> bool:
    return validate_log_entry_fields(
        log_entry,
        required_platform="gce_instance",
        require_message=True,
        require_log_name=True,
        require_timestamp=True,
    )
