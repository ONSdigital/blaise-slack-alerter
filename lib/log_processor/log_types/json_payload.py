from typing import Optional

from lib.cloud_logging import LogEntry, PayloadType
from lib.log_processor.app_log_payload import AppLogPayload


def attempt_create(entry: LogEntry) -> Optional[AppLogPayload]:
    if entry.payload_type is not PayloadType.JSON:
        return None

    return AppLogPayload(
        message="Unknown JSON Error",
        data=entry.payload,
        platform=entry.resource_type,
        application=None,
    )
