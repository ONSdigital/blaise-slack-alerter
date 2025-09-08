import dataclasses
import datetime
from datetime import timezone
from typing import Any, Dict, List

import pytest

from lib.filters.fluent_bit_maintenance_filter import fluent_bit_maintenance_filter
from lib.log_processor.processed_log_entry import ProcessedLogEntry


@pytest.fixture()
def base_maintenance_log() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="[2025/07/18 12:48:35] [error] [C:\\work\\submodules\\fluent-bit\\src\\tls\\openssl.c:551 errno=0] No error",
        data={},
        severity="ERROR",
        platform="gce_instance",
        application="unknown",
        log_name="projects/ons-blaise-v2-prod/logs/ops-agent-fluent-bit",
        timestamp=datetime.datetime(
            2025, 7, 11, 0, 30, 35, tzinfo=timezone.utc
        ),  # 00:30 UTC = 01:30 BST (in maintenance window)
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
        timestamp=datetime.datetime(2025, 7, 15, 10, 0, 0, tzinfo=timezone.utc),
        log_query={
            "resource.type": "gce_instance",
            "resource.labels.instance_id": "test123",
        },
    )


def create_log_with_field(
    base_log: ProcessedLogEntry, **kwargs: Any
) -> ProcessedLogEntry:
    return dataclasses.replace(base_log, **kwargs)


def test_fluent_bit_error_patterns_are_skipped_during_maintenance(
    base_maintenance_log: ProcessedLogEntry,
) -> None:
    error_messages = [
        # TLS/OpenSSL patterns
        "[2025/07/18 12:48:35] [error] [C:\\work\\submodules\\fluent-bit\\src\\tls\\openssl.c:551 errno=0] No error",
        "[2025/07/18 12:48:51] [error] [tls] syscall error: error:00000005:lib(0):func(0):DH lib",
        # HTTP client connection patterns
        "[2025/07/18 12:48:51] [error] [http_client] broken connection to logging.googleapis.com:443 ?",
        # Windows event log read failures
        "[2025/07/25 16:04:40] [error] [input:winlog:winlog.1] failed to read 'Security'",
        "[2025/07/25 16:04:45] [error] [in_winlog] cannot read 'Application' (1722)",
        # Generic pattern matches
        "Some error with No error pattern",
        "Message with broken connection text",
        "Log with [error] [input:winlog: pattern",
        "Entry with [error] [in_winlog] pattern",
    ]

    for message in error_messages:
        log = create_log_with_field(base_maintenance_log, message=message)
        assert (
            fluent_bit_maintenance_filter(log) is True
        ), f"Message '{message}' should be skipped"


def test_logs_are_not_skipped_outside_maintenance_window(
    base_non_maintenance_log: ProcessedLogEntry,
) -> None:
    error_messages = [
        "[2025/07/18 12:48:35] [error] [C:\\work\\submodules\\fluent-bit\\src\\tls\\openssl.c:551 errno=0] No error",
        "[2025/07/25 16:04:40] [error] [input:winlog:winlog.1] failed to read 'Security'",
        "[2025/07/25 16:04:45] [error] [in_winlog] cannot read 'Application' (1722)",
    ]

    for message in error_messages:
        log = create_log_with_field(base_non_maintenance_log, message=message)
        assert (
            fluent_bit_maintenance_filter(log) is False
        ), f"Message '{message}' should not be skipped outside maintenance"


def test_maintenance_window_boundary_conditions(
    base_maintenance_log: ProcessedLogEntry,
) -> None:
    # Prod weekly maintenance window in July is 01:25-01:35 BST = 00:25-00:35 UTC
    test_times = [
        (
            datetime.datetime(2025, 7, 11, 0, 25, 0, tzinfo=timezone.utc),
            True,
        ),
        (
            datetime.datetime(2025, 7, 11, 0, 35, 0, tzinfo=timezone.utc),
            True,
        ),
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
        result = fluent_bit_maintenance_filter(log)
        assert (
            result is should_skip
        ), f"Timestamp {timestamp} should {'be' if should_skip else 'not be'} skipped"


def test_logs_not_matching_patterns_are_not_skipped(
    base_maintenance_log: ProcessedLogEntry,
) -> None:
    test_cases: List[Dict[str, Any]] = [
        {"platform": 123, "description": "Invalid platform type"},
        {"platform": "cloud_run_revision", "description": "Wrong platform type"},
        {"message": 123, "description": "Invalid message type"},
        {"timestamp": "not-a-datetime", "description": "Invalid timestamp type"},
        {"timestamp": None, "description": "Missing timestamp"},
        {"severity": "INFO", "description": "Wrong severity level"},
        {"log_name": None, "description": "Missing log name"},
        {
            "log_name": "projects/ons-blaise-v2-prod/logs/some-other-log",
            "description": "Wrong log name",
        },
        {
            "message": "Some completely different error message",
            "description": "Non-matching message",
        },
        {
            "message": "Database connection failed",
            "description": "Non-matching message",
        },
    ]

    for test_case in test_cases:
        description = test_case.pop("description")
        log = create_log_with_field(base_maintenance_log, **test_case)
        assert (
            fluent_bit_maintenance_filter(log) is False
        ), f"{description} should not be skipped"


def test_log_name_variations_are_accepted(
    base_maintenance_log: ProcessedLogEntry,
) -> None:
    valid_log_names = [
        "projects/ons-blaise-v2-prod/logs/ops-agent-fluent-bit",
        "some-prefix-ops-agent-fluent-bit-suffix",
        "ops-agent-fluent-bit",
    ]

    for log_name in valid_log_names:
        log = create_log_with_field(base_maintenance_log, log_name=log_name)
        assert (
            fluent_bit_maintenance_filter(log) is True
        ), f"Log name '{log_name}' should be accepted"


def test_none_log_entry_is_not_skipped() -> None:
    assert fluent_bit_maintenance_filter(None) is False
