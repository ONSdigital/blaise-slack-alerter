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
        timestamp=datetime.datetime(
            2025, 7, 11, 0, 30, 46, tzinfo=timezone.utc
        ),  # 00:30 UTC = 01:30 BST (in maintenance window)
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


def create_log_with_field(
    base_log: ProcessedLogEntry, **kwargs: Any
) -> ProcessedLogEntry:
    return dataclasses.replace(base_log, **kwargs)


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
    # Prod weekly maintenance window in July is 01:25-01:35 BST = 00:25-00:35 UTC
    test_times = [
        (datetime.datetime(2025, 7, 11, 0, 25, 0, tzinfo=timezone.utc), True),
        (datetime.datetime(2025, 7, 11, 0, 35, 0, tzinfo=timezone.utc), True),
        (
            datetime.datetime(2025, 7, 11, 0, 24, 59, tzinfo=timezone.utc),
            False,
        ),
        (
            datetime.datetime(2025, 7, 11, 0, 35, 1, tzinfo=timezone.utc),
            False,
        ),
    ]

    for timestamp, should_skip in test_times:
        log = create_log_with_field(base_maintenance_log, timestamp=timestamp)
        result = os_patch_maintenance_filter(log)
        assert (
            result is should_skip
        ), f"Timestamp {timestamp} should {'be' if should_skip else 'not be'} skipped"


def test_logs_not_matching_patterns_are_not_skipped(
    base_maintenance_log: ProcessedLogEntry,
):
    test_cases = [
        {
            "message": "Some completely different error message",
            "log_name": "projects/ons-blaise-v2-prod/logs/windows_event_log",
            "description": "Non-matching message with correct log name",
        },
        {
            "message": "Regular application error",
            "log_name": "projects/ons-blaise-v2-prod/logs/GCEGuestAgent",
            "description": "Non-matching message with correct log name",
        },
        {
            "message": "The Google Compute Engine Agent Manager service terminated unexpectedly",
            "log_name": "projects/ons-blaise-v2-prod/logs/GCEGuestAgent",
            "description": "Correct message with wrong log name",
        },
        {
            "message": "Error watching metadata: context canceled",
            "log_name": "projects/ons-blaise-v2-prod/logs/windows_event_log",
            "description": "Correct message with wrong log name",
        },
        {
            "message": "The Google Compute Engine Agent Manager service terminated unexpectedly",
            "log_name": "projects/ons-blaise-v2-prod/logs/application",
            "description": "Service message with wrong log name",
        },
        {
            "message": "The Google Compute Engine Agent Manager service terminated unexpectedly",
            "log_name": "",
            "description": "Service message with empty log name",
        },
        {
            "message": "The Google Compute Engine Agent Manager service terminated unexpectedly",
            "log_name": None,
            "description": "Service message with None log name",
        },
    ]

    for test_case in test_cases:
        log = create_log_with_field(
            base_maintenance_log,
            message=test_case["message"],
            log_name=test_case["log_name"],
        )
        assert (
            os_patch_maintenance_filter(log) is False
        ), f"{test_case['description']} should not be skipped"


def test_invalid_or_missing_fields_are_not_skipped(
    base_maintenance_log: ProcessedLogEntry,
):
    invalid_variations: List[Dict[str, Any]] = [
        {"platform": "cloud_run_revision", "description": "Wrong platform type"},
        {"platform": 123, "description": "Invalid platform type"},
        {"platform": None, "description": "Missing platform"},
        {"message": None, "description": "Missing message"},
        {"message": 123, "description": "Invalid message type"},
        {"timestamp": None, "description": "Missing timestamp"},
        {"timestamp": "not-a-datetime", "description": "Invalid timestamp type"},
    ]

    for variation in invalid_variations:
        description = variation.pop("description")
        log = create_log_with_field(base_maintenance_log, **variation)
        assert (
            os_patch_maintenance_filter(log) is False
        ), f"{description} should not be skipped"


def test_specific_field_combinations_are_not_skipped(
    base_maintenance_log: ProcessedLogEntry,
):
    assert (
        os_patch_maintenance_filter(
            create_log_with_field(base_maintenance_log, platform=None)
        )
        is False
    )
    assert (
        os_patch_maintenance_filter(
            create_log_with_field(base_maintenance_log, message=None)
        )
        is False
    )
    assert (
        os_patch_maintenance_filter(
            create_log_with_field(base_maintenance_log, timestamp=None)
        )
        is False
    )
