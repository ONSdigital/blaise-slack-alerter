import typing
import pytest
import datetime
import dataclasses

from lib.log_processor.processed_log_entry import ProcessedLogEntry
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


@pytest.fixture()
def processed_log_entry_generic_not_found_error_with_uuid() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message='alert: ERROR: [AuditLog] generic::not_found: Failed to fetch "6568e9ec-3d4a-4778-a1d3-af58553134d3"',
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
) -> None:
    log_is_skipped = generic_not_found_filter(
        processed_log_entry_generic_not_found_error_latest
    )
    assert log_is_skipped is True


def test_log_is_not_skipped_when_its_first_run_generic_not_found_error_version(
    processed_log_entry_generic_not_found_error_version: ProcessedLogEntry,
) -> None:
    log_is_skipped = generic_not_found_filter(
        processed_log_entry_generic_not_found_error_version
    )
    assert log_is_skipped is True


def test_log_is_not_skipped_when_its_first_run_generic_not_found_error_with_uuid(
    processed_log_entry_generic_not_found_error_with_uuid: ProcessedLogEntry,
) -> None:
    log_is_skipped = generic_not_found_filter(
        processed_log_entry_generic_not_found_error_with_uuid
    )
    assert log_is_skipped is True


def test_log_is_skipped_when_its_from_cloud_run_revision_when_generic_not_found_error_latest(
    processed_log_entry_generic_not_found_error_latest: ProcessedLogEntry,
) -> None:
    log_is_skipped = generic_not_found_filter(
        processed_log_entry_generic_not_found_error_latest
    )
    assert log_is_skipped is True


def test_log_is_skipped_when_its_from_cloud_run_revision_when_generic_not_found_error_version(
    processed_log_entry_generic_not_found_error_version: ProcessedLogEntry,
) -> None:
    log_is_skipped = generic_not_found_filter(
        processed_log_entry_generic_not_found_error_version
    )
    assert log_is_skipped is True


def test_log_is_skipped_when_its_from_cloud_run_revision_when_generic_not_found_error_with_uuid(
    processed_log_entry_generic_not_found_error_with_uuid: ProcessedLogEntry,
) -> None:
    log_is_skipped = generic_not_found_filter(
        processed_log_entry_generic_not_found_error_with_uuid
    )
    assert log_is_skipped is True


def test_log_message_is_not_a_string_when_generic_not_found_error_latest(
    processed_log_entry_generic_not_found_error_latest: ProcessedLogEntry,
) -> None:
    processed_log_entry_generic_not_found_error_latest = dataclasses.replace(
        processed_log_entry_generic_not_found_error_latest,
        message=typing.cast(typing.Any, 1234),
    )
    log_is_skipped = generic_not_found_filter(
        processed_log_entry_generic_not_found_error_latest
    )

    assert log_is_skipped is False


def test_log_message_is_not_a_string_when_generic_not_found_error_version(
    processed_log_entry_generic_not_found_error_version: ProcessedLogEntry,
) -> None:
    processed_log_entry_generic_not_found_error_version = dataclasses.replace(
        processed_log_entry_generic_not_found_error_version,
        message=typing.cast(typing.Any, 1234),
    )
    log_is_skipped = generic_not_found_filter(
        processed_log_entry_generic_not_found_error_version
    )

    assert log_is_skipped is False


