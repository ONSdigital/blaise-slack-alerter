from typing import Optional

from lib.cloud_logging import LogEntry, PayloadType
from lib.log_processor.app_log_payload import AppLogPayload


def attempt_create(entry: LogEntry) -> Optional[AppLogPayload]:
    if entry.payload_type != PayloadType.TEXT:
        return None

    if not isinstance(entry.payload, str):
        return None

    return AppLogPayload(
        message=entry.payload, data={}, platform=entry.resource_type, application=None
    )
