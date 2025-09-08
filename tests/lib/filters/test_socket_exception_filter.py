import dataclasses
import datetime
import typing

import pytest

from lib.filters.socket_exception_filter import socket_exception_filter
from lib.log_processor.processed_log_entry import ProcessedLogEntry


@pytest.fixture()
def processed_log_entry_socket_not_found_error() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="Socket exception: Connection reset by peer (104)",
        data=dict(description="dummeh"),
        severity="ERROR",
        platform="cloud_run_revision",
        application="slack-alerts",
        log_name="/logs/cloudfunctions",
        timestamp=datetime.datetime(2024, 5, 20, 10, 23, 56, 32425),
        log_query={
            "resource.type": "cloud_run_revision",
            "resource.labels.instance_id": "00f46b928521d49fcdbf455e4592829a1631850562c1b37283d70572deaca72b851130f7fbca367bbb5a75b386efa9832f3d974f1a5a463b2fb9af0fb2a9c2fb4e57",
        },
    )


def test_socket_exception_error_log_is_skipped_when_its_run(
    processed_log_entry_socket_not_found_error: ProcessedLogEntry,
) -> None:
    log_is_skipped = socket_exception_filter(processed_log_entry_socket_not_found_error)
    assert log_is_skipped is True


def test_log_message_is_not_a_string_when_socket_exception_error(
    processed_log_entry_socket_not_found_error: ProcessedLogEntry,
) -> None:
    processed_log_entry_socket_not_found_error = dataclasses.replace(
        processed_log_entry_socket_not_found_error,
        message=typing.cast(typing.Any, 1234),
    )
    log_is_skipped = socket_exception_filter(processed_log_entry_socket_not_found_error)

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_does_not_contain_socket_exception_error(
    processed_log_entry_socket_not_found_error: ProcessedLogEntry,
) -> None:
    processed_log_entry_socket_not_found_error = dataclasses.replace(
        processed_log_entry_socket_not_found_error, message="foo"
    )
    log_is_skipped = socket_exception_filter(processed_log_entry_socket_not_found_error)

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_contains_severity_info_socket_exception_error(
    processed_log_entry_socket_not_found_error: ProcessedLogEntry,
) -> None:
    processed_log_entry_socket_not_found_error = dataclasses.replace(
        processed_log_entry_socket_not_found_error, severity="INFO"
    )
    log_is_skipped = socket_exception_filter(processed_log_entry_socket_not_found_error)

    assert log_is_skipped is False
