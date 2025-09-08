from typing import Any
import typing
import pytest
import datetime
import dataclasses

from lib.log_processor.processed_log_entry import ProcessedLogEntry
from lib.filters.gcp_constraint_not_found_filter import (
    org_policy_constraint_not_found_filter,
    physical_zone_separation_constraint_filter,
    service_account_hmac_key_constraint_filter,
)

CONSTRAINT_NAMES = {
    "physical_zone_separation": "constraints/gcp.requiresPhysicalZoneSeparation",
    "hmac_key_creation": "constraints/storage.disableServiceAccountHmacKeyCreation",
    "other_constraint": "constraints/compute.requireOsLogin",
}

ERROR_MESSAGES = {
    "physical_zone_constraint_error": "com.google.apps.framework.request.StatusException: <eye3 title='NOT_FOUND'/> generic::NOT_FOUND: No constraint found with name 'constraints/gcp.requiresPhysicalZoneSeparation'.",
    "hmac_key_constraint_error": "com.google.apps.framework.request.StatusException: <eye3 title='NOT_FOUND'/> generic::NOT_FOUND: No constraint found with name 'constraints/storage.disableServiceAccountHmacKeyCreation'.",
    "other_constraint_error": "generic::NOT_FOUND: No constraint found with name 'constraints/compute.requireOsLogin'.",
    "different_error": "Some other error message that should not be filtered",
}


@pytest.fixture()
def processed_org_policy_constraint_log() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message=ERROR_MESSAGES["physical_zone_constraint_error"],
        data=dict(
            serviceName="orgpolicy.googleapis.com",
            methodName="google.cloud.orgpolicy.v2.OrgPolicy.GetEffectivePolicy",
            authenticationInfo=dict(
                principalEmail="john.blaise@example.com",
            ),
        ),
        severity="ERROR",
        platform="audited_resource",
        application="unknown",
        log_name="projects/ons-blaise-v2-prod/logs/cloudaudit.googleapis.com%2Fdata_access",
        timestamp=datetime.datetime(2025, 7, 11, 8, 21, 33, 984397),
        log_query={
            "resource.type": "audited_resource",
            "resource.labels.service": "orgpolicy.googleapis.com",
        },
    )


def test_filter_skips_allowed_physical_zone_separation_constraint_error(
    processed_org_policy_constraint_log: ProcessedLogEntry,
) -> None:
    log_is_skipped = org_policy_constraint_not_found_filter(
        processed_org_policy_constraint_log
    )
    assert log_is_skipped is True


def test_filter_skips_allowed_hmac_key_constraint_error(
    processed_org_policy_constraint_log: ProcessedLogEntry,
) -> None:
    processed_log = dataclasses.replace(
        processed_org_policy_constraint_log,
        message=ERROR_MESSAGES["hmac_key_constraint_error"],
    )
    log_is_skipped = org_policy_constraint_not_found_filter(processed_log)
    assert log_is_skipped is True


def test_filter_does_not_skip_other_constraint_error(
    processed_org_policy_constraint_log: ProcessedLogEntry,
) -> None:
    processed_log = dataclasses.replace(
        processed_org_policy_constraint_log,
        message=ERROR_MESSAGES["other_constraint_error"],
    )
    log_is_skipped = org_policy_constraint_not_found_filter(processed_log)
    assert log_is_skipped is False


def test_specific_physical_zone_filter_skips_correct_constraint(
    processed_org_policy_constraint_log: ProcessedLogEntry,
) -> None:
    log_is_skipped = physical_zone_separation_constraint_filter(
        processed_org_policy_constraint_log
    )
    assert log_is_skipped is True


def test_specific_hmac_key_filter_skips_correct_constraint(
    processed_org_policy_constraint_log: ProcessedLogEntry,
) -> None:
    processed_log = dataclasses.replace(
        processed_org_policy_constraint_log,
        message=ERROR_MESSAGES["hmac_key_constraint_error"],
    )
    log_is_skipped = service_account_hmac_key_constraint_filter(processed_log)
    assert log_is_skipped is True


