import dataclasses

import pytest

from lib.cloud_logging import LogEntry, PayloadType
from lib.log_processor.log_types.gce_instance import attempt_create


@pytest.fixture
def log_entry() -> LogEntry:
    return LogEntry(
        resource_type="gce_instance",
        resource_labels=dict(instance_id="123123123"),
        payload_type=PayloadType.JSON,
        payload=dict(
            message="GCE Error", extra="example extra", computer_name="my-instance"
        ),
        severity="ERROR",
        log_name="/logs/gce-example",
        timestamp="2022-08-01T11:25:38.670159583Z",
        labels=dict(instance_name="my-instance-label"),
    )


def test_attempt_create_succeeds_with_complete_entry(log_entry):
    instance = attempt_create(log_entry)

    assert instance is not None
    assert instance.message == "GCE Error"
    assert instance.data == dict(extra="example extra")
    assert instance.platform == "gce_instance"
    assert instance.application == "my-instance"
    assert instance.log_query == {
        "resource.type": "gce_instance",
        "resource.labels.instance_id": "123123123",
    }
    assert instance.most_important_values == ["description", "event_type"]


def test_attempt_create_returns_none_if_resource_type_is_wrong(log_entry):
    log_entry = dataclasses.replace(log_entry, resource_type="different_resource")
    instance = attempt_create(log_entry)
    assert instance is None


def test_attempt_create_returns_unknown_error_if_message_is_missing(log_entry):
    del log_entry.payload["message"]
    instance = attempt_create(log_entry)
    assert instance.message == "Unknown Error"


def test_attempt_create_returns_computer_name_label_if_computer_name_is_missing(
    log_entry,
):
    del log_entry.payload["computer_name"]
    instance = attempt_create(log_entry)
    assert instance.application == "my-instance-label"


def test_attempt_create_returns_instance_id_if_computer_name_and_label_is_missing(
    log_entry,
):
    del log_entry.payload["computer_name"]
    del log_entry.labels["instance_name"]
    instance = attempt_create(log_entry)
    assert instance.application == "123123123"


def test_attempt_create_returns_unknown_app_if_computer_name_and_label_and_instance_id_is_missing(
    log_entry,
):
    del log_entry.payload["computer_name"]
    del log_entry.labels["instance_name"]
    del log_entry.resource_labels["instance_id"]
    instance = attempt_create(log_entry)
    assert instance.application == "[unknown]"


def test_attempt_create_does_not_include_instance_id_if_label_is_missing(log_entry):
    instance = attempt_create(dataclasses.replace(log_entry, resource_labels={}))
    assert instance.log_query == {"resource.type": "gce_instance"}


def test_attempt_create_returns_none_if_payload_type_is_text(log_entry):
    log_entry = dataclasses.replace(
        log_entry, payload_type=PayloadType.TEXT, payload="Error message"
    )
    instance = attempt_create(log_entry)
    assert instance.message == "Error message"
