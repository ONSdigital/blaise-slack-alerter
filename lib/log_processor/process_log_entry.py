from typing import List

from lib.cloud_logging import LogEntry
from lib.log_processor.app_log_payload_factories import CreateAppLogPayloadFromLogEntry
from lib.log_processor.processed_log_entry import (
    ProcessedLogEntry,
    create_processed_log_entry,
)
from lib.log_processor.utilities import apply_argument_to_all, first_successful


class NoMatchingLogTypeFound(RuntimeError):
    pass


def process_log_entry(
    entry: LogEntry, payload_factories: List[CreateAppLogPayloadFromLogEntry]
) -> ProcessedLogEntry:
    app_log_payload = first_successful(apply_argument_to_all(payload_factories, entry))

    if app_log_payload is None:
        raise NoMatchingLogTypeFound()

    return create_processed_log_entry(entry, app_log_payload)
