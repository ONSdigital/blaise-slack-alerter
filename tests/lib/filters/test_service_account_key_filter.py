import pytest
import datetime
import dataclasses

from lib.log_processor import ProcessedLogEntry
from lib.filters.service_account_key_filter import service_account_key_filter


@pytest.fixture()
def processed_service_account_key_error() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message='Service account key 8fb56338d14c4624c7687dfd50ad4b66357d224a does not exist.',
        data=dict(description="dummy"),
        severity="ERROR",
        platform="service_account",
        application="unknown",
        log_name="projects/ons-blaise-v2-prod/logs/run.googleapis.com%2Fstderr",
        timestamp=datetime.datetime(2023, 2, 25, 3, 46, 57, 99633),
        log_query={
            "resource.type": "service_account",
            "resource.labels.instance_id": "458491777778639951",
        },
    )

def test_log_is_skipped_when_its_from_service_account_when_service_account_key_error(
    processed_log_entry_service_account_key_error: ProcessedLogEntry,
):
    log_is_skipped = service_account_key_filter(processed_log_entry_service_account_key_error)
    assert log_is_skipped is True


def test_log_message_is_not_a_string_when_service_account_key_error(
    processed_log_entry_service_account_key_error: ProcessedLogEntry,
):
    processed_log_entry_service_account_key_error = dataclasses.replace(
        processed_log_entry_service_account_key_error, message=1234
    )
    log_is_skipped = service_account_key_filter(processed_log_entry_service_account_key_error)

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_contains_severity_info_for_service_account_key_error(
    processed_log_entry_service_account_key_error: ProcessedLogEntry,
):
    processed_log_entry_service_account_key_error = dataclasses.replace(
        processed_log_entry_service_account_key_error, severity="INFO"
    )
    log_is_skipped = service_account_key_filter(processed_log_entry_service_account_key_error)

    assert log_is_skipped is False

def test_log_message_does_not_contain_service_account_key(
    processed_log_entry_service_account_key_error: ProcessedLogEntry,
):
    processed_log_entry_service_account_key_error = dataclasses.replace(
        processed_log_entry_service_account_key_error,
        message="some other message",
    )
    log_is_skipped = service_account_key_filter(processed_log_entry_service_account_key_error)
    assert log_is_skipped is False


@pytest.mark.parametrize(
    "account_key",
    [
        "8fa56330d10b6624c7687ddd50ad4b86347d224a",
        "f7ade4740059a1f5137bea2ff20b0952f012cf17",
        "170277cc2e4b598b9d60542b5a17ee3c779e4112",
        "e8bc6052cdfdb71b7fca130dd9ff815c4b8a6421",
    ],
)
def test_log_message_is_correct_format_for_different_service_account_keys(
    processed_log_entry_service_account_key_error: ProcessedLogEntry, account_key: str
):
    processed_log_entry_service_account_key_error = dataclasses.replace(
        processed_log_entry_service_account_key_error,
        message=f"Service account key {account_key} does not exist.",
    )
    log_is_skipped = service_account_key_filter(processed_log_entry_service_account_key_error)
    assert log_is_skipped is True


@pytest.mark.parametrize(
    "invalid_account_key",
    [
        "GFA56330D10B6624C7687DDD50AD4B86347D224A",
        "1234567890abcdef",
        "z7ade4740059a1f5137bea2ff20b0952f012cf17",
        "170277cc2e4b598b9d60542b5a17ee3c779e41122",
        "service-key-1234567890123456789012345678901234567890",
    ],
)
def test_log_message_is_incorrect_format_for_service_account_key(
    processed_log_entry_service_account_key_error: ProcessedLogEntry, invalid_account_key: str
):
    processed_log_entry_service_account_key_error = dataclasses.replace(
        processed_log_entry_service_account_key_error,
        message=f"Service account key {invalid_account_key} does not exist.",
    )
    log_is_skipped = service_account_key_filter(processed_log_entry_service_account_key_error)
    assert log_is_skipped is False
