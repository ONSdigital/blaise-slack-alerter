import pytest
import datetime
import dataclasses

from lib.log_processor import ProcessedLogEntry
from lib.filters.osconfig_agent_filter import osconfig_agent_filter


@pytest.fixture()
def processed_log_entry_unexpected_end_of_json() -> ProcessedLogEntry:
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


@pytest.fixture()
def processed_log_entry_context_deadline_exceeded() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="Error: context deadline exceeded",
        data=dict(omitempty="null", localTimestamp="2023-03-30T16:12:02.8996+01:00"),
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


def test_log_is_from_gce_instance_when_context_deadline_exceeded(
    processed_log_entry_context_deadline_exceeded: ProcessedLogEntry,
):
    log_is_skipped = osconfig_agent_filter(
        processed_log_entry_context_deadline_exceeded
    )

    assert log_is_skipped == True


def test_log_is_from_gce_instance_when_unexpected_end_of_json(
    processed_log_entry_unexpected_end_of_json: ProcessedLogEntry,
):
    log_is_skipped = osconfig_agent_filter(processed_log_entry_unexpected_end_of_json)

    assert log_is_skipped == True


def test_log_is_not_from_gce_instance_when_unexpected_end_of_json(
    processed_log_entry_unexpected_end_of_json: ProcessedLogEntry,
):
    processed_log_entry_unexpected_end_of_json = dataclasses.replace(
        processed_log_entry_unexpected_end_of_json, platform="not_gce_instance"
    )
    log_is_skipped = osconfig_agent_filter(processed_log_entry_unexpected_end_of_json)

    assert log_is_skipped == False


def test_log_data_is_dict_and_has_description_when_unexpected_end_of_json(
    processed_log_entry_unexpected_end_of_json: ProcessedLogEntry,
):
    log_is_skipped = osconfig_agent_filter(processed_log_entry_unexpected_end_of_json)

    assert log_is_skipped == True


def test_log_data_is_dict_but_no_description_when_unexpected_end_of_json(
    processed_log_entry_unexpected_end_of_json: ProcessedLogEntry,
):
    processed_log_entry_unexpected_end_of_json = dataclasses.replace(
        processed_log_entry_unexpected_end_of_json, data=dict(source_name="gcp")
    )
    log_is_skipped = osconfig_agent_filter(processed_log_entry_unexpected_end_of_json)

    assert log_is_skipped == False


def test_log_data_is_not_dict_and_no_description_when_unexpected_end_of_json(
    processed_log_entry_unexpected_end_of_json: ProcessedLogEntry,
):
    processed_log_entry_unexpected_end_of_json = dataclasses.replace(
        processed_log_entry_unexpected_end_of_json, data="no-relevant-data"
    )
    log_is_skipped = osconfig_agent_filter(processed_log_entry_unexpected_end_of_json)

    assert log_is_skipped == False


def test_log_data_description_has_target_text_when_unexpected_end_of_json(
    processed_log_entry_unexpected_end_of_json: ProcessedLogEntry,
):
    log_is_skipped = osconfig_agent_filter(processed_log_entry_unexpected_end_of_json)

    assert log_is_skipped == True


def test_log_data_description_has_no_target_text_when_unexpected_end_of_json(
    processed_log_entry_unexpected_end_of_json: ProcessedLogEntry,
):
    processed_log_entry_unexpected_end_of_json = dataclasses.replace(
        processed_log_entry_unexpected_end_of_json,
        data=dict(description="ERROR: there is no relevant data descrtiption"),
    )
    log_is_skipped = osconfig_agent_filter(processed_log_entry_unexpected_end_of_json)

    assert log_is_skipped == False
