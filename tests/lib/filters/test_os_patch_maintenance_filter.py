import pytest
import datetime
import dataclasses

from datetime import timezone
from lib.log_processor import ProcessedLogEntry
from lib.filters.os_patch_maintenance_filter import os_patch_maintenance_filter


@pytest.fixture()
def processed_log_entry_service_terminated() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="The Google Compute Engine Agent Manager service terminated unexpectedly.  It has done this 2 time(s).  The following corrective action will be taken in 2000 milliseconds: Restart the service.\r\n",
        data={
            "Data": "4700430045004100670065006e0074004d0061006e0061006700650072000000",
            "EventID": 7031,
            "StringInserts": [
                "Google Compute Engine Agent Manager",
                "2",
                "2000",
                "1",
                "Restart the service",
            ],
            "EventType": "Error",
        },
        severity="ERROR",
        platform="gce_instance",
        application="restapi-1",
        log_name="projects/ons-blaise-v2-prod/logs/windows_event_log",
        timestamp=datetime.datetime(
            2025, 7, 11, 1, 30, 46, tzinfo=timezone.utc
        ),  # 1:30 AM - weekly maintenance window
        log_query={"resource.type": "gce_instance"},
    )


@pytest.fixture()
def processed_log_entry_metadata_context_canceled() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="Error watching metadata: context canceled",
        data={"localTimestamp": "2025-07-11T01:30:46.3700+01:00", "omitempty": None},
        severity="ERROR",
        platform="gce_instance",
        application="restapi-1",
        log_name="projects/ons-blaise-v2-prod/logs/GCEGuestAgent",
        timestamp=datetime.datetime(
            2025, 7, 11, 1, 30, 46, tzinfo=timezone.utc
        ),  # 1:30 AM - weekly maintenance window
        log_query={"resource.type": "gce_instance"},
    )


@pytest.fixture()
def processed_log_entry_compat_manager_terminated() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="The Google Compute Engine Compat Manager service terminated unexpectedly.  It has done this 1 time(s).  The following corrective action will be taken in 1000 milliseconds: Restart the service.\r\n",
        data={
            "Data": "470043004500570069006e0064006f007700730043006f006d007000610074004d0061006e0061006700650072000000",
            "EventID": 7031,
            "StringInserts": [
                "Google Compute Engine Compat Manager",
                "1",
                "1000",
                "1",
                "Restart the service",
            ],
            "EventType": "Error",
        },
        severity="ERROR",
        platform="gce_instance",
        application="blaise-gusty-data-entry-3",
        log_name="projects/ons-blaise-v2-prod/logs/windows_event_log",
        timestamp=datetime.datetime(
            2025, 7, 11, 1, 40, 25, tzinfo=timezone.utc
        ),  # 1:40 AM - weekly maintenance window
        log_query={"resource.type": "gce_instance"},
    )


def test_log_is_skipped_during_maintenance_window_compat_manager_terminated(
    processed_log_entry_compat_manager_terminated: ProcessedLogEntry,
):
    log_is_skipped = os_patch_maintenance_filter(
        processed_log_entry_compat_manager_terminated
    )
    assert log_is_skipped is True


def test_log_is_skipped_during_maintenance_window_service_terminated(
    processed_log_entry_service_terminated: ProcessedLogEntry,
):
    log_is_skipped = os_patch_maintenance_filter(processed_log_entry_service_terminated)
    assert log_is_skipped is True


def test_log_is_skipped_during_maintenance_window_metadata_canceled(
    processed_log_entry_metadata_context_canceled: ProcessedLogEntry,
):
    log_is_skipped = os_patch_maintenance_filter(
        processed_log_entry_metadata_context_canceled
    )
    assert log_is_skipped is True


def test_log_is_not_skipped_outside_maintenance_window(
    processed_log_entry_service_terminated: ProcessedLogEntry,
):
    log_entry_outside_window = dataclasses.replace(
        processed_log_entry_service_terminated,
        timestamp=datetime.datetime(2025, 7, 11, 10, 30, 46, tzinfo=timezone.utc),
    )
    log_is_skipped = os_patch_maintenance_filter(log_entry_outside_window)
    assert log_is_skipped is False


def test_log_is_not_skipped_when_not_gce_instance(
    processed_log_entry_service_terminated: ProcessedLogEntry,
):
    log_entry_not_gce = dataclasses.replace(
        processed_log_entry_service_terminated, platform="cloud_run_revision"
    )
    log_is_skipped = os_patch_maintenance_filter(log_entry_not_gce)
    assert log_is_skipped is False


def test_log_is_not_skipped_when_message_doesnt_match(
    processed_log_entry_service_terminated: ProcessedLogEntry,
):
    log_entry_different_message = dataclasses.replace(
        processed_log_entry_service_terminated, message="Some other error message"
    )
    log_is_skipped = os_patch_maintenance_filter(log_entry_different_message)
    assert log_is_skipped is False


def test_log_is_not_skipped_when_log_name_doesnt_match(
    processed_log_entry_service_terminated: ProcessedLogEntry,
):
    log_entry_different_log_name = dataclasses.replace(
        processed_log_entry_service_terminated,
        log_name="projects/ons-blaise-v2-prod/logs/some_other_log",
    )
    log_is_skipped = os_patch_maintenance_filter(log_entry_different_log_name)
    assert log_is_skipped is False


def test_metadata_canceled_is_not_skipped_outside_maintenance_window(
    processed_log_entry_metadata_context_canceled: ProcessedLogEntry,
):
    log_entry_outside_window = dataclasses.replace(
        processed_log_entry_metadata_context_canceled,
        timestamp=datetime.datetime(2025, 7, 11, 10, 30, 46, tzinfo=timezone.utc),
    )
    log_is_skipped = os_patch_maintenance_filter(log_entry_outside_window)
    assert log_is_skipped is False
