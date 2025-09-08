import logging

from lib.log_processor import ProcessedLogEntry


def rproxy_lookupEffectiveGuestPolicies_filter(log_entry: ProcessedLogEntry) -> bool:
    if not isinstance(log_entry.platform, str):
        return False

    if log_entry.platform != "gce_instance":
        return False

    if not isinstance(log_entry.application, str):
        return False

    if log_entry.application != "rproxy-b0bd8e4b":
        return False

    if not isinstance(log_entry.message, str):
        return False

    if (
        'Error running LookupEffectiveGuestPolicies: error calling LookupEffectiveGuestPolicies: code: "NotFound", message: "Requested entity was not found.", details: []'
        not in log_entry.message
    ):
        return False

    logging.info(f"Skipping rproxy lookupEffectiveGuestPolicies alert")
    return True
