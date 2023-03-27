from copy import copy
from typing import Optional

from lib.cloud_logging import LogEntry, PayloadType
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
    application = "[unknown]"

    log_query = {"resource.type": "gce_instance"}

    if "instance_id" in entry.resource_labels:
        application = entry.resource_labels["instance_id"]
        log_query["resource.labels.instance_id"] = entry.resource_labels["instance_id"]

    if "message" in entry.payload:
        message = entry.payload["message"]

    if "computer_name" in entry.payload:
        application = entry.payload["computer_name"]

    data = copy(entry.payload)
    data.pop("message", None)
    data.pop("computer_name", None)

    return AppLogPayload(
        message=message,
        data=data,
        platform="gce_instance",
        application=application,
        log_query=log_query,
        most_important_values=["description", "event_type"],
    )
