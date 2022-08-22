from datetime import datetime
from unittest.mock import Mock

import pytest

from lib.cloud_logging import LogEntry, PayloadType
from lib.log_processor import (
    process_log_entry,
    NoMatchingLogTypeFound,
    AppLogPayload,
    ProcessedLogEntry,
)


@pytest.fixture()
def log_entry():
    return LogEntry(
        resource_type="ignored",
        resource_labels=dict(),
        payload_type=PayloadType.JSON,
        payload="ignored",
        severity="ERROR",
        log_name="/example_log",
        timestamp="NOW",
    )


def test_process_log_entry_raise_if_no_factories_are_provided(log_entry):
    with pytest.raises(NoMatchingLogTypeFound):
        process_log_entry(log_entry, [])


def test_process_log_entry_calls_factories_with_log_entry(log_entry):
    factory1 = Mock(return_value=None)
    factory2 = Mock(return_value=None)
    with pytest.raises(NoMatchingLogTypeFound):
        process_log_entry(log_entry, [factory1, factory2])

    factory1.assert_called_with(log_entry)
    factory2.assert_called_with(log_entry)


def test_process_log_entry_raise_if_no_factories_create_a_value(log_entry):
    with pytest.raises(NoMatchingLogTypeFound):
        process_log_entry(log_entry, [lambda _: None, lambda _: None])


def test_process_log_entry_returns_a_proceed_log_entry_for_the_first_created_payload(
    log_entry,
):
    result = process_log_entry(
        log_entry,
        [
            lambda _: AppLogPayload(
                message="message 1",
                data=dict(),
                platform="platform1",
                application="app1",
            ),
            lambda _: AppLogPayload(
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
        timestamp=None,
        platform="platform1",
        application="app1",
    )
