import pytest
import datetime
import dataclasses

from lib.log_processor import ProcessedLogEntry
from lib.filters.paramiko_filter import paramiko_filter


@pytest.fixture()
def processed_log_entry_paramiko_error() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="paramiko",
        data=dict(description="dummy"),
        severity="ERROR",
        platform="cloud_run_revision",
        application="unknown",
        log_name="projects/ons-blaise-v2-prod/logs/run.googleapis.com%2Fstderr",
        timestamp=datetime.datetime(2023, 2, 25, 3, 46, 57, 99633),
        log_query={
            "resource.type": "cloud_run_revision",
            "resource.labels.instance_id": "458491777778639951",
        },
    )


def test_log_is_skipped_when_its_from_cloud_run_revision_when_paramiko_error(
    processed_log_entry_paramiko_error: ProcessedLogEntry,
):
    log_is_skipped = paramiko_filter(processed_log_entry_paramiko_error)
    assert log_is_skipped is True


def test_log_message_is_not_a_string_when_paramiko_error(
    processed_log_entry_paramiko_error: ProcessedLogEntry,
):
    processed_log_entry_paramiko_error = dataclasses.replace(
        processed_log_entry_paramiko_error, message=1234
    )
    log_is_skipped = paramiko_filter(processed_log_entry_paramiko_error)

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_contains_severity_info_for_paramiko_error(
    processed_log_entry_paramiko_error: ProcessedLogEntry,
):
    processed_log_entry_paramiko_error = dataclasses.replace(
        processed_log_entry_paramiko_error, severity="INFO"
    )
    log_is_skipped = paramiko_filter(processed_log_entry_paramiko_error)

    assert log_is_skipped is False


def test_log_message_does_not_contain_paramiko(
    processed_log_entry_paramiko_error: ProcessedLogEntry,
):
    processed_log_entry_paramiko_error = dataclasses.replace(
        processed_log_entry_paramiko_error,
        message="some other message",
    )
    log_is_skipped = paramiko_filter(processed_log_entry_paramiko_error)
    assert log_is_skipped is False
