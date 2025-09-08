from typing import cast
import pytest
import datetime
import dataclasses

from lib.log_processor.processed_log_entry import ProcessedLogEntry
from lib.filters.auditlog_filter import auditlog_filter


@pytest.fixture()
def process_log_entry() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="OSConfigAgent Error main.go:231: unexpected end of JSON input",
        data={
            "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
            "methodName": "storage.objects.list",
        },
        severity="ERROR",
        platform="gce_instance",
        application="blaise-gusty-data-entry-1",
        log_name="/logs/gce-example",
        timestamp=datetime.datetime(2023, 2, 25, 3, 46, 57, 99633),
        log_query={
            "resource.type": "gce_instance",
            "resource.labels.instance_id": "458491889528639951",
        },
    )


@pytest.mark.parametrize(
    "method_name",
    [
        "storage.objects.list",
        "storage.objects.get",
        "storage.buckets.list",
        "storage.buckets.get",
    ],
)
def test_log_is_skipped_when_methodname_contains_storage(
    process_log_entry: ProcessedLogEntry, method_name: str
) -> None:
    cast(dict, process_log_entry.data)["methodName"] = method_name
    log_is_skipped = auditlog_filter(process_log_entry)

    assert log_is_skipped is True


def test_log_is_not_skipped_when_methodname_does_not_contain_storage(
    process_log_entry: ProcessedLogEntry,
) -> None:
    cast(dict, process_log_entry.data)["methodName"] = "method"
    log_is_skipped = auditlog_filter(process_log_entry)

    assert log_is_skipped is False


def test_log_is_not_skipped_when_type_is_not_auditlog(
    process_log_entry: ProcessedLogEntry,
) -> None:
    cast(dict, process_log_entry.data)["@type"] = "not_audit_log"
    log_is_skipped = auditlog_filter(process_log_entry)

    assert log_is_skipped is False


def test_log_is_not_skipped_when_methjod_name_does_not_exist(
    process_log_entry: ProcessedLogEntry,
) -> None:
    del cast(dict, process_log_entry.data)["methodName"]
    log_is_skipped = auditlog_filter(process_log_entry)

    assert log_is_skipped is False
