from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, cast, Callable, Optional, Union, List

from dateutil.parser import parse, ParserError

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
    timestamp: Optional[datetime] = field(default=None)
    log_query: Dict[str, str] = field(default_factory=dict)
    most_important_values: Optional[List[str]] = field(default=None)


def create_processed_log_entry(
    entry: LogEntry, app_log_payload: AppLogPayload
) -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message=app_log_payload.message,
        data=app_log_payload.data,
        severity=entry.severity,
        log_name=entry.log_name,
        timestamp=_parse_datetime(entry),
        platform=app_log_payload.platform,
        application=app_log_payload.application,
        log_query=app_log_payload.log_query,
        most_important_values=app_log_payload.most_important_values,
    )


def _parse_datetime(entry: LogEntry) -> Optional[datetime]:
    try:
        return (parse(entry.timestamp)) if entry.timestamp is not None else None
    except ParserError:
        return None
