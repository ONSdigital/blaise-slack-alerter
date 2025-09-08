import dataclasses
import datetime

import pytest

from lib.filters.rproxy_lookupEffectiveGuestPolicies_filter import \
    rproxy_lookupEffectiveGuestPolicies_filter
from lib.log_processor.processed_log_entry import ProcessedLogEntry


@pytest.fixture()
def processed_log_entry_rproxy_lookupEffectiveGuestPolicies_error() -> (
    ProcessedLogEntry
):
    return ProcessedLogEntry(
        message='Error running LookupEffectiveGuestPolicies: error calling LookupEffectiveGuestPolicies: code: "NotFound", message: "Requested entity was not found.", details: []',
        data={"localTimestamp": "2023-09-28T08:45:35.1241Z", "omitempty": None},
        severity="ERROR",
        platform="gce_instance",
        application="rproxy-b0bd8e4b",
        log_name="projects/ons-blaise-v2-prod/logs/OSConfigAgent",
        timestamp=datetime.datetime(2023, 9, 28, 8, 45, 36, 225541),
        log_query={"resource.type": "gce_instance"},
        most_important_values=["description", "event_type"],
    )


def test_log_is_a_valid_rproxy_lookupEffectiveGuestPolicies_error(
    processed_log_entry_rproxy_lookupEffectiveGuestPolicies_error: ProcessedLogEntry,
) -> None:
    log_is_skipped = rproxy_lookupEffectiveGuestPolicies_filter(
        processed_log_entry_rproxy_lookupEffectiveGuestPolicies_error
    )

    assert log_is_skipped is True


def test_log_is_not_from_gce_instance_when_rproxy_lookupEffectiveGuestPolicies_error(
    processed_log_entry_rproxy_lookupEffectiveGuestPolicies_error: ProcessedLogEntry,
) -> None:
    processed_log_entry_rproxy_lookupEffectiveGuestPolicies_error = dataclasses.replace(
        processed_log_entry_rproxy_lookupEffectiveGuestPolicies_error,
        platform="not_gce_instance",
    )
    log_is_skipped = rproxy_lookupEffectiveGuestPolicies_filter(
        processed_log_entry_rproxy_lookupEffectiveGuestPolicies_error
    )

    assert log_is_skipped is False


def test_log_is_not_from_rproxy_gce_instance_when_rproxy_lookupEffectiveGuestPolicies_error(
    processed_log_entry_rproxy_lookupEffectiveGuestPolicies_error: ProcessedLogEntry,
) -> None:
    processed_log_entry_rproxy_lookupEffectiveGuestPolicies_error = dataclasses.replace(
        processed_log_entry_rproxy_lookupEffectiveGuestPolicies_error,
        platform="not_rproxy_vm",
    )
    log_is_skipped = rproxy_lookupEffectiveGuestPolicies_filter(
        processed_log_entry_rproxy_lookupEffectiveGuestPolicies_error
    )

    assert log_is_skipped is False


def test_log_message_is_not_a_rproxy_lookupEffectiveGuestPolicies_error(
    processed_log_entry_rproxy_lookupEffectiveGuestPolicies_error: ProcessedLogEntry,
) -> None:
    processed_log_entry_rproxy_lookupEffectiveGuestPolicies_error = dataclasses.replace(
        processed_log_entry_rproxy_lookupEffectiveGuestPolicies_error,
        message="not_rproxy_lookupEffectiveGuestPolicies_error",
    )
    log_is_skipped = rproxy_lookupEffectiveGuestPolicies_filter(
        processed_log_entry_rproxy_lookupEffectiveGuestPolicies_error
    )

    assert log_is_skipped is False
