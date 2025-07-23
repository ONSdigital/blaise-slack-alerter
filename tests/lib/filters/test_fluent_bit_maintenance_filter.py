import pytest
import datetime
import dataclasses
from lib.log_processor import ProcessedLogEntry
from lib.filters.fluent_bit_maintenance_filter import fluent_bit_maintenance_filter


@pytest.fixture()
def processed_log_entry_fluent_bit_tls_error() -> ProcessedLogEntry:
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
            "resource.labels.instance_id": "6542796480007992547",
        },
    )


@pytest.fixture()
def processed_log_entry_fluent_bit_syscall_error() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="[2025/07/18 12:48:51] [error] [tls] syscall error: error:00000005:lib(0):func(0):DH lib",
        data={},
        severity="ERROR",
        platform="gce_instance", 
        application="unknown",
        log_name="projects/ons-blaise-v2-prod/logs/ops-agent-fluent-bit",
        timestamp=datetime.datetime(2025, 7, 11, 1, 48, 51),  # Friday at 01:48 AM UTC
        log_query={
            "resource.type": "gce_instance",
            "resource.labels.instance_id": "6542796480007992547",
        },
    )


@pytest.fixture()
def processed_log_entry_fluent_bit_broken_connection() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="[2025/07/18 12:48:51] [error] [http_client] broken connection to logging.googleapis.com:443 ?",
        data={},
        severity="ERROR",
        platform="gce_instance",
        application="unknown", 
        log_name="projects/ons-blaise-v2-prod/logs/ops-agent-fluent-bit",
        timestamp=datetime.datetime(2025, 7, 11, 1, 48, 51),  # Friday at 01:48 AM UTC
        log_query={
            "resource.type": "gce_instance",
            "resource.labels.instance_id": "6542796480007992547",
        },
    )


def test_log_is_skipped_during_maintenance_window_for_tls_error(
    processed_log_entry_fluent_bit_tls_error: ProcessedLogEntry,
):
    log_is_skipped = fluent_bit_maintenance_filter(
        processed_log_entry_fluent_bit_tls_error
    )
    assert log_is_skipped is True


def test_log_is_skipped_during_maintenance_window_for_syscall_error(
    processed_log_entry_fluent_bit_syscall_error: ProcessedLogEntry,
):
    log_is_skipped = fluent_bit_maintenance_filter(
        processed_log_entry_fluent_bit_syscall_error
    )
    assert log_is_skipped is True


def test_log_is_skipped_during_maintenance_window_for_broken_connection(
    processed_log_entry_fluent_bit_broken_connection: ProcessedLogEntry,
):
    log_is_skipped = fluent_bit_maintenance_filter(
        processed_log_entry_fluent_bit_broken_connection
    )
    assert log_is_skipped is True


def test_log_is_not_skipped_outside_maintenance_window(
    processed_log_entry_fluent_bit_tls_error: ProcessedLogEntry,
):
    # Tuesday at 10:00 AM UTC (outside maintenance window)
    modified_log = dataclasses.replace(
        processed_log_entry_fluent_bit_tls_error,
        timestamp=datetime.datetime(2025, 7, 15, 10, 0, 0)
    )
    log_is_skipped = fluent_bit_maintenance_filter(modified_log)
    assert log_is_skipped is False


def test_log_is_not_skipped_when_not_from_gce_instance(
    processed_log_entry_fluent_bit_tls_error: ProcessedLogEntry,
):
    modified_log = dataclasses.replace(
        processed_log_entry_fluent_bit_tls_error,
        platform="cloud_run_revision"
    )
    log_is_skipped = fluent_bit_maintenance_filter(modified_log)
    assert log_is_skipped is False


def test_log_is_not_skipped_when_not_error_severity(
    processed_log_entry_fluent_bit_tls_error: ProcessedLogEntry,
):
    modified_log = dataclasses.replace(
        processed_log_entry_fluent_bit_tls_error,
        severity="INFO"
    )
    log_is_skipped = fluent_bit_maintenance_filter(modified_log)
    assert log_is_skipped is False


def test_log_is_not_skipped_when_not_from_ops_agent_fluent_bit(
    processed_log_entry_fluent_bit_tls_error: ProcessedLogEntry,
):
    modified_log = dataclasses.replace(
        processed_log_entry_fluent_bit_tls_error,
        log_name="projects/ons-blaise-v2-prod/logs/some-other-log"
    )
    log_is_skipped = fluent_bit_maintenance_filter(modified_log)
    assert log_is_skipped is False


def test_log_is_not_skipped_when_message_doesnt_match_patterns(
    processed_log_entry_fluent_bit_tls_error: ProcessedLogEntry,
):
    modified_log = dataclasses.replace(
        processed_log_entry_fluent_bit_tls_error,
        message="Some completely different error message"
    )
    log_is_skipped = fluent_bit_maintenance_filter(modified_log)
    assert log_is_skipped is False


def test_log_is_not_skipped_when_log_entry_is_none():
    log_is_skipped = fluent_bit_maintenance_filter(None)
    assert log_is_skipped is False


def test_log_is_not_skipped_when_platform_is_not_string(
    processed_log_entry_fluent_bit_tls_error: ProcessedLogEntry,
):
    modified_log = dataclasses.replace(
        processed_log_entry_fluent_bit_tls_error,
        platform=123
    )
    log_is_skipped = fluent_bit_maintenance_filter(modified_log)
    assert log_is_skipped is False


def test_log_is_not_skipped_when_message_is_not_string(
    processed_log_entry_fluent_bit_tls_error: ProcessedLogEntry,
):
    modified_log = dataclasses.replace(
        processed_log_entry_fluent_bit_tls_error,
        message=123
    )
    log_is_skipped = fluent_bit_maintenance_filter(modified_log)
    assert log_is_skipped is False


def test_log_is_not_skipped_when_timestamp_is_not_datetime(
    processed_log_entry_fluent_bit_tls_error: ProcessedLogEntry,
):
    modified_log = dataclasses.replace(
        processed_log_entry_fluent_bit_tls_error,
        timestamp="not-a-datetime"
    )
    log_is_skipped = fluent_bit_maintenance_filter(modified_log)
    assert log_is_skipped is False
