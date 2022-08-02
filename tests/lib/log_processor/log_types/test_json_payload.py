import dataclasses

import pytest

from lib.cloud_logging import LogEntry, PayloadType
from lib.log_processor.log_types.json_payload import attempt_create


@pytest.fixture
def log_entry() -> LogEntry:
    return LogEntry(
        resource_type="unknown-resource",
        payload_type=PayloadType.JSON,
        payload=dict(message="Example text payload"),
        severity="ERROR",
        log_name="/logs/text-payload-example",
        timestamp="2022-08-01T11:25:38.670159583Z",
    )


def test_attempt_create_returns_processed_text_payload(log_entry):
    instance = attempt_create(log_entry)
    assert instance is not None
    assert instance.message == "Unknown JSON Error"
    assert instance.data == dict(message="Example text payload")
    assert instance.platform == "unknown-resource"
    assert instance.application is None


def test_attempt_create_returns_none_payload_type_is_not_json(log_entry):
    log_entry = dataclasses.replace(log_entry, payload_type=PayloadType.TEXT)
    instance = attempt_create(log_entry)
    assert instance is None
