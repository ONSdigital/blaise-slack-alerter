import pytest
import datetime
import dataclasses
from typing import Any, Dict, List
from lib.log_processor import ProcessedLogEntry
from lib.filters.fluent_bit_maintenance_filter import fluent_bit_maintenance_filter


@pytest.fixture()
def base_maintenance_log() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="[2025/07/18 12:48:35] [error] [C:\\work\\submodules\\fluent-bit\\src\\tls\\openssl.c:551 errno=0] No error",
        data={},
        severity="ERROR",
        platform="gce_instance",
        application="unknown",
        log_name="projects/ons-blaise-v2-prod/logs/ops-agent-fluent-bit",
        timestamp=datetime.datetime(2025, 7, 11, 1, 30, 35),  # Friday at 01:30 AM UTC
        log_query={
            "resource.type": "gce_instance",
            "resource.labels.instance_id": "test123",
        },
    )


@pytest.fixture()
def base_non_maintenance_log() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="[2025/07/18 12:48:35] [error] [C:\\work\\submodules\\fluent-bit\\src\\tls\\openssl.c:551 errno=0] No error",
        data={},
        severity="ERROR",
        platform="gce_instance",
        application="unknown",
        log_name="projects/ons-blaise-v2-prod/logs/ops-agent-fluent-bit",
        timestamp=datetime.datetime(2025, 7, 15, 10, 0, 0),  # Tuesday at 10:00 AM UTC
        log_query={
            "resource.type": "gce_instance",
            "resource.labels.instance_id": "test123",
        },
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


def test_fluent_bit_error_patterns_are_skipped_during_maintenance(
    base_maintenance_log: ProcessedLogEntry,
):
    error_messages = [
        "[2025/07/18 12:48:35] [error] [C:\\work\\submodules\\fluent-bit\\src\\tls\\openssl.c:551 errno=0] No error",
        "[2025/07/18 12:48:51] [error] [tls] syscall error: error:00000005:lib(0):func(0):DH lib",
        "[2025/07/18 12:48:51] [error] [http_client] broken connection to logging.googleapis.com:443 ?",
        "[2025/07/25 16:04:40] [error] [input:winlog:winlog.1] failed to read 'Security'",
        "[2025/07/25 16:04:45] [error] [input:winlog:winlog.1] failed to read 'System'",
        "[2025/07/25 16:04:45] [error] [in_winlog] cannot read 'Application' (1722)",
        "[2025/07/25 16:04:40] [error] [input:winlog:winlog.1] failed to read event log",
        "[2025/07/25 16:04:45] [error] [in_winlog] cannot read event log data",
        "Some error with No error pattern",
        "Error containing DH lib somewhere",
        "Message with broken connection text",
        "Another cannot read 'System' message",
        "Test cannot read 'Application' error",
        "Sample cannot read 'Security' log",
        "Log with [error] [input:winlog: pattern",
        "Entry with [error] [in_winlog] pattern",
    ]

    for message in error_messages:
        log = create_log_with_message(base_maintenance_log, message)
        assert (
            fluent_bit_maintenance_filter(log) is True
        ), f"Message '{message}' should be skipped"


def test_logs_are_not_skipped_outside_maintenance_window(
    base_non_maintenance_log: ProcessedLogEntry,
):
    error_messages = [
        "[2025/07/18 12:48:35] [error] [C:\\work\\submodules\\fluent-bit\\src\\tls\\openssl.c:551 errno=0] No error",
        "[2025/07/25 16:04:40] [error] [input:winlog:winlog.1] failed to read 'Security'",
        "[2025/07/25 16:04:45] [error] [in_winlog] cannot read 'Application' (1722)",
    ]

    for message in error_messages:
        log = create_log_with_message(base_non_maintenance_log, message)
        assert (
            fluent_bit_maintenance_filter(log) is False
        ), f"Message '{message}' should not be skipped outside maintenance"


def test_maintenance_window_boundary_conditions(
    base_maintenance_log: ProcessedLogEntry,
):
    test_times = [
        (datetime.datetime(2025, 7, 11, 1, 25, 0), True),  # Start of window
        (datetime.datetime(2025, 7, 11, 1, 35, 0), True),  # End of window
        (datetime.datetime(2025, 7, 11, 1, 24, 59), False),  # Just before
        (datetime.datetime(2025, 7, 11, 1, 35, 1), False),  # Just after
    ]

    for timestamp, should_skip in test_times:
        log = create_log_with_timestamp(base_maintenance_log, timestamp)
        result = fluent_bit_maintenance_filter(log)
        assert (
            result is should_skip
        ), f"Timestamp {timestamp} should {'be' if should_skip else 'not be'} skipped"


def test_invalid_field_types_are_not_skipped(base_maintenance_log: ProcessedLogEntry):
    invalid_variations: List[Dict[str, Any]] = [
        {"platform": 123},
        {"platform": "cloud_run_revision"},
        {"message": 123},
        {"timestamp": "not-a-datetime"},
        {"timestamp": None},
        {"severity": 123},
        {"severity": None},
        {"severity": "INFO"},
        {"severity": "WARNING"},
        {"log_name": None},
        {"log_name": ""},
        {"log_name": "projects/ons-blaise-v2-prod/logs/some-other-log"},
    ]

    for variation in invalid_variations:
        log = create_log_with_field(base_maintenance_log, **variation)
        assert (
            fluent_bit_maintenance_filter(log) is False
        ), f"Invalid field {variation} should not be skipped"


def test_non_matching_messages_are_not_skipped(base_maintenance_log: ProcessedLogEntry):
    non_matching_messages = [
        "Some completely different error message",
        "Regular application error",
        "Database connection failed",
        "File not found error",
    ]

    for message in non_matching_messages:
        log = create_log_with_message(base_maintenance_log, message)
        assert (
            fluent_bit_maintenance_filter(log) is False
        ), f"Non-matching message '{message}' should not be skipped"


def test_log_name_variations_are_accepted(base_maintenance_log: ProcessedLogEntry):
    valid_log_names = [
        "projects/ons-blaise-v2-prod/logs/ops-agent-fluent-bit",
        "projects/ons-blaise-v2-dev/logs/ops-agent-fluent-bit-additional",
        "some-prefix-ops-agent-fluent-bit-suffix",
        "ops-agent-fluent-bit",
    ]

    for log_name in valid_log_names:
        log = create_log_with_field(base_maintenance_log, log_name=log_name)
        assert (
            fluent_bit_maintenance_filter(log) is True
        ), f"Log name '{log_name}' should be accepted"


def test_none_log_entry_is_not_skipped():
    assert fluent_bit_maintenance_filter(None) is False