def test_specific_filters_do_not_skip_other_constraints(
    processed_org_policy_constraint_log: ProcessedLogEntry,
) -> None:
    processed_log = dataclasses.replace(
        processed_org_policy_constraint_log,
        message=ERROR_MESSAGES["other_constraint_error"],
    )
    physical_zone_skipped = physical_zone_separation_constraint_filter(processed_log)
    hmac_key_skipped = service_account_hmac_key_constraint_filter(processed_log)

    assert physical_zone_skipped is False
    assert hmac_key_skipped is False


def test_log_is_not_skipped_when_log_entry_is_none() -> None:
    log_is_skipped = org_policy_constraint_not_found_filter(None)
    assert log_is_skipped is False


def test_log_is_not_skipped_when_severity_is_not_error(
    processed_org_policy_constraint_log: ProcessedLogEntry,
) -> None:
    processed_log = dataclasses.replace(
        processed_org_policy_constraint_log, severity="INFO"
    )
    log_is_skipped = org_policy_constraint_not_found_filter(processed_log)
    assert log_is_skipped is False


def test_log_is_not_skipped_when_platform_is_not_string(
    processed_org_policy_constraint_log: ProcessedLogEntry,
) -> None:
    processed_log = dataclasses.replace(
        processed_org_policy_constraint_log, platform=typing.cast(Any, 123)
    )
    log_is_skipped = org_policy_constraint_not_found_filter(processed_log)
    assert log_is_skipped is False


def test_log_is_not_skipped_when_platform_is_not_audited_resource(
    processed_org_policy_constraint_log: ProcessedLogEntry,
) -> None:
    processed_log = dataclasses.replace(
        processed_org_policy_constraint_log, platform="different_platform"
    )
    log_is_skipped = org_policy_constraint_not_found_filter(processed_log)
    assert log_is_skipped is False


def test_log_is_not_skipped_when_message_is_not_string(
    processed_org_policy_constraint_log: ProcessedLogEntry,
) -> None:
    processed_log = dataclasses.replace(
        processed_org_policy_constraint_log, message=typing.cast(Any, 123)
    )
    log_is_skipped = org_policy_constraint_not_found_filter(processed_log)
    assert log_is_skipped is False


def test_log_is_not_skipped_when_data_is_not_dict(
    processed_org_policy_constraint_log: ProcessedLogEntry,
) -> None:
    processed_log = dataclasses.replace(
        processed_org_policy_constraint_log, data="not_a_dict"
    )
    log_is_skipped = org_policy_constraint_not_found_filter(processed_log)
    assert log_is_skipped is False


def test_log_is_not_skipped_when_service_name_is_not_string(
    processed_org_policy_constraint_log: ProcessedLogEntry,
) -> None:
    processed_log = dataclasses.replace(
        processed_org_policy_constraint_log,
        data={"serviceName": 123, "methodName": "test"},
    )
    log_is_skipped = org_policy_constraint_not_found_filter(processed_log)
    assert log_is_skipped is False


def test_log_is_not_skipped_when_service_name_is_missing(
    processed_org_policy_constraint_log: ProcessedLogEntry,
) -> None:
    processed_log = dataclasses.replace(
        processed_org_policy_constraint_log, data={"methodName": "test"}
    )
    log_is_skipped = org_policy_constraint_not_found_filter(processed_log)
    assert log_is_skipped is False


def test_log_is_not_skipped_when_service_name_is_not_orgpolicy(
    processed_org_policy_constraint_log: ProcessedLogEntry,
) -> None:
    processed_log = dataclasses.replace(
        processed_org_policy_constraint_log,
        data=dict(serviceName="different.service.com", methodName="test"),
    )
    log_is_skipped = org_policy_constraint_not_found_filter(processed_log)
    assert log_is_skipped is False


def test_log_is_not_skipped_when_message_does_not_contain_constraint_patterns(
    processed_org_policy_constraint_log: ProcessedLogEntry,
) -> None:
    processed_log = dataclasses.replace(
        processed_org_policy_constraint_log, message=ERROR_MESSAGES["different_error"]
    )
    log_is_skipped = org_policy_constraint_not_found_filter(processed_log)
    assert log_is_skipped is False
