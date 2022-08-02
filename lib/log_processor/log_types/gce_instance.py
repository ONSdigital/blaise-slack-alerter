from copy import copy
from typing import Optional

from lib.cloud_logging import LogEntry, PayloadType
from lib.log_processor.app_log_payload import AppLogPayload


def attempt_create(entry: LogEntry) -> Optional[AppLogPayload]:
    if entry.payload_type is not PayloadType.JSON:
        return None

    if not isinstance(entry.payload, dict):
        return None

    if entry.resource_type != "gce_instance":
        return None

    if "message" not in entry.payload:
        return None

    if "computer_name" not in entry.payload:
        return None

    data = copy(entry.payload)
    del data["message"]
    del data["computer_name"]
    return AppLogPayload(
        message=entry.payload["message"],
        data=data,
        platform="gce_instance",
        application=entry.payload["computer_name"],
    )
