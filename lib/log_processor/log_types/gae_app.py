from copy import copy
from typing import Optional, Any, Dict, Tuple, Union

from lib.cloud_logging import LogEntry, PayloadType
from lib.log_processor.app_log_payload import AppLogPayload


def attempt_create(entry: LogEntry) -> Optional[AppLogPayload]:
    if entry.resource_type != "gae_app":
        return None

    message = "Unknown error"
    data: Union[str, Dict[str, Any]] = ""

    if isinstance(entry.payload, str):
        message = entry.payload
    else:
        data = copy(entry.payload)

        data.pop("moduleId", None)

        if "message" in entry.payload:
            data.pop("message", None)
            message = entry.payload["message"]
        elif (
            "line" in entry.payload
            and isinstance(entry.payload["line"], list)
            and len(entry.payload["line"]) > 0
            and isinstance(entry.payload["line"][0], dict)
            and "logMessage" in entry.payload["line"][0]
        ):
            data.pop("line", None)
            message = entry.payload["line"][0]["logMessage"]

    application = entry.resource_labels.get("module_id", None)

    log_query = {"resource.type": "gae_app"}
    if application:
        log_query["resource.labels.module_id"] = application

    return AppLogPayload(
        message=message,
        data=data,
        platform="gae_app",
        application=application or "[unknown]",
        log_query=log_query,
        most_important_values=[
            "status",
            "host",
            "method",
            "resource",
            "ip",
            "latency",
            "responseSize",
            "httpVersion",
        ],
    )
