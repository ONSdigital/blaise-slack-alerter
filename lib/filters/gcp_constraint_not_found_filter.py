import logging
from typing import Optional
from lib.log_processor import ProcessedLogEntry


def org_policy_constraint_not_found_filter(
    log_entry: Optional[ProcessedLogEntry],
) -> bool:
    if log_entry is None:
        return False

    if log_entry.severity != "ERROR":
        return False

    if (
        not isinstance(log_entry.platform, str)
        or log_entry.platform != "audited_resource"
    ):
        return False

    if not isinstance(log_entry.message, str):
        return False

    if not isinstance(log_entry.data, dict) or not isinstance(
        log_entry.data.get("serviceName"), str
    ):
        return False

    if log_entry.data.get("serviceName") != "orgpolicy.googleapis.com":
        return False

    general_patterns = ["No constraint found with name", "generic::NOT_FOUND"]

    if not any(pattern in log_entry.message for pattern in general_patterns):
        return False

    target_constraints = [
        "constraints/gcp.requiresPhysicalZoneSeparation",
        "constraints/storage.disableServiceAccountHmacKeyCreation",
    ]

    matching_constraint = None
    for constraint in target_constraints:
        if constraint in log_entry.message:
            matching_constraint = constraint
            break

    if not matching_constraint:
        return False

    logging.info(
        f"Skipping 'org policy constraint not found: {matching_constraint}' alert"
    )
    return True


def physical_zone_separation_constraint_filter(log_entry: ProcessedLogEntry) -> bool:
    return org_policy_constraint_not_found_filter(log_entry)


def service_account_hmac_key_constraint_filter(log_entry: ProcessedLogEntry) -> bool:
    return org_policy_constraint_not_found_filter(log_entry)
