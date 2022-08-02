from typing import Dict, Any, Tuple, Optional, Union

from lib.cloud_logging.log_entry import LogEntry, PayloadType


def parse_log_entry(raw: Dict[str, Any]) -> LogEntry:
    payload_type, payload = parse_payload(raw)

    return LogEntry(
        resource_type=parse_resource_type(raw),
        payload_type=payload_type,
        payload=payload,
        severity=raw.get("severity"),
        log_name=raw.get("logName"),
        timestamp=raw.get("receiveTimestamp"),
    )


def parse_resource_type(raw: Dict[str, Any]) -> Optional[str]:
    resource_type = None
    if "resource" in raw and isinstance(raw["resource"], dict):
        resource_type = raw["resource"].get("type")
    return resource_type


def parse_payload(
    raw: Dict[str, Any]
) -> Tuple[PayloadType, Union[str, Dict[str, Any]]]:
    payload_type = PayloadType.NONE
    payload = raw
    if "textPayload" in raw:
        payload_type = PayloadType.TEXT
        payload = raw["textPayload"]
    elif "jsonPayload" in raw:
        payload_type = PayloadType.JSON
        payload = raw["jsonPayload"]
    return payload_type, payload
