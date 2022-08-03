import dataclasses

import pytest

from lib.cloud_logging import LogEntry, PayloadType
from lib.log_processor.log_types.gce_instance import attempt_create


@pytest.fixture
def log_entry() -> LogEntry:
    return LogEntry(
        resource_type="gce_instance",
        resource_labels=dict(),
        payload_type=PayloadType.JSON,
        payload=dict(
            message="GCE Error", extra="example extra", computer_name="my-instance"
        ),
        severity="ERROR",
        log_name="/logs/gce-example",
        timestamp="2022-08-01T11:25:38.670159583Z",
    )


def test_attempt_create_succeeds_with_complete_entry(log_entry):
    instance = attempt_create(log_entry)

    assert instance is not None
    assert instance.message == "GCE Error"
    assert instance.data == dict(extra="example extra")
    assert instance.platform == "gce_instance"
    assert instance.application == "my-instance"


def test_attempt_create_returns_none_if_resource_type_is_wrong(log_entry):
    log_entry = dataclasses.replace(log_entry, resource_type="different_resource")
    instance = attempt_create(log_entry)
    assert instance is None


def test_attempt_create_returns_none_if_message_is_missing(log_entry):
    del log_entry.payload["message"]
    instance = attempt_create(log_entry)
    assert instance is None


def test_attempt_create_returns_none_if_computer_name_is_missing(log_entry):
    del log_entry.payload["computer_name"]
    instance = attempt_create(log_entry)
    assert instance is None


def test_attempt_create_returns_none_if_payload_type_is_not_json(log_entry):
    log_entry = dataclasses.replace(log_entry, payload_type=PayloadType.TEXT)
    instance = attempt_create(log_entry)
    assert instance is None


def test_attempt_create_returns_none_if_payload_not_a_dict(log_entry):
    log_entry = dataclasses.replace(log_entry, payload="text payload")
    instance = attempt_create(log_entry)
    assert instance is None
