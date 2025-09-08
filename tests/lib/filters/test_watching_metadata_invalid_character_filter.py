import dataclasses
import datetime

import pytest

from lib.filters.watching_metadata_invalid_character_filter import \
    watching_metadata_invalid_character_filter
from lib.log_processor.processed_log_entry import ProcessedLogEntry


@pytest.fixture()
def processed_log_entry_watching_metadata_invalid_character_error() -> (
    ProcessedLogEntry
):
    return ProcessedLogEntry(
        message="Error watching metadata: invalid character '<' looking for beginning of value",
        data={
            "localTimestamp": "2023-09-18T15:12:28.8451+01:00",
            "message": "Error watching metadata: invalid character '<' looking for beginning of value",
            "omitempty": None,
        },
        severity="ERROR",
        platform="gce_instance",
        application="blaise-gusty-data-entry-4",
        log_name="projects/ons-blaise-v2-prod/logs/GCEGuestAgent",
        timestamp=datetime.datetime(2023, 9, 18, 15, 12, 30, 225541),
        log_query={"resource.type": "gce_instance"},
    )


def test_log_is_a_valid_watching_metadata_invalid_character_error(
    processed_log_entry_watching_metadata_invalid_character_error: ProcessedLogEntry,
) -> None:
    log_is_skipped = watching_metadata_invalid_character_filter(
        processed_log_entry_watching_metadata_invalid_character_error
    )

    assert log_is_skipped is True


def test_log_is_not_from_gce_instance_when_watching_metadata_invalid_character_error(
    processed_log_entry_watching_metadata_invalid_character_error: ProcessedLogEntry,
) -> None:
    processed_log_entry_watching_metadata_invalid_character_error = dataclasses.replace(
        processed_log_entry_watching_metadata_invalid_character_error,
        platform="not_gce_instance",
    )
    log_is_skipped = watching_metadata_invalid_character_filter(
        processed_log_entry_watching_metadata_invalid_character_error
    )

    assert log_is_skipped is False


def test_log_is_not_from_GCEGuestAgent_when_watching_metadata_invalid_character_error(
    processed_log_entry_watching_metadata_invalid_character_error: ProcessedLogEntry,
) -> None:
    processed_log_entry_watching_metadata_invalid_character_error = dataclasses.replace(
        processed_log_entry_watching_metadata_invalid_character_error,
        log_name="not_valid_value",
    )
    log_is_skipped = watching_metadata_invalid_character_filter(
        processed_log_entry_watching_metadata_invalid_character_error
    )

    assert log_is_skipped is False


def test_second_version_log_if_logName_is_Not_explicitly_GCEGuestAgent_when_watching_metadata_invalid_character_error(
    processed_log_entry_watching_metadata_invalid_character_error: ProcessedLogEntry,
) -> None:
    processed_log_entry_watching_metadata_invalid_character_error = dataclasses.replace(
        processed_log_entry_watching_metadata_invalid_character_error,
        message="2023/10/10 23:06:39 GCEGuestAgent: Error watching metadata: invalid character '<' looking for beginning of value\r\n",
        log_name="projects/ons-blaise-v2-prod/logs/winevt.raw",
    )
    log_is_skipped = watching_metadata_invalid_character_filter(
        processed_log_entry_watching_metadata_invalid_character_error
    )

    assert log_is_skipped is True
