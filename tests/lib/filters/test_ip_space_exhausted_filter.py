import pytest
import datetime
import dataclasses

from lib.log_processor import ProcessedLogEntry
from lib.filters.ip_space_exhausted_filter import ip_space_exhausted_filter


@pytest.fixture()
def processed_log_entry_IP_space_exhausted() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="IP_SPACE_EXHAUSTED",
        data=dict(description="2023-06-06 14:36:14Z: IP_SPACE_EXHAUSTED\r\n"),
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


def test_log_is_IP_space_exhausted(
    processed_log_entry_IP_space_exhausted: ProcessedLogEntry,
):
    log_is_skipped = ip_space_exhausted_filter(processed_log_entry_IP_space_exhausted)

    assert log_is_skipped is True


def test_log_platform_is_not_a_string(
    processed_log_entry_IP_space_exhausted: ProcessedLogEntry,
):
    processed_log_entry_IP_space_exhausted = dataclasses.replace(
        processed_log_entry_IP_space_exhausted, platform=123
    )
    log_is_skipped = ip_space_exhausted_filter(processed_log_entry_IP_space_exhausted)

    assert log_is_skipped is False


def test_log_platform_not_gce_instance_in_IP_space_exhausted(
    processed_log_entry_IP_space_exhausted: ProcessedLogEntry,
):
    processed_log_entry_IP_space_exhausted = dataclasses.replace(
        processed_log_entry_IP_space_exhausted, platform="not_gce_instance"
    )
    log_is_skipped = ip_space_exhausted_filter(processed_log_entry_IP_space_exhausted)

    assert log_is_skipped is False


def test_log_message_is_not_a_string_in_IP_space_exhausted(
    processed_log_entry_IP_space_exhausted: ProcessedLogEntry,
):
    processed_log_entry_IP_space_exhausted = dataclasses.replace(
        processed_log_entry_IP_space_exhausted, message=123
    )
    log_is_skipped = ip_space_exhausted_filter(processed_log_entry_IP_space_exhausted)

    assert log_is_skipped is False


def test_IP_space_exhausted_is_not_in_message(
    processed_log_entry_IP_space_exhausted: ProcessedLogEntry,
):
    processed_log_entry_IP_space_exhausted = dataclasses.replace(
        processed_log_entry_IP_space_exhausted, message="IP_SPACE_is_not_EXHAUSTED"
    )
    log_is_skipped = ip_space_exhausted_filter(processed_log_entry_IP_space_exhausted)

    assert log_is_skipped is False
