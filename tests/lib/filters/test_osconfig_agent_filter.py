import pytest
import datetime
import dataclasses

from lib.log_processor import ProcessedLogEntry
from lib.filters.osconfig_agent_filter import osconfig_agent_filter


@pytest.fixture()
def processed_log_entry() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="OSConfigAgent Error main.go:231: unexpected end of JSON input",
        data=dict(
            description="2023-02-25T03:46:49.1619Z OSConfigAgent Error main.go:231: unexpected end of JSON input\r\n"
        ),
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


def test_log_is_from_gce_instance(processed_log_entry: ProcessedLogEntry):
    log_is_skipped = osconfig_agent_filter(processed_log_entry)

    assert log_is_skipped == True


def test_log_is_not_from_gce_instance(processed_log_entry: ProcessedLogEntry):
    processed_log_entry = dataclasses.replace(
        processed_log_entry, platform="not_gce_instance"
    )
    log_is_skipped = osconfig_agent_filter(processed_log_entry)

    assert log_is_skipped == False


def test_log_data_is_dict_and_has_description(processed_log_entry: ProcessedLogEntry):
    log_is_skipped = osconfig_agent_filter(processed_log_entry)

    assert log_is_skipped == True


def test_log_data_is_dict_but_no_description(processed_log_entry: ProcessedLogEntry):
    processed_log_entry = dataclasses.replace(
        processed_log_entry, data=dict(source_name="gcp")
    )
    log_is_skipped = osconfig_agent_filter(processed_log_entry)

    assert log_is_skipped == False


def test_log_data_is_not_dict_and_no_description(
    processed_log_entry: ProcessedLogEntry,
):
    processed_log_entry = dataclasses.replace(
        processed_log_entry, data="no-relevant-data"
    )
    log_is_skipped = osconfig_agent_filter(processed_log_entry)

    assert log_is_skipped == False


def test_log_data_description_has_target_text(processed_log_entry: ProcessedLogEntry):
    log_is_skipped = osconfig_agent_filter(processed_log_entry)

    assert log_is_skipped == True


def test_log_data_description_has_no_target_text(
    processed_log_entry: ProcessedLogEntry,
):
    processed_log_entry = dataclasses.replace(
        processed_log_entry,
        data=dict(description="ERROR: there is no relevant data descrtiption"),
    )
    log_is_skipped = osconfig_agent_filter(processed_log_entry)

    assert log_is_skipped == False
