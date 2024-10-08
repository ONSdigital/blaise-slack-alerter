from typing import List, Callable, Optional, TypeVar

from lib.cloud_logging import LogEntry
from lib.log_processor.app_log_payload import AppLogPayload
from lib.log_processor.log_types import (
    audit_log,
    cloud_run_revision,
    gce_instance,
    gae_app,
    json_payload,
    text_payload,
    unknown_payload,
)

CreateAppLogPayloadFromLogEntry = Callable[[LogEntry], Optional[AppLogPayload]]


APP_LOG_PAYLOAD_FACTORIES: List[CreateAppLogPayloadFromLogEntry] = [
    audit_log.attempt_create,
    gce_instance.attempt_create,
    gae_app.attempt_create,
    cloud_run_revision.attempt_create,
    json_payload.attempt_create,
    text_payload.attempt_create,
    unknown_payload.attempt_create,
]
