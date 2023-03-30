import dataclasses

import pytest

from lib.cloud_logging import LogEntry, PayloadType
from lib.log_processor.log_types.cloud_function import attempt_create


@pytest.fixture
def log_entry() -> LogEntry:
    return LogEntry(
        resource_type="cloud_function",
        resource_labels=dict(function_name="example-function"),
        payload_type=PayloadType.TEXT,
        payload="Cloud function error message",
        severity="ERROR",
        log_name="/logs/cf-example",
        timestamp="2022-08-01T11:25:38.670159583Z",
        labels=dict(),
    )


def test_attempt_create_succeeds_with_complete_entry(log_entry):
    instance = attempt_create(log_entry)

    assert instance is not None
    assert instance.message == "Cloud function error message"
    assert instance.data == ""
    assert instance.platform == "cloud_function"
    assert instance.application == "example-function"
    assert instance.log_query == {
        "resource.type": "cloud_function",
        "resource.labels.function_name": "example-function",
    }


def test_attempt_create_returns_none_if_resource_type_is_wrong(log_entry):
    log_entry = dataclasses.replace(log_entry, resource_type="different_resource")
    instance = attempt_create(log_entry)
    assert instance is None


def test_attempt_create_returns_unknown_application_if_label_is_missing(log_entry):
    del log_entry.resource_labels["function_name"]
    instance = attempt_create(log_entry)
    assert instance is not None
    assert instance.application == "[unknown]"


def test_attempt_create_returns_query_without_function_name_if_label_is_missing(
    log_entry,
):
    del log_entry.resource_labels["function_name"]
    instance = attempt_create(log_entry)
    assert instance is not None
    assert instance.log_query == {"resource.type": "cloud_function"}


def test_attempt_create_succeeds_if_payload_type_is_json(log_entry):
    log_entry = dataclasses.replace(
        log_entry,
        payload_type=PayloadType.JSON,
        payload=dict(example_key="example value"),
    )
    instance = attempt_create(log_entry)
    assert instance.message == "Unknown Error (see data)"
    assert instance.data == dict(example_key="example value")


def test_attempt_create_succeeds_if_payload_type_is_none(log_entry):
    log_entry = dataclasses.replace(
        log_entry, payload_type=PayloadType.NONE, payload=""
    )
    instance = attempt_create(log_entry)
    assert instance.message == "Unknown Error"
    assert instance.data == ""
