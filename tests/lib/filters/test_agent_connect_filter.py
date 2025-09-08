import dataclasses
import datetime

import pytest

from lib.filters.agent_connect_filter import agent_connect_filter
from lib.log_processor.processed_log_entry import ProcessedLogEntry


@pytest.fixture()
def processed_log_entry_agent_connect_error() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="Agent Connect Error main.go:231: unexpected end of JSON input",
        data=dict(
            description="2023-06-06 14:36:14Z: Agent connect error: The HTTP request timed out after 00:01:00.. Retrying until reconnected.\r\n"
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


def test_log_is_from_gce_instance_when_agent_connect_error(
    processed_log_entry_agent_connect_error: ProcessedLogEntry,
) -> None:
    log_is_skipped = agent_connect_filter(processed_log_entry_agent_connect_error)

    assert log_is_skipped is True


def test_log_is_not_from_gce_instance_when_agent_connect_error(
    processed_log_entry_agent_connect_error: ProcessedLogEntry,
) -> None:
    processed_log_entry_agent_connect_error = dataclasses.replace(
        processed_log_entry_agent_connect_error, platform="not_gce_instance"
    )
    log_is_skipped = agent_connect_filter(processed_log_entry_agent_connect_error)

    assert log_is_skipped is False


def test_log_data_is_dict_and_has_description_when_agent_connect_error(
    processed_log_entry_agent_connect_error: ProcessedLogEntry,
) -> None:
    log_is_skipped = agent_connect_filter(processed_log_entry_agent_connect_error)

    assert log_is_skipped is True


def test_log_data_is_dict_but_no_description_when_agent_connect_error(
    processed_log_entry_agent_connect_error: ProcessedLogEntry,
) -> None:
    processed_log_entry_agent_connect_error = dataclasses.replace(
        processed_log_entry_agent_connect_error, data=dict(source_name="gcp")
    )
    log_is_skipped = agent_connect_filter(processed_log_entry_agent_connect_error)

    assert log_is_skipped is False


def test_log_data_is_not_dict_and_no_description_when_agent_connect_error(
    processed_log_entry_agent_connect_error: ProcessedLogEntry,
) -> None:
    processed_log_entry_agent_connect_error = dataclasses.replace(
        processed_log_entry_agent_connect_error, data="no-relevant-data"
    )
    log_is_skipped = agent_connect_filter(processed_log_entry_agent_connect_error)

    assert log_is_skipped is False


def test_log_data_description_has_target_text_when_agent_connect_error(
    processed_log_entry_agent_connect_error: ProcessedLogEntry,
) -> None:
    log_is_skipped = agent_connect_filter(processed_log_entry_agent_connect_error)

    assert log_is_skipped is True


def test_log_data_description_has_no_target_text_when_agent_connect_error(
    processed_log_entry_agent_connect_error: ProcessedLogEntry,
) -> None:
    processed_log_entry_agent_connect_error = dataclasses.replace(
        processed_log_entry_agent_connect_error,
        data=dict(description="ERROR: there is no relevant data descrtiption"),
    )
    log_is_skipped = agent_connect_filter(processed_log_entry_agent_connect_error)

    assert log_is_skipped is False
