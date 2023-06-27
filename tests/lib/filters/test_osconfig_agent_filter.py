import pytest
import datetime
import dataclasses

from lib.log_processor import ProcessedLogEntry
from lib.filters.osconfig_agent_filter import osconfig_agent_filter


@pytest.fixture()
def processed_log_entry_osconfig_error() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="OSConfigAgent Error main.go:231: unexpected end of JSON input",
        data=dict(
            description="2023-02-25T03:46:49.1619Z OSConfigAgent Error main.go:231: unexpected end of JSON input\r\n"
        ),
        severity="ERROR",
        platform="gce_instance",
        application="blaise-gusty-data-entry-1",
        log_name="/logs/gce-example",
        timestamp=datetime.datetime(2023, 2, 25, 3, 46, 57, 99633),
        log_query={
            "resource.type": "gce_instance",
            "resource.labels.instance_id": "458491889528639951",
        },
    )


@pytest.fixture()
def processed_log_entry_unexpected_end_of_json() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="unexpected end of JSON input",
        data=dict(foo="bar"),
        severity="ERROR",
        platform="gce_instance",
        application="blaise-gusty-data-entry-1",
        log_name="/logs/OSConfigAgent",
        timestamp=datetime.datetime(2023, 2, 25, 3, 46, 57, 99633),
        log_query={
            "resource.type": "gce_instance",
            "resource.labels.instance_id": "458491889528639951",
        },
    )


def test_log_is_skipped_when_its_not_from_gce_instance_when_osconfig_error(
    processed_log_entry_osconfig_error: ProcessedLogEntry,
):
    log_is_skipped = osconfig_agent_filter(processed_log_entry_osconfig_error)

    assert log_is_skipped is True


def test_log_is_skipped_when_from_gce_instance_when_unexpected_end_of_json_error(
    processed_log_entry_unexpected_end_of_json: ProcessedLogEntry,
):
    log_is_skipped = osconfig_agent_filter(processed_log_entry_unexpected_end_of_json)

    assert log_is_skipped is True


def test_log_is_not_skipped_when_not_from_gce_instance_when_osconfig_error(
    processed_log_entry_osconfig_error: ProcessedLogEntry,
):
    processed_log_entry_osconfig_error = dataclasses.replace(
        processed_log_entry_osconfig_error, platform="not_gce_instance"
    )
    log_is_skipped = osconfig_agent_filter(processed_log_entry_osconfig_error)

    assert log_is_skipped is False


def test_log_is_not_skipped_when_not_from_gce_instance_when_unexpected_end_of_json_error(
    processed_log_entry_unexpected_end_of_json: ProcessedLogEntry,
):
    processed_log_entry_unexpected_end_of_json = dataclasses.replace(
        processed_log_entry_unexpected_end_of_json, platform="not_gce_instance"
    )
    log_is_skipped = osconfig_agent_filter(processed_log_entry_unexpected_end_of_json)

    assert log_is_skipped is False


def test_log_message_is_a_string_when_osconfig_error(
    processed_log_entry_osconfig_error: ProcessedLogEntry,
):
    log_is_skipped = osconfig_agent_filter(processed_log_entry_osconfig_error)

    assert log_is_skipped is True


def test_log_message_is_a_string_when_unexpected_end_of_json_error(
    processed_log_entry_unexpected_end_of_json: ProcessedLogEntry,
):
    log_is_skipped = osconfig_agent_filter(processed_log_entry_unexpected_end_of_json)

    assert log_is_skipped is True


def test_log_message_is_not_a_string_when_osconfig_error(
    processed_log_entry_osconfig_error: ProcessedLogEntry,
):
    processed_log_entry_osconfig_error = dataclasses.replace(
        processed_log_entry_osconfig_error, message=1234
    )
    log_is_skipped = osconfig_agent_filter(processed_log_entry_osconfig_error)

    assert log_is_skipped is False


def test_log_message_is_not_a_string_when_unexpected_end_of_json_error(
    processed_log_entry_unexpected_end_of_json: ProcessedLogEntry,
):
    processed_log_entry_unexpected_end_of_json = dataclasses.replace(
        processed_log_entry_unexpected_end_of_json, message=123
    )
    log_is_skipped = osconfig_agent_filter(processed_log_entry_unexpected_end_of_json)

    assert log_is_skipped is False