def test_log_message_is_not_a_string_when_generic_not_found_error_with_uuid(
    processed_log_entry_generic_not_found_error_with_uuid: ProcessedLogEntry,
) -> None:
    processed_log_entry_generic_not_found_error_with_uuid = dataclasses.replace(
        processed_log_entry_generic_not_found_error_with_uuid,
        message=typing.cast(typing.Any, 1234),
    )
    log_is_skipped = generic_not_found_filter(
        processed_log_entry_generic_not_found_error_with_uuid
    )

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_does_not_contain_generic_not_found_error_latest(
    processed_log_entry_generic_not_found_error_latest: ProcessedLogEntry,
) -> None:
    processed_log_entry_generic_not_found_error_latest = dataclasses.replace(
        processed_log_entry_generic_not_found_error_latest, message="foo"
    )
    log_is_skipped = generic_not_found_filter(
        processed_log_entry_generic_not_found_error_latest
    )

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_does_not_contain_generic_not_found_error_version(
    processed_log_entry_generic_not_found_error_version: ProcessedLogEntry,
) -> None:
    processed_log_entry_generic_not_found_error_version = dataclasses.replace(
        processed_log_entry_generic_not_found_error_version, message="foo"
    )
    log_is_skipped = generic_not_found_filter(
        processed_log_entry_generic_not_found_error_version
    )

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_does_not_contain_generic_not_found_error_with_uuid(
    processed_log_entry_generic_not_found_error_with_uuid: ProcessedLogEntry,
) -> None:
    processed_log_entry_generic_not_found_error_with_uuid = dataclasses.replace(
        processed_log_entry_generic_not_found_error_with_uuid, message="foo"
    )
    log_is_skipped = generic_not_found_filter(
        processed_log_entry_generic_not_found_error_with_uuid
    )

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_contains_severity_info_latest(
    processed_log_entry_generic_not_found_error_latest: ProcessedLogEntry,
) -> None:
    processed_log_entry_generic_not_found_error_latest = dataclasses.replace(
        processed_log_entry_generic_not_found_error_latest, severity="INFO"
    )
    log_is_skipped = generic_not_found_filter(
        processed_log_entry_generic_not_found_error_latest
    )

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_contains_severity_info_version(
    processed_log_entry_generic_not_found_error_version: ProcessedLogEntry,
) -> None:
    processed_log_entry_generic_not_found_error_version = dataclasses.replace(
        processed_log_entry_generic_not_found_error_version, severity="INFO"
    )
    log_is_skipped = generic_not_found_filter(
        processed_log_entry_generic_not_found_error_version
    )

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_contains_severity_info_with_uuid(
    processed_log_entry_generic_not_found_error_with_uuid: ProcessedLogEntry,
) -> None:
    processed_log_entry_generic_not_found_error_with_uuid = dataclasses.replace(
        processed_log_entry_generic_not_found_error_with_uuid, severity="INFO"
    )
    log_is_skipped = generic_not_found_filter(
        processed_log_entry_generic_not_found_error_with_uuid
    )

    assert log_is_skipped is False


def test_log_message_is_skipped_for_different_uuids(
    processed_log_entry_generic_not_found_error_with_uuid: ProcessedLogEntry,
) -> None:
    uuids = [
        "75172346-8454-4d2a-9c43-68d11a246e9f",
        "d649b442-8700-4a12-9718-df3eb8b3cc47",
        "2fe741af-b0cd-4674-86cf-c9af03fd4967",
        "6568e9ec-3d4a-4778-a1d3-af58553134d3",
        "2da2ada0-11d3-43ec-8c2b-46dacf056e13",
        "faabd683-3f78-476f-967f-16fd24a13247",
        "910f5b2a-aa01-459b-b36d-e983aafc1c6b",
        "850d6598-b2b2-418d-9bfc-c79676463076",
        "79cce210-187e-4c0c-8b38-4efe12e4c88e",
    ]

    for uuid in uuids:
        processed_log_entry_generic_not_found_error_with_uuid = dataclasses.replace(
            processed_log_entry_generic_not_found_error_with_uuid,
            message=f'alert: ERROR: [AuditLog] generic::not_found: Failed to fetch "{uuid}"',
        )
        log_is_skipped = generic_not_found_filter(
            processed_log_entry_generic_not_found_error_with_uuid
        )
        assert log_is_skipped is True, f"Log was not skipped for UUID: {uuid}"


def test_log_message_is_not_skipped_when_uuid_format_is_incorrect(
    processed_log_entry_generic_not_found_error_with_uuid: ProcessedLogEntry,
) -> None:
    processed_log_entry_generic_not_found_error_with_uuid = dataclasses.replace(
        processed_log_entry_generic_not_found_error_with_uuid,
        message='alert: ERROR: [AuditLog] generic::not_found: Failed to fetch "65618e9ec-3d4a-4778-a1d3-af58553134d3"',
    )
    log_is_skipped = generic_not_found_filter(
        processed_log_entry_generic_not_found_error_with_uuid
    )

    assert log_is_skipped is False
