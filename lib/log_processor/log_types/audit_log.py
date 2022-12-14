from typing import Optional

from lib.cloud_logging import LogEntry
from lib.log_processor import AppLogPayload


def attempt_create(entry: LogEntry) -> Optional[AppLogPayload]:
    if not isinstance(entry.payload, dict):
        return None

    if (
        "@type" not in entry.payload
        or entry.payload["@type"] != "type.googleapis.com/google.cloud.audit.AuditLog"
    ):
        return None

    message = "Unknown entry"
    if "status" in entry.payload and "message" in entry.payload["status"]:
        message = entry.payload["status"]["message"]

    return AppLogPayload(
        message=f"[AuditLog] {message}",
        data=entry.payload,
        platform=entry.resource_type,
        application="[unknown]",
        log_query={
            "protoPayload.@type": "type.googleapis.com/google.cloud.audit.AuditLog",
        },
        most_important_values=[
            "serviceName",
            "methodName",
            "requestMetadata.callerIp",
            "requestMetadata.callerSuppliedUserAgent",
            "requestMetadata.requestAttributes.path",
            "requestMetadata.requestAttributes.host",
            "requestMetadata.requestAttributes.time",
            "request.httpRequest.url",
        ],
    )
