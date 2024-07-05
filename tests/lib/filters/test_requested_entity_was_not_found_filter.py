import pytest
import datetime
import dataclasses

from lib.log_processor import ProcessedLogEntry
from lib.filters.requested_entity_was_not_found_filter import requested_entity_was_not_found_filter

@pytest.fixture()
def processed_log_entry_requested_entity_was_not_found_error() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message='generic::not_found: Requested entity was not found.".',
        data=dict(description="dummy"),
        severity="ERROR",
        platform="cloud_function",
        application="unknown",
        log_name="/logs/cloudfunctions",
        timestamp=datetime.datetime(2024, 4, 18, 6, 22, 54, 24321),
        log_query={
            "resource.type": "cloud_function",
            "resource.labels.instance_id": "234023567239340394",
        },
    )

def test_log_is_skipped_when_its_from_cloud_function_when_requested_entity_was_not_found_error_GCP(
    processed_log_entry_requested_entity_was_not_found_error: ProcessedLogEntry,
):
    log_is_skipped = requested_entity_was_not_found_filter(
        processed_log_entry_requested_entity_was_not_found_error
    )
    assert log_is_skipped is True

def test_log_message_is_not_a_string_when_entity_was_not_found_error_GCP(
    processed_log_entry_requested_entity_was_not_found_error: ProcessedLogEntry,
):
    processed_log_entry_requested_entity_was_not_found_error = dataclasses.replace(
        processed_log_entry_requested_entity_was_not_found_error, message=1234
    )
    log_is_skipped = requested_entity_was_not_found_filter(
        processed_log_entry_requested_entity_was_not_found_error
    )

    assert log_is_skipped is False

def test_log_message_is_not_skipped_when_it_does_not_contain_requested_entity_was_not_found_error_GCP(
    processed_log_entry_requested_entity_was_not_found_error: ProcessedLogEntry,
):
    processed_log_entry_requested_entity_was_not_found_error = dataclasses.replace(
        processed_log_entry_requested_entity_was_not_found_error, message="foo"
    )
    log_is_skipped = requested_entity_was_not_found_filter(
        processed_log_entry_requested_entity_was_not_found_error
    )

    assert log_is_skipped is False

def test_log_message_is_not_skipped_when_it_contains_severity_info_GCP(
    processed_log_entry_requested_entity_was_not_found_error: ProcessedLogEntry,
):
    processed_log_entry_requested_entity_was_not_found_error = dataclasses.replace(
        processed_log_entry_requested_entity_was_not_found_error, severity="INFO"
    )
    log_is_skipped = requested_entity_was_not_found_filter(
        processed_log_entry_requested_entity_was_not_found_error
    )

    assert log_is_skipped is False
