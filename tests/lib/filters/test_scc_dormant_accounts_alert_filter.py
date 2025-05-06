import pytest
import datetime
import dataclasses

from lib.log_processor import ProcessedLogEntry
from lib.filters.scc_dormant_accounts_alert_filter import (
    scc_dormant_accounts_alert_filter,
)

SERVICE_ACCOUNT_EMAILS = {
    "target_external_service_account": "scc-dormant-accounts-alert@ons-gcp-monitoring-prod.iam.gserviceaccount.com",
    "random_external_service_account": "google-service-account@example.com",
}


POTENTIAL_ERROR_MESSAGES = {
    "key_error": "Service account key 8fb56338d14c4624c7687dfd50ad4b66357d224a does not exist.",
    "account_error": "Service account projects/ons-blaise-v2-prod/serviceAccounts/blaise-cloud-functions@ons-blaise-v2-prod.iam.gserviceaccount.com does not exist.",
}


@pytest.fixture()
def processed_scc_dormant_accounts_alert_log() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message=POTENTIAL_ERROR_MESSAGES["key_error"],
        data=dict(
            description="dummy",
            authenticationInfo=dict(
                principalEmail=SERVICE_ACCOUNT_EMAILS[
                    "target_external_service_account"
                ],
            ),
        ),
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


def test_log_is_skipped_when_its_from_external_service_account(
    processed_scc_dormant_accounts_alert_log: ProcessedLogEntry,
):
    log_is_skipped = scc_dormant_accounts_alert_filter(
        processed_scc_dormant_accounts_alert_log
    )
    assert log_is_skipped is True


def test_log_is_skipped_when_its_a_service_account_not_found__error(
    processed_scc_dormant_accounts_alert_log: ProcessedLogEntry,
):
    processed_scc_dormant_accounts_alert_log = dataclasses.replace(
        processed_scc_dormant_accounts_alert_log,
        message=POTENTIAL_ERROR_MESSAGES["account_error"],
    )
    log_is_skipped = scc_dormant_accounts_alert_filter(
        processed_scc_dormant_accounts_alert_log
    )

    assert log_is_skipped is True


def test_log_is_not_skipped_when_message_is_not_a_string(
    processed_scc_dormant_accounts_alert_log: ProcessedLogEntry,
):
    processed_scc_dormant_accounts_alert_log = dataclasses.replace(
        processed_scc_dormant_accounts_alert_log, message=1234
    )
    log_is_skipped = scc_dormant_accounts_alert_filter(
        processed_scc_dormant_accounts_alert_log
    )

    assert log_is_skipped is False


def test_log_is_not_skipped_when_it_contains_a_different_service_account(
    processed_scc_dormant_accounts_alert_log: ProcessedLogEntry,
):
    processed_scc_dormant_accounts_alert_log = dataclasses.replace(
        processed_scc_dormant_accounts_alert_log,
        data=dict(
            description="dummy",
            authenticationInfo=dict(
                principalEmail=SERVICE_ACCOUNT_EMAILS[
                    "random_external_service_account"
                ],
            ),
        ),
        message="Message from a different service account",
    )
    log_is_skipped = scc_dormant_accounts_alert_filter(
        processed_scc_dormant_accounts_alert_log
    )
    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_contains_severity_error_from_a_different_service_account(
    processed_scc_dormant_accounts_alert_log: ProcessedLogEntry,
):
    processed_scc_dormant_accounts_alert_log = dataclasses.replace(
        processed_scc_dormant_accounts_alert_log,
        data=dict(
            description="dummy",
            authenticationInfo=dict(
                principalEmail=SERVICE_ACCOUNT_EMAILS[
                    "random_external_service_account"
                ],
            ),
        ),
        severity="ERROR",
    )
    log_is_skipped = scc_dormant_accounts_alert_filter(
        processed_scc_dormant_accounts_alert_log
    )

    assert log_is_skipped is False


def test_log_is_not_skipped_when_it_does_not_contain_a_valid_service_account(
    processed_scc_dormant_accounts_alert_log: ProcessedLogEntry,
):
    processed_scc_dormant_accounts_alert_log = dataclasses.replace(
        processed_scc_dormant_accounts_alert_log,
        data=dict(
            description="dummy",
            authenticationInfo=dict(
                principalEmail=123,
            ),
        ),
        message="Invalid service account",
    )
    log_is_skipped = scc_dormant_accounts_alert_filter(
        processed_scc_dormant_accounts_alert_log
    )
    assert log_is_skipped is False
