import logging

from lib.log_processor import ProcessedLogEntry
from lib.utilities.log_validation import validate_log_entry_fields
from lib.utilities.weekly_maintenance_window import is_in_friday_maintenance_window


def os_patch_maintenance_filter(log_entry: ProcessedLogEntry) -> bool:
    """
    Filter harmless VM shutdown/restart logs during weekly OS patch jobs, which causes VMs to restart.
    Activates only on Fridays around 01:30 AM UTC (1:25-1:35 AM window).

    Handles:
    - VM service termination/restart logs (Google Compute Engine services)
    - Metadata context canceled errors (GCE Guest Agent)
    - OSConfigAgent task cancellation errors (OS patching operations)
    """

    if not validate_log_entry_fields(
        log_entry,
        required_platform="gce_instance",
        require_message=True,
        require_timestamp=True,
    ):
        return False

    if not log_entry.timestamp or not is_in_friday_maintenance_window(
        log_entry.timestamp
    ):
        return False

    maintenance_log_patterns = [
        {
            "name": "service_termination",
            "indicators": [
                "The Google Compute Engine Agent Manager service terminated unexpectedly",
                "The Google Compute Engine Compat Manager service terminated unexpectedly",
                "service terminated unexpectedly",
                "Restart the service",
            ],
            "log_name_contains": "windows_event_log",
            "description": "OS patch weekly maintenance window alert",
        },
        {
            "name": "metadata_context",
            "indicators": [
                "Error watching metadata: context canceled",
            ],
            "log_name_contains": "GCEGuestAgent",
            "description": "metadata context canceled alert during maintenance window",
        },
        {
            "name": "osconfig_agent",
            "indicators": [
                "OSConfigAgent Warning: Error waiting for task",
                "rpc error: code = Canceled desc = context canceled",
            ],
            "log_name_contains": "windows_event_log",
            "description": "OSConfigAgent error alert during maintenance window",
        },
    ]

    return _check_maintenance_log_patterns(log_entry, maintenance_log_patterns)


def _check_maintenance_log_patterns(
    log_entry: ProcessedLogEntry, patterns: list
) -> bool:
    for pattern in patterns:
        if _matches_pattern(log_entry, pattern):
            logging.info(
                f"Skipping {pattern['description']} for {log_entry.application}"
            )
            return True

    return False


def _matches_pattern(log_entry: ProcessedLogEntry, pattern: dict) -> bool:
    if not log_entry.message:
        return False

    message_match = any(
        indicator in log_entry.message for indicator in pattern["indicators"]
    )

    log_name_match = bool(
        log_entry.log_name and pattern["log_name_contains"] in log_entry.log_name
    )

    return message_match and log_name_match
