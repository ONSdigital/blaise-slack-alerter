import dataclasses

import pytest

from lib.cloud_logging import LogEntry, PayloadType
from lib.log_processor.log_types.gae_app import attempt_create


@pytest.fixture
def log_entry() -> LogEntry:
    return LogEntry(
        resource_type="gae_app",
        resource_labels=dict(module_id="app-name"),
        payload_type=PayloadType.JSON,
        payload=dict(
            moduleId="app-name",
            extra="something",
        ),
        severity="ERROR",
        log_name="/logs/gae-example",
        timestamp="2022-08-01T11:25:38.670159583Z",
    )


def test_attempt_create_succeeds_with_no_message_or_line(log_entry):
    instance = attempt_create(log_entry)

    assert instance is not None
    assert instance.message == "Unknown error"


def test_attempt_create_succeeds_with_complete_entry_with_message(log_entry):
    log_entry.payload["message"] = "Error message"

    instance = attempt_create(log_entry)

    assert instance is not None
    assert instance.message == "Error message"
    assert instance.data == dict(extra="something")
    assert instance.platform == "gae_app"
    assert instance.application == "app-name"
    assert instance.log_query == {
        "resource.type": "gae_app",
        "resource.labels.module_id": "app-name",
    }


def test_attempt_create_succeeds_with_complete_entry_with_message_and_line(log_entry):
    log_entry.payload["message"] = "Error message"
    log_entry.payload["line"] = [
        dict(
            logMessage="Line message message",
            severity="ERROR",
            time="2022-08-03T14:48:46.535735Z",
        )
    ]

    instance = attempt_create(log_entry)

    assert instance is not None
    assert instance.message == "Error message"


def test_attempt_create_succeeds_with_complete_entry_with_line(log_entry):
    log_entry.payload["line"] = [
        dict(
            logMessage="Error message",
            severity="ERROR",
            time="2022-08-03T14:48:46.535735Z",
        )
    ]

    instance = attempt_create(log_entry)

    assert instance is not None
    assert instance.message == "Error message"
    assert instance.data == dict(extra="something")
    assert instance.platform == "gae_app"
    assert instance.application == "app-name"


def test_attempt_create_succeeds_with_line_which_is_not_an_array(log_entry):
    log_entry.payload["line"] = "random string"

    instance = attempt_create(log_entry)

    assert instance is not None
    assert instance.message == "Unknown error"


def test_attempt_create_succeeds_with_line_with_no_elements(log_entry):
    log_entry.payload["line"] = []

    instance = attempt_create(log_entry)

    assert instance is not None
    assert instance.message == "Unknown error"


def test_attempt_create_succeeds_with_line_non_dict_element(log_entry):
    log_entry.payload["line"] = ["string"]

    instance = attempt_create(log_entry)

    assert instance is not None
    assert instance.message == "Unknown error"


def test_attempt_create_succeeds_with_line_without_log_message(log_entry):
    log_entry.payload["line"] = [dict()]

    instance = attempt_create(log_entry)

    assert instance is not None
    assert instance.message == "Unknown error"


def test_attempt_create_returns_none_if_resource_type_is_wrong(log_entry):
    log_entry = dataclasses.replace(log_entry, resource_type="different_resource")
    instance = attempt_create(log_entry)
    assert instance is None


def test_attempt_create_returns_none_application_if_module_id_label_is_missing(
    log_entry,
):
    del log_entry.resource_labels["module_id"]
    instance = attempt_create(log_entry)
    assert instance.application == "[unknown]"


def test_attempt_create_returns_no_name_filter_if_module_id_label_is_missing(log_entry):
    del log_entry.resource_labels["module_id"]
    instance = attempt_create(log_entry)
    assert instance.log_query == {"resource.type": "gae_app"}


def test_attempt_create_succeeds_if_payload_type_is_text(log_entry):
    log_entry = dataclasses.replace(
        log_entry,
        payload_type=PayloadType.TEXT,
        payload="Error message",
    )
    instance = attempt_create(log_entry)
    assert instance.message == "Error message"
    assert instance.data == ""
