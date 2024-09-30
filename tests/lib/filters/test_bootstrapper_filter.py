import pytest
import datetime
import dataclasses

from lib.log_processor import ProcessedLogEntry
from lib.filters.bootstrapper_filter import bootstrapper_filter


@pytest.fixture()
def processed_log_entry_bootstrapper_error() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="2024/09/20 01:31:12 GCEGuestAgent: Failed to schedule job MTLS_MDS_Credential_Boostrapper with error: ShouldEnable() returned false, cannot schedule job MTLS_MDS_Credential_Boostrapper\r\n",
        data=dict(description="dummy"),
        severity="ERROR",
        platform="gce_instance",
        application="blaise-gusty-data-entry-1",
        log_name="projects/ons-blaise-v2-prod/logs/winevt.raw",
        timestamp=datetime.datetime(2023, 2, 25, 3, 46, 57, 99633),
        log_query={
            "resource.type": "gce_instance",
            "resource.labels.instance_id": "458491777778639951",
        },
    )


def test_log_is_skipped_when_its_from_gce_instance_when_bootstrapper_error(
    processed_log_entry_bootstrapper_error: ProcessedLogEntry,
):
    log_is_skipped = bootstrapper_filter(processed_log_entry_bootstrapper_error)
    assert log_is_skipped is True


def test_log_message_is_not_a_string_when_bootstrapper_error(
    processed_log_entry_bootstrapper_error: ProcessedLogEntry,
):
    processed_log_entry_bootstrapper_error = dataclasses.replace(
        processed_log_entry_bootstrapper_error, message=1234
    )
    log_is_skipped = bootstrapper_filter(processed_log_entry_bootstrapper_error)

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_contains_severity_info_for_bootstrapper_error(
    processed_log_entry_bootstrapper_error: ProcessedLogEntry,
):
    processed_log_entry_bootstrapper_error = dataclasses.replace(
        processed_log_entry_bootstrapper_error, severity="INFO"
    )
    log_is_skipped = bootstrapper_filter(processed_log_entry_bootstrapper_error)

    assert log_is_skipped is False


def test_log_message_does_not_contain_bootstrapper(
    processed_log_entry_bootstrapper_error: ProcessedLogEntry,
):
    processed_log_entry_bootstrapper_error = dataclasses.replace(
        processed_log_entry_bootstrapper_error,
        message="some other message",
    )
    log_is_skipped = bootstrapper_filter(processed_log_entry_bootstrapper_error)
    assert log_is_skipped is False
