from typing import List, Callable, Optional, TypeVar

from lib.cloud_logging import LogEntry
from lib.log_processor.app_log_payload import AppLogPayload
from lib.log_processor.processed_log_entry import create_processed_log_entry

CreateAppLogPayload = Callable[[], Optional[AppLogPayload]]


class NoMatchingLogTypeFound(RuntimeError):
    pass


def process_log_entry(entry: LogEntry, payload_factories: List[CreateAppLogPayload]):
    app_log_payload = first_successful(payload_factories)

    if app_log_payload is None:
        raise NoMatchingLogTypeFound()

    return create_processed_log_entry(entry, app_log_payload)


Return = TypeVar("Return")


def first_successful(
    factories: List[Callable[[], Optional[Return]]]
) -> Optional[Return]:
    for create in factories:
        result = create()
        if result is not None:
            return result
    return None
