import pytest
import datetime
import dataclasses

from lib.log_processor import ProcessedLogEntry
from lib.filters.ip_space_exhausted_filter import ip_space_exhausted_filter


@pytest.fixture()
def processed_log_entry_IP_space_exhausted() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="foo",
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


def test_log_is_from_gce_instance_when_IP_space_exhausted(
    processed_log_entry_IP_space_exhausted: ProcessedLogEntry,
):
    log_is_skipped = ip_space_exhausted_filter(processed_log_entry_IP_space_exhausted)

    assert log_is_skipped is True


def test_log_is_not_from_gce_instance_when_IP_space_exhausted(
    processed_log_entry_IP_space_exhausted: ProcessedLogEntry,
):
    processed_log_entry_IP_space_exhausted = dataclasses.replace(
        processed_log_entry_IP_space_exhausted, platform="not_gce_instance"
    )
    log_is_skipped = ip_space_exhausted_filter(processed_log_entry_IP_space_exhausted)

    assert log_is_skipped is False


def test_log_data_is_dict_and_has_description_when_IP_space_exhausted(
    processed_log_entry_IP_space_exhausted: ProcessedLogEntry,
):
    log_is_skipped = ip_space_exhausted_filter(processed_log_entry_IP_space_exhausted)

    assert log_is_skipped is True


def test_log_data_is_dict_but_no_description_when_IP_space_exhausted(
    processed_log_entry_IP_space_exhausted: ProcessedLogEntry,
):
    processed_log_entry_IP_space_exhausted = dataclasses.replace(
        processed_log_entry_IP_space_exhausted, data=dict(source_name="gcp")
    )
    log_is_skipped = ip_space_exhausted_filter(processed_log_entry_IP_space_exhausted)

    assert log_is_skipped is False


def test_log_data_is_not_dict_and_no_description_when_IP_space_exhausted(
    processed_log_entry_IP_space_exhausted: ProcessedLogEntry,
):
    processed_log_entry_IP_space_exhausted = dataclasses.replace(
        processed_log_entry_IP_space_exhausted, data="no-relevant-data"
    )
    log_is_skipped = ip_space_exhausted_filter(processed_log_entry_IP_space_exhausted)

    assert log_is_skipped is False


def test_log_data_description_has_target_text_when_IP_space_exhausted(
    processed_log_entry_IP_space_exhausted: ProcessedLogEntry,
):
    log_is_skipped = ip_space_exhausted_filter(processed_log_entry_IP_space_exhausted)

    assert log_is_skipped is True


def test_log_data_description_has_no_target_text_when_IP_space_exausted(
    processed_log_entry_IP_space_exhausted: ProcessedLogEntry,
):
    processed_log_entry_IP_space_exhausted = dataclasses.replace(
        processed_log_entry_IP_space_exhausted,
        data=dict(description="ERROR: there is no relevant data descrtiption"),
    )
    log_is_skipped = ip_space_exhausted_filter(processed_log_entry_IP_space_exhausted)

    assert log_is_skipped is False
