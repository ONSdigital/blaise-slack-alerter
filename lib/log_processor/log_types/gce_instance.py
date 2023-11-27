from copy import copy
from typing import Optional

from lib.cloud_logging import LogEntry
from lib.log_processor.app_log_payload import AppLogPayload


def attempt_create(entry: LogEntry) -> Optional[AppLogPayload]:
    if entry.resource_type != "gce_instance":
        return None

    if isinstance(entry.payload, str):
        return AppLogPayload(
            message=entry.payload,
            data="",
            platform="gce_instance",
            application="[unknown]",
        )

    message = "Unknown Error"

    log_query = {"resource.type": "gce_instance"}

    if "instance_id" in entry.resource_labels:
        log_query["resource.labels.instance_id"] = entry.resource_labels["instance_id"]

    if "message" in entry.payload:
        message = entry.payload["message"]

    data = copy(entry.payload)
    data.pop("message", None)
    data.pop("computer_name", None)

    return AppLogPayload(
        message=message,
        data=data,
        platform="gce_instance",
        application=application_name(entry),
        log_query=log_query,
        most_important_values=["description", "event_type"],
    )


def application_name(entry: LogEntry) -> str:
    if isinstance(entry.payload, str):
        return "[unknown]"

    if "computer_name" in entry.payload:
        return entry.payload["computer_name"]

    if "instance_name" in entry.labels:
        return entry.labels["instance_name"]

    if "instance_id" in entry.resource_labels:
        return entry.resource_labels["instance_id"]

    return "[unknown]"
