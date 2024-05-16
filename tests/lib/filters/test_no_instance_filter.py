import pytest
import datetime
import dataclasses

from lib.log_processor import ProcessedLogEntry
from lib.filters.no_instance_filter import no_instance_filter


@pytest.fixture()
def processed_log_entry_no_instance_error() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="The request was aborted because there was no available instance. Additional troubleshooting documentation can be found at: https://cloud.google.com/functions/docs/troubleshooting#scalability",
        data=dict(description="dummy"),
        severity="ERROR",
        platform="cloud_function",
        application="nisra-case-mover-processor",
        log_name="/logs/cloudfunctions",
        timestamp=datetime.datetime(2024, 5, 16, 11, 11, 11, 99633),
        log_query={
            "resource.type": "cloud_function",
            "resource.labels.instance_id": "458491889528627364",
        },
    )


def test_log_is_skipped_when_its_not_from_cloud_function_instance_when_no_instance_error(
    processed_log_entry_no_instance_error: ProcessedLogEntry,
):
    log_is_skipped = no_instance_filter(processed_log_entry_no_instance_error)
    assert log_is_skipped is True


def test_log_is_skipped_when_its_application_is_bert_instance_when_no_instance_error(
    processed_log_entry_no_instance_error: ProcessedLogEntry,
):
    processed_log_entry_no_instance_error = dataclasses.replace(
        processed_log_entry_no_instance_error, application="bert-call-history"
    )
    log_is_skipped = no_instance_filter(processed_log_entry_no_instance_error)
    assert log_is_skipped is True


def test_log_is_not_skipped_when_its_application_is_not_in_list_of_skippable_applications_instance_when_no_instance_error(
    processed_log_entry_no_instance_error: ProcessedLogEntry,
):
    processed_log_entry_no_instance_error = dataclasses.replace(
        processed_log_entry_no_instance_error, application="dummy"
    )
    log_is_skipped = no_instance_filter(processed_log_entry_no_instance_error)
    assert log_is_skipped is False


def test_log_is_not_skipped_when_not_from_cloud_function_instance_when_no_instance_error(
    processed_log_entry_no_instance_error: ProcessedLogEntry,
):
    processed_log_entry_no_instance_error = dataclasses.replace(
        processed_log_entry_no_instance_error, platform="not_cloud_function_instance"
    )
    log_is_skipped = no_instance_filter(processed_log_entry_no_instance_error)

    assert log_is_skipped is False


def test_log_message_is_a_string_when_no_instance_error(
    processed_log_entry_no_instance_error: ProcessedLogEntry,
):
    log_is_skipped = no_instance_filter(processed_log_entry_no_instance_error)

    assert log_is_skipped is True


def test_log_message_is_not_a_string_when_no_instance_error(
    processed_log_entry_no_instance_error: ProcessedLogEntry,
):
    processed_log_entry_no_instance_error = dataclasses.replace(
        processed_log_entry_no_instance_error, message=1234
    )
    log_is_skipped = no_instance_filter(processed_log_entry_no_instance_error)

    assert log_is_skipped is False


def test_log_message_is_skipped_when_it_contains_no_instance_error(
    processed_log_entry_no_instance_error: ProcessedLogEntry,
):
    log_is_skipped = no_instance_filter(processed_log_entry_no_instance_error)

    assert log_is_skipped is True


def test_log_message_is_not_skipped_when_it_does_not_contain_no_instance_error(
    processed_log_entry_no_instance_error: ProcessedLogEntry,
):
    processed_log_entry_no_instance_error = dataclasses.replace(
        processed_log_entry_no_instance_error, message="foo"
    )
    log_is_skipped = no_instance_filter(processed_log_entry_no_instance_error)

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_log_name_is_not_a_string(
    processed_log_entry_no_instance_error: ProcessedLogEntry,
):
    processed_log_entry_no_instance_error = dataclasses.replace(
        processed_log_entry_no_instance_error, log_name=1234
    )
    log_is_skipped = no_instance_filter(processed_log_entry_no_instance_error)

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_log_message_and_log_name_contain_no_instance_agent_error(
    processed_log_entry_no_instance_error: ProcessedLogEntry,
):
    processed_log_entry_no_instance_error = dataclasses.replace(
        processed_log_entry_no_instance_error, message="foo", log_name="foo"
    )
    log_is_skipped = no_instance_filter(processed_log_entry_no_instance_error)

    assert log_is_skipped is False
