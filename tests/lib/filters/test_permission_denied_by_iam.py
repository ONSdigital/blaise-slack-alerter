import dataclasses
import datetime
import typing

import pytest

from lib.filters.permission_denied_by_iam_filter import \
    permission_denied_by_iam_filter
from lib.log_processor.processed_log_entry import ProcessedLogEntry


@pytest.fixture()
def processed_log_entry_permission_denied_by_iam_error() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="[AuditLog] permission denied by IAM",
        data=dict(
            requestMetadata={
                "callerIp": "5.161.230.161",
                "callerSuppliedUserAgent": "Fuzz Faster U Fool v2.1.0,gzip(gfe)",
            }
        ),
        severity="ERROR",
        platform="audited_resource",
        application="unknown",
        log_name="/logs/cloudfunctions",
        timestamp=datetime.datetime(2024, 4, 18, 6, 22, 54, 24321),
        log_query={
            "resource.type": "cloud_run_revision",
            "resource.labels.instance_id": "234023940239340394",
        },
    )


def test_log_is_skipped_when_its_from_cloud_run_revision_when_permission_denied_by_iam_error(
    processed_log_entry_permission_denied_by_iam_error: ProcessedLogEntry,
) -> None:
    log_is_skipped = permission_denied_by_iam_filter(
        processed_log_entry_permission_denied_by_iam_error
    )
    assert log_is_skipped is True


def test_log_message_is_not_a_string_when_permission_denied_by_iam_error(
    processed_log_entry_permission_denied_by_iam_error: ProcessedLogEntry,
) -> None:
    processed_log_entry_permission_denied_by_iam_error = dataclasses.replace(
        processed_log_entry_permission_denied_by_iam_error,
        message=typing.cast(typing.Any, 1234),
    )
    log_is_skipped = permission_denied_by_iam_filter(
        processed_log_entry_permission_denied_by_iam_error
    )

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_does_not_contain_permission_denied_by_iam_error(
    processed_log_entry_permission_denied_by_iam_error: ProcessedLogEntry,
) -> None:
    processed_log_entry_permission_denied_by_iam_error = dataclasses.replace(
        processed_log_entry_permission_denied_by_iam_error, message="foo"
    )
    log_is_skipped = permission_denied_by_iam_filter(
        processed_log_entry_permission_denied_by_iam_error
    )

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_contains_severity_info(
    processed_log_entry_permission_denied_by_iam_error: ProcessedLogEntry,
) -> None:
    processed_log_entry_permission_denied_by_iam_error = dataclasses.replace(
        processed_log_entry_permission_denied_by_iam_error, severity="INFO"
    )
    log_is_skipped = permission_denied_by_iam_filter(
        processed_log_entry_permission_denied_by_iam_error
    )

    assert log_is_skipped is False
