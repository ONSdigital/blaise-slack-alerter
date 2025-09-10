from typing import Any, Dict, Optional, Tuple, Union

from lib.cloud_logging import LogEntry, PayloadType
from lib.log_processor.app_log_payload import AppLogPayload


def attempt_create(entry: LogEntry) -> Optional[AppLogPayload]:
    if entry.resource_type != "cloud_run_revision":
        return None

    message, data = get_message_and_data(entry)

    service_name = entry.resource_labels.get("service_name")
    log_query = {"resource.type": "cloud_run_revision"}

    if service_name:
        log_query["resource.labels.service_name"] = service_name

    return AppLogPayload(
        message=message,
        data=data,
        platform=entry.resource_type,
        application=service_name or "[unknown]",
        log_query=log_query,
    )


def get_message_and_data(entry: LogEntry) -> Tuple[str, Union[str, Dict[str, Any]]]:
    if entry.payload_type == PayloadType.JSON:
        return "Unknown Error (see data)", entry.payload

    if entry.payload_type == PayloadType.NONE:
        return "Unknown Error", ""

    return entry.payload if isinstance(entry.payload, str) else "", ""
