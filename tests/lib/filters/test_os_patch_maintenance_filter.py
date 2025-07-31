import pytest
import datetime
import dataclasses
from datetime import timezone
from typing import Any, Dict, List
from lib.log_processor import ProcessedLogEntry
from lib.filters.os_patch_maintenance_filter import os_patch_maintenance_filter


@pytest.fixture()
def base_maintenance_log() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="The Google Compute Engine Agent Manager service terminated unexpectedly.",
        data={"EventID": 7031, "EventType": "Error"},
        severity="ERROR",
        platform="gce_instance",
        application="restapi-1",
        log_name="projects/ons-blaise-v2-prod/logs/windows_event_log",
        timestamp=datetime.datetime(2025, 7, 11, 1, 30, 46, tzinfo=timezone.utc),
        log_query={"resource.type": "gce_instance"},
    )


@pytest.fixture()
def base_non_maintenance_log() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="The Google Compute Engine Agent Manager service terminated unexpectedly.",
        data={"EventID": 7031, "EventType": "Error"},
        severity="ERROR",
        platform="gce_instance",
        application="restapi-1",
        log_name="projects/ons-blaise-v2-prod/logs/windows_event_log",
        timestamp=datetime.datetime(2025, 7, 15, 10, 30, 46, tzinfo=timezone.utc),
        log_query={"resource.type": "gce_instance"},
    )


def create_log_with_message(
    base_log: ProcessedLogEntry, message: str
) -> ProcessedLogEntry:
    return dataclasses.replace(base_log, message=message)


def create_log_with_timestamp(
    base_log: ProcessedLogEntry, timestamp
) -> ProcessedLogEntry:
    return dataclasses.replace(base_log, timestamp=timestamp)


def create_log_with_field(
    base_log: ProcessedLogEntry, **kwargs: Any
) -> ProcessedLogEntry:
    field_updates: Dict[str, Any] = dict(kwargs)
    return dataclasses.replace(base_log, **field_updates)


MAINTENANCE_LOG_PATTERNS = {
    "service_termination": [
        {
            "message": "The Google Compute Engine Agent Manager service terminated unexpectedly.  It has done this 2 time(s).  The following corrective action will be taken in 2000 milliseconds: Restart the service.\r\n",
            "log_name": "projects/ons-blaise-v2-prod/logs/windows_event_log",
        },
        {
            "message": "The Google Compute Engine Compat Manager service terminated unexpectedly.  It has done this 1 time(s).  The following corrective action will be taken in 1000 milliseconds: Restart the service.\r\n",
            "log_name": "projects/ons-blaise-v2-prod/logs/windows_event_log",
        },
        {
            "message": "Some service terminated unexpectedly and requires Restart the service",
            "log_name": "projects/ons-blaise-v2-prod/logs/windows_event_log",
        },
    ],
    "metadata_context": [
        {
            "message": "Error watching metadata: context canceled",
            "log_name": "projects/ons-blaise-v2-prod/logs/GCEGuestAgent",
        },
    ],
    "osconfig_agent": [
        {
            "message": "2025-07-25T13:45:15.8361+01:00 OSConfigAgent Warning: Error waiting for task (attempt 1 of 10): rpc error: code = Canceled desc = context canceled\r\n",
            "log_name": "projects/ons-blaise-v2-dev-jun1/logs/windows_event_log",
        },
        {
            "message": "OSConfigAgent Warning: Error waiting for task - rpc error: code = Canceled desc = context canceled",
            "log_name": "projects/ons-blaise-v2-prod/logs/windows_event_log",
        },
    ],
}


def test_os_patch_maintenance_log_patterns_are_skipped_during_maintenance(
    base_maintenance_log: ProcessedLogEntry,
):
    for pattern_name, pattern_tests in MAINTENANCE_LOG_PATTERNS.items():
        for pattern_test in pattern_tests:
            log = create_log_with_field(
                base_maintenance_log,
                message=pattern_test["message"],
                log_name=pattern_test["log_name"],
            )
            assert (
                os_patch_maintenance_filter(log) is True
            ), f"Pattern '{pattern_name}' with message '{pattern_test['message'][:50]}...' should be skipped"


def test_patterns_are_not_skipped_outside_maintenance_window(
    base_non_maintenance_log: ProcessedLogEntry,
):
    for pattern_name, pattern_tests in MAINTENANCE_LOG_PATTERNS.items():
        for pattern_test in pattern_tests[:1]:
            log = create_log_with_field(
                base_non_maintenance_log,
                message=pattern_test["message"],
                log_name=pattern_test["log_name"],
            )
            assert (
                os_patch_maintenance_filter(log) is False
            ), f"Pattern '{pattern_name}' should not be skipped outside maintenance window"


