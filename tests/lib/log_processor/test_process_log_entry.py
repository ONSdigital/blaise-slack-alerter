import pytest

from lib.cloud_logging import LogEntry, PayloadType
from lib.log_processor import (
    process_log_entry,
    NoMatchingLogTypeFound,
    AppLogPayload,
    ProcessedLogEntry,
)


def test_process_log_entry_raise_if_no_factories_are_provided():
    log_entry = LogEntry(
        resource_type="ignored",
        payload_type=PayloadType.JSON,
        payload="ignored",
        severity="ignored",
        log_name="ignored",
        timestamp="ignored",
    )
    with pytest.raises(NoMatchingLogTypeFound):
        process_log_entry(log_entry, [])


def test_process_log_entry_raise_if_no_factories_create_a_value():
    log_entry = LogEntry(
        resource_type="ignored",
        payload_type=PayloadType.JSON,
        payload="ignored",
        severity="ignored",
        log_name="ignored",
        timestamp="ignored",
    )
    with pytest.raises(NoMatchingLogTypeFound):
        process_log_entry(log_entry, [lambda: None, lambda: None])


def test_process_log_entry_returns_a_proceed_log_entry_for_the_first_created_payload():
    log_entry = LogEntry(
        resource_type="ignored",
        payload_type=PayloadType.JSON,
        payload="ignored",
        severity="ERROR",
        log_name="/example_log",
        timestamp="NOW",
    )
    result = process_log_entry(
        log_entry,
        [
            lambda: AppLogPayload(
                message="message 1",
                data=dict(),
                platform="platform1",
                application="app1",
            ),
            lambda: AppLogPayload(
                message="message 1",
                data=dict(),
                platform="platform2",
                application="app2",
            ),
        ],
    )

    assert result == ProcessedLogEntry(
        message="message 1",
        data=dict(),
        severity="ERROR",
        log_name="/example_log",
        timestamp="NOW",
        platform="platform1",
        application="app1",
    )