def test_log_message_is_skipped_when_it_contains_osconfig_error(
    processed_log_entry_osconfig_error: ProcessedLogEntry,
):
    log_is_skipped = osconfig_agent_filter(processed_log_entry_osconfig_error)

    assert log_is_skipped is True


def test_log_message_is_skipped_when_it_contains_unexpected_end_of_json(
    processed_log_entry_unexpected_end_of_json: ProcessedLogEntry,
):
    log_is_skipped = osconfig_agent_filter(processed_log_entry_unexpected_end_of_json)

    assert log_is_skipped is True


def test_log_message_is_not_skipped_when_it_does_not_contain_osconfig_error(
    processed_log_entry_osconfig_error: ProcessedLogEntry,
):
    processed_log_entry_osconfig_error = dataclasses.replace(
        processed_log_entry_osconfig_error, message="foo"
    )
    log_is_skipped = osconfig_agent_filter(processed_log_entry_osconfig_error)

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_does_not_contain_unexpected_end_of_json(
    processed_log_entry_unexpected_end_of_json: ProcessedLogEntry,
):
    processed_log_entry_unexpected_end_of_json = dataclasses.replace(
        processed_log_entry_unexpected_end_of_json, message="foo"
    )
    log_is_skipped = osconfig_agent_filter(processed_log_entry_unexpected_end_of_json)

    assert log_is_skipped is False


def test_log_message_is_skipped_when_log_name_is_a_string(
    processed_log_entry_osconfig_error: ProcessedLogEntry,
):
    log_is_skipped = osconfig_agent_filter(processed_log_entry_osconfig_error)

    assert log_is_skipped is True


def test_log_message_is_skipped_when_log_name_is_not_a_string(
    processed_log_entry_unexpected_end_of_json: ProcessedLogEntry,
):
    log_is_skipped = osconfig_agent_filter(processed_log_entry_unexpected_end_of_json)

    assert log_is_skipped is True


def test_log_message_is_not_skipped_when_log_name_is_not_a_string(
    processed_log_entry_osconfig_error: ProcessedLogEntry,
):
    processed_log_entry_osconfig_error = dataclasses.replace(
        processed_log_entry_osconfig_error, log_name=1234
    )
    log_is_skipped = osconfig_agent_filter(processed_log_entry_osconfig_error)

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_log_name_is_a_string(
    processed_log_entry_unexpected_end_of_json: ProcessedLogEntry,
):
    processed_log_entry_unexpected_end_of_json = dataclasses.replace(
        processed_log_entry_unexpected_end_of_json, log_name=1234
    )
    log_is_skipped = osconfig_agent_filter(processed_log_entry_unexpected_end_of_json)

    assert log_is_skipped is False


def test_log_message_is_skipped_when_log_message_contains_osconfig_agent_error(
    processed_log_entry_osconfig_error: ProcessedLogEntry,
):
    log_is_skipped = osconfig_agent_filter(processed_log_entry_osconfig_error)

    assert log_is_skipped is True


def test_log_message_is_skipped_when_log_message_contains_unexpected_end_of_json_error(
    processed_log_entry_unexpected_end_of_json: ProcessedLogEntry,
):
    log_is_skipped = osconfig_agent_filter(processed_log_entry_unexpected_end_of_json)

    assert log_is_skipped is True


def test_log_message_is_not_skipped_when_log_message_and_log_name_contain_osconfig_agent_error(
    processed_log_entry_osconfig_error: ProcessedLogEntry,
):
    processed_log_entry_osconfig_error = dataclasses.replace(
        processed_log_entry_osconfig_error, message="foo", log_name="foo"
    )
    log_is_skipped = osconfig_agent_filter(processed_log_entry_osconfig_error)

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_log_message_and_log_name_contain_unexpected_end_of_json_error(
    processed_log_entry_unexpected_end_of_json: ProcessedLogEntry,
):
    processed_log_entry_unexpected_end_of_json = dataclasses.replace(
        processed_log_entry_unexpected_end_of_json, message="foo", log_name="foo"
    )
    log_is_skipped = osconfig_agent_filter(processed_log_entry_unexpected_end_of_json)

    assert log_is_skipped is False
