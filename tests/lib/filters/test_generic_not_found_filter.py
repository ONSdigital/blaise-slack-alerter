import pytest
import datetime
import dataclasses

from lib.log_processor import ProcessedLogEntry
from lib.filters.generic_not_found_filter import generic_not_found_filter


@pytest.fixture()
def processed_log_entry_generic_not_found_error_latest() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message='alert: ERROR: [AuditLog] generic::not_found: Failed to fetch "latest"',
        data=dict(description="dummy"),
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


@pytest.fixture()
def processed_log_entry_generic_not_found_error_version() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message='alert: ERROR: [AuditLog] generic::not_found: Failed to fetch "version_255"',
        data=dict(description="dummy"),
        severity="ERROR",
        platform="cloud_run_revision",
        application="slack-alerts",
        log_name="/logs/cloudfunctions",
        timestamp=datetime.datetime(2024, 5, 20, 10, 23, 56, 32425),
        log_query={
            "resource.type": "cloud_run_revision",
            "resource.labels.instance_id": "00f46b928521d49fcdbf455e4592829a1631850562c1b37283d70572df455e4592829a1631850562c1b3725a75b386efa9832f3d974f1a5a463b2fb9af0fb2a9b4e57",
        },
    )


def test_log_is_not_skipped_when_its_first_run_generic_not_found_error_latest(
    processed_log_entry_generic_not_found_error_latest: ProcessedLogEntry,
):
    log_is_skipped = generic_not_found_filter(
        processed_log_entry_generic_not_found_error_latest
    )
    assert log_is_skipped is True


def test_log_is_not_skipped_when_its_first_run_generic_not_found_error_version(
    processed_log_entry_generic_not_found_error_version: ProcessedLogEntry,
):
    log_is_skipped = generic_not_found_filter(
        processed_log_entry_generic_not_found_error_version
    )
    assert log_is_skipped is True


def test_log_is_skipped_when_its_from_cloud_run_revision_when_generic_not_found_error_latest(
    processed_log_entry_generic_not_found_error_latest: ProcessedLogEntry,
):
    log_is_skipped = generic_not_found_filter(
        processed_log_entry_generic_not_found_error_latest
    )
    assert log_is_skipped is True


def test_log_is_skipped_when_its_from_cloud_run_revision_when_generic_not_found_error_version(
    processed_log_entry_generic_not_found_error_version: ProcessedLogEntry,
):
    log_is_skipped = generic_not_found_filter(
        processed_log_entry_generic_not_found_error_version
    )
    assert log_is_skipped is True


def test_log_message_is_not_a_string_when_generic_not_found_error_latest(
    processed_log_entry_generic_not_found_error_latest: ProcessedLogEntry,
):
    processed_log_entry_generic_not_found_error_latest = dataclasses.replace(
        processed_log_entry_generic_not_found_error_latest, message=1234
    )
    log_is_skipped = generic_not_found_filter(
        processed_log_entry_generic_not_found_error_latest
    )

    assert log_is_skipped is False


def test_log_message_is_not_a_string_when_generic_not_found_error_version(
    processed_log_entry_generic_not_found_error_version: ProcessedLogEntry,
):
    processed_log_entry_generic_not_found_error_version = dataclasses.replace(
        processed_log_entry_generic_not_found_error_version, message=1234
    )
    log_is_skipped = generic_not_found_filter(
        processed_log_entry_generic_not_found_error_version
    )

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_does_not_contain_generic_not_found_error_latest(
    processed_log_entry_generic_not_found_error_latest: ProcessedLogEntry,
):
    processed_log_entry_generic_not_found_error_latest = dataclasses.replace(
        processed_log_entry_generic_not_found_error_latest, message="foo"
    )
    log_is_skipped = generic_not_found_filter(
        processed_log_entry_generic_not_found_error_latest
    )

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_does_not_contain_generic_not_found_error_version(
    processed_log_entry_generic_not_found_error_version: ProcessedLogEntry,
):
    processed_log_entry_generic_not_found_error_version = dataclasses.replace(
        processed_log_entry_generic_not_found_error_version, message="foo"
    )
    log_is_skipped = generic_not_found_filter(
        processed_log_entry_generic_not_found_error_version
    )

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_contains_severity_info_latest(
    processed_log_entry_generic_not_found_error_latest: ProcessedLogEntry,
):
    processed_log_entry_generic_not_found_error_latest = dataclasses.replace(
        processed_log_entry_generic_not_found_error_latest, severity="INFO"
    )
    log_is_skipped = generic_not_found_filter(
        processed_log_entry_generic_not_found_error_latest
    )

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_contains_severity_info_version(
    processed_log_entry_generic_not_found_error_version: ProcessedLogEntry,
):
    processed_log_entry_generic_not_found_error_version = dataclasses.replace(
        processed_log_entry_generic_not_found_error_version, severity="INFO"
    )
    log_is_skipped = generic_not_found_filter(
        processed_log_entry_generic_not_found_error_version
    )

    assert log_is_skipped is False