def test_maintenance_window_boundary_conditions(
    base_maintenance_log: ProcessedLogEntry,
):
    test_times = [
        (datetime.datetime(2025, 7, 11, 1, 25, 0, tzinfo=timezone.utc), True),  # Start
        (datetime.datetime(2025, 7, 11, 1, 35, 0, tzinfo=timezone.utc), True),  # End
        (
            datetime.datetime(2025, 7, 11, 1, 24, 59, tzinfo=timezone.utc),
            False,
        ),  # Before
        (
            datetime.datetime(2025, 7, 11, 1, 35, 1, tzinfo=timezone.utc),
            False,
        ),  # After
    ]

    for timestamp, should_skip in test_times:
        log = create_log_with_timestamp(base_maintenance_log, timestamp)
        result = os_patch_maintenance_filter(log)
        assert (
            result is should_skip
        ), f"Timestamp {timestamp} should {'be' if should_skip else 'not be'} skipped"


def test_invalid_field_types_are_not_skipped(base_maintenance_log: ProcessedLogEntry):
    invalid_variations: List[Dict[str, Any]] = [
        {"platform": "cloud_run_revision"},
        {"platform": 123},
        {"message": None},
        {"message": 123},
        {"timestamp": None},
        {"timestamp": "not-a-datetime"},
        {"log_name": None},
        {"log_name": ""},
    ]

    for variation in invalid_variations:
        log = create_log_with_field(base_maintenance_log, **variation)
        assert (
            os_patch_maintenance_filter(log) is False
        ), f"Invalid field {variation} should not be skipped"


def test_non_matching_messages_are_not_skipped(base_maintenance_log: ProcessedLogEntry):
    non_matching_test_cases = [
        {
            "message": "Some completely different error message",
            "log_name": "projects/ons-blaise-v2-prod/logs/windows_event_log",
        },
        {
            "message": "Regular application error",
            "log_name": "projects/ons-blaise-v2-prod/logs/GCEGuestAgent",
        },
        {
            "message": "Database connection failed",
            "log_name": "projects/ons-blaise-v2-prod/logs/cloudaudit.googleapis.com%2Factivity",
        },
    ]

    for test_case in non_matching_test_cases:
        log = create_log_with_field(
            base_maintenance_log,
            message=test_case["message"],
            log_name=test_case["log_name"],
        )
        assert (
            os_patch_maintenance_filter(log) is False
        ), f"Non-matching message '{test_case['message']}' should not be skipped"


def test_non_matching_log_names_are_not_skipped(
    base_maintenance_log: ProcessedLogEntry,
):
    service_message = (
        "The Google Compute Engine Agent Manager service terminated unexpectedly"
    )
    wrong_log_names = [
        "projects/ons-blaise-v2-prod/logs/application",
        "projects/ons-blaise-v2-prod/logs/system",
        "projects/ons-blaise-v2-prod/logs/some_other_log",
        "",
        None,
    ]

    for log_name in wrong_log_names:
        log = create_log_with_field(
            base_maintenance_log, message=service_message, log_name=log_name
        )
        assert (
            os_patch_maintenance_filter(log) is False
        ), f"Message with wrong log name '{log_name}' should not be skipped"


def test_pattern_matching_requires_both_message_and_log_name(
    base_maintenance_log: ProcessedLogEntry,
):
    mismatched_cases = [
        {
            "message": "The Google Compute Engine Agent Manager service terminated unexpectedly",
            "log_name": "projects/ons-blaise-v2-prod/logs/GCEGuestAgent",  # Wrong log name
        },
        {
            "message": "Error watching metadata: context canceled",
            "log_name": "projects/ons-blaise-v2-prod/logs/windows_event_log",  # Wrong log name
        },
        {
            "message": "Instance should be in the RUNNING state.",
            "log_name": "projects/ons-blaise-v2-prod/logs/windows_event_log",  # Wrong log name
        },
    ]

    for case in mismatched_cases:
        log = create_log_with_field(
            base_maintenance_log,
            message=case["message"],
            log_name=case["log_name"],
        )
        assert (
            os_patch_maintenance_filter(log) is False
        ), f"Mismatched pattern (message/log_name) should not be skipped"


def test_log_entry_without_required_fields_is_not_skipped(
    base_maintenance_log: ProcessedLogEntry,
):
    log_no_platform = create_log_with_field(base_maintenance_log, platform=None)
    assert os_patch_maintenance_filter(log_no_platform) is False

    log_no_message = create_log_with_field(base_maintenance_log, message=None)
    assert os_patch_maintenance_filter(log_no_message) is False

    log_no_timestamp = create_log_with_field(base_maintenance_log, timestamp=None)
    assert os_patch_maintenance_filter(log_no_timestamp) is False
