import pytest
import datetime
import dataclasses
from typing import Any

from lib.log_processor import ProcessedLogEntry
from lib.filters.scc_dormant_accounts_prod_alert_filter import (
    scc_dormant_accounts_prod_alert_filter,
)


# Test constants
TARGET_SERVICE_ACCOUNT = (
    "scc-dormant-accounts-alert@ons-gcp-monitoring-prod.iam.gserviceaccount.com"
)
RANDOM_SERVICE_ACCOUNT = "google-service-account@example.com"
SERVICE_ACCOUNT_KEY_ERROR = (
    "Service account key test8fb56338d14c4624c7687dfd50ad4b66357d224a does not exist."
)
SERVICE_ACCOUNT_NOT_FOUND_ERROR = "Service account projects/ons-blaise-v2-prod/serviceAccounts/blaise-cloud-functions-test@ons-blaise-v2-prod.iam.gserviceaccount.com does not exist."


@pytest.fixture
def base_scc_log() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="dummy",
        data={
            "description": "dummy",
            "authenticationInfo": {
                "principalEmail": TARGET_SERVICE_ACCOUNT,
            },
        },
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


def create_log_with_field(
    base_log: ProcessedLogEntry, **kwargs: Any
) -> ProcessedLogEntry:
    return dataclasses.replace(base_log, **kwargs)


def create_log_with_message(
    base_log: ProcessedLogEntry, message: str
) -> ProcessedLogEntry:
    return dataclasses.replace(base_log, message=message)


def create_log_with_data(base_log: ProcessedLogEntry, data: Any) -> ProcessedLogEntry:
    return dataclasses.replace(base_log, data=data)


def test_log_is_skipped_when_from_target_service_account(
    base_scc_log: ProcessedLogEntry,
):
    assert scc_dormant_accounts_prod_alert_filter(base_scc_log) is True


@pytest.mark.parametrize(
    "error_message",
    [
        SERVICE_ACCOUNT_KEY_ERROR,
        SERVICE_ACCOUNT_NOT_FOUND_ERROR,
    ],
)
def test_log_is_skipped_for_service_account_errors(
    base_scc_log: ProcessedLogEntry, error_message: str
):
    log = create_log_with_message(base_scc_log, error_message)
    assert scc_dormant_accounts_prod_alert_filter(log) is True


def test_log_is_not_skipped_when_log_entry_is_none():
    assert scc_dormant_accounts_prod_alert_filter(None) is False


@pytest.mark.parametrize("invalid_platform", [123, "different_platform", None])
def test_log_is_not_skipped_for_invalid_platform(
    base_scc_log: ProcessedLogEntry, invalid_platform: Any
):
    log = create_log_with_field(base_scc_log, platform=invalid_platform)
    assert scc_dormant_accounts_prod_alert_filter(log) is False


@pytest.mark.parametrize(
    "invalid_data",
    [
        "not_a_dict",
        {"description": "dummy", "authenticationInfo": "not_a_dict"},
        {"description": "dummy"},
        {"description": "dummy", "authenticationInfo": {}},
    ],
)
def test_log_is_not_skipped_for_invalid_data(
    base_scc_log: ProcessedLogEntry, invalid_data: Any
):
    log = create_log_with_data(base_scc_log, invalid_data)
    assert scc_dormant_accounts_prod_alert_filter(log) is False


@pytest.mark.parametrize("invalid_message", [1234, None, []])
def test_log_is_not_skipped_for_invalid_message(
    base_scc_log: ProcessedLogEntry, invalid_message: Any
):
    log = create_log_with_field(base_scc_log, message=invalid_message)
    assert scc_dormant_accounts_prod_alert_filter(log) is False


def test_log_is_not_skipped_for_different_service_account(
    base_scc_log: ProcessedLogEntry,
):
    data = {
        "description": "dummy",
        "authenticationInfo": {
            "principalEmail": RANDOM_SERVICE_ACCOUNT,
        },
    }
    log = create_log_with_data(base_scc_log, data)
    log = create_log_with_message(log, SERVICE_ACCOUNT_KEY_ERROR)
    assert scc_dormant_accounts_prod_alert_filter(log) is False


def test_log_is_not_skipped_for_invalid_principal_email_type(
    base_scc_log: ProcessedLogEntry,
):
    data = {
        "description": "dummy",
        "authenticationInfo": {
            "principalEmail": 123,  # Invalid type
        },
    }
    log = create_log_with_data(base_scc_log, data)
    log = create_log_with_message(log, "Invalid service account")
    assert scc_dormant_accounts_prod_alert_filter(log) is False


@pytest.mark.parametrize("invalid_severity", ["INFO", "WARNING", "DEBUG", None, 123])
def test_log_is_not_skipped_for_invalid_severity(
    base_scc_log: ProcessedLogEntry, invalid_severity: Any
):
    log = create_log_with_field(base_scc_log, severity=invalid_severity)
    assert scc_dormant_accounts_prod_alert_filter(log) is False
