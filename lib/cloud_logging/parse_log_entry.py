from typing import Dict, Any, Tuple, Optional, Union

from lib.cloud_logging.log_entry import LogEntry, PayloadType


def parse_log_entry(raw: Dict[str, Any]) -> LogEntry:
    payload_type, payload = parse_payload(raw)

    resource_type, resource_labels = parse_resource(raw)

    return LogEntry(
        resource_type=resource_type,
        resource_labels=resource_labels,
        payload_type=payload_type,
        payload=payload,
        severity=raw.get("severity"),
        log_name=raw.get("logName"),
        timestamp=raw.get("receiveTimestamp"),
    )


def parse_resource(raw: Dict[str, Any]) -> Tuple[Optional[str], Dict[str, str]]:
    resource_type = None
    resource_labels = dict()

    if "resource" in raw and isinstance(raw["resource"], dict):
        resource_type = raw["resource"].get("type")
        resource_labels = raw["resource"].get("labels", dict())

    return resource_type, resource_labels


def parse_payload(
    raw: Dict[str, Any]
) -> Tuple[PayloadType, Union[str, Dict[str, Any]]]:
    if "textPayload" in raw:
        return PayloadType.TEXT, raw["textPayload"]

    if "jsonPayload" in raw:
        return PayloadType.JSON, raw["jsonPayload"]

    if "protoPayload" in raw:
        return PayloadType.JSON, raw["protoPayload"]

    return PayloadType.NONE, raw
