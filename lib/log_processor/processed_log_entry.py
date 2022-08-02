from dataclasses import dataclass, field
from typing import Any, Dict, cast, Callable, Optional, Union

from lib.cloud_logging import LogEntry
from lib.log_processor.app_log_payload import AppLogPayload


@dataclass(frozen=True)
class ProcessedLogEntry:
    message: str
    data: Union[str, Dict[str, Any]] = field(
        default_factory=cast(Callable[[], Dict[str, Any]], dict)
    )
    severity: Optional[str] = field(default=None)
    platform: Optional[str] = field(default=None)
    application: Optional[str] = field(default=None)
    log_name: Optional[str] = field(default=None)
    timestamp: Optional[str] = field(default=None)


def create_processed_log_entry(
    entry: LogEntry, app_log_payload: AppLogPayload
) -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message=app_log_payload.message,
        data=app_log_payload.data,
        severity=entry.severity,
        log_name=entry.log_name,
        timestamp=entry.timestamp,
        platform=app_log_payload.platform,
        application=app_log_payload.application,
    )
