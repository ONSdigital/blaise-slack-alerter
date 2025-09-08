import dataclasses
import datetime
import typing

import pytest

from lib.filters.get_role_filter import get_role_filter
from lib.log_processor.processed_log_entry import ProcessedLogEntry


@pytest.fixture()
def processed_log_entry_get_role() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="You don't have permission to get the role at projects/ons-blaise-v2-prod/roles/CustomConcourseSARole.",
        data=dict(methodName="google.iam.admin.v1.GetRole"),
        severity="ERROR",
        platform="unknown",
        application="unknown",
        log_name="projects/ons-blaise-v2-prod/logs/cloudaudit.googleapis.com%2Fdata_access",
        timestamp=datetime.datetime(2024, 8, 2, 5, 52, 34, 24221),
        log_query={
            "resource.type": "iam.roles",
            "resource.labels.database_id": "ons-blaise-v2-prod",
        },
    )


def test_log_is_skipped_when_get_role(
    processed_log_entry_get_role: ProcessedLogEntry,
) -> None:
    log_is_skipped = get_role_filter(processed_log_entry_get_role)
    assert log_is_skipped is True


def test_log_message_is_not_a_string_when_get_role(
    processed_log_entry_get_role: ProcessedLogEntry,
) -> None:
    processed_log_entry_get_role = dataclasses.replace(
        processed_log_entry_get_role, message=typing.cast(typing.Any, 1234)
    )
    log_is_skipped = get_role_filter(processed_log_entry_get_role)

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_does_not_contain_get_role(
    processed_log_entry_get_role: ProcessedLogEntry,
) -> None:
    processed_log_entry_get_role = dataclasses.replace(
        processed_log_entry_get_role, message="dummy"
    )
    log_is_skipped = get_role_filter(processed_log_entry_get_role)

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_contains_severity_info(
    processed_log_entry_get_role: ProcessedLogEntry,
) -> None:
    processed_log_entry_get_role = dataclasses.replace(
        processed_log_entry_get_role, severity="INFO"
    )
    log_is_skipped = get_role_filter(processed_log_entry_get_role)

    assert log_is_skipped is False
