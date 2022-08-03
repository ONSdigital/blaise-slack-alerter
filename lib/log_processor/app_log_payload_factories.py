from typing import List, Callable, Optional, TypeVar

from lib.cloud_logging import LogEntry
from lib.log_processor.app_log_payload import AppLogPayload
from lib.log_processor.log_types import (
    cloud_function,
    gce_instance,
    json_payload,
    text_payload,
    unknown_payload,
)

CreateAppLogPayloadFromLogEntry = Callable[[LogEntry], Optional[AppLogPayload]]


APP_LOG_PAYLOAD_FACTORIES: List[CreateAppLogPayloadFromLogEntry] = [
    gce_instance.attempt_create,
    cloud_function.attempt_create,
    json_payload.attempt_create,
    text_payload.attempt_create,
    unknown_payload.attempt_create,
]


Arg = TypeVar("Arg")
Return = TypeVar("Return")


def apply_argument_to_all(
    fs: List[Callable[[Arg], Return]], argument: Arg
) -> List[Callable[[], Return]]:
    return [apply_argument(create, argument) for create in fs]


def apply_argument(f: Callable[[Arg], Return], argument: Arg) -> Callable[[], Return]:
    return lambda: f(argument)
