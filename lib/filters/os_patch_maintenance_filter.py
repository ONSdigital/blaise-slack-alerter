import logging
from datetime import datetime
from lib.log_processor import ProcessedLogEntry
from lib.utilities.weekly_maintenance_window import is_in_weekly_maintenance_window
from lib.utilities.log_validation import validate_log_entry_fields


def os_patch_maintenance_filter(log_entry: ProcessedLogEntry) -> bool:
    """
    Filter harmless VM shutdown/restart logs during OS patch weekly maintenance windows.
    Activates only on Fridays around 01:30 AM UTC (1:00-2:00 AM window) when VMs restart for patches.
    
    Handles:
    - VM service termination/restart logs (Google Compute Engine services)
    - Metadata context canceled errors (GCE Guest Agent)
    """

    if not validate_log_entry_fields(
        log_entry,
        required_platform="gce_instance",
        require_message=True,
        require_timestamp=True
    ):
        return False

    if not is_in_weekly_maintenance_window(log_entry.timestamp):
        return False

    service_termination_indicators = [
        "The Google Compute Engine Agent Manager service terminated unexpectedly",
        "The Google Compute Engine Compat Manager service terminated unexpectedly",
        "service terminated unexpectedly",
        "Restart the service",
    ]

    metadata_context_indicators = [
        "Error watching metadata: context canceled",
    ]

    service_termination_match = any(
        indicator in log_entry.message for indicator in service_termination_indicators
    )

    if service_termination_match and log_entry.log_name and "windows_event_log" in log_entry.log_name:
        logging.info(
            f"Skipping OS patch weekly maintenance window alert for {log_entry.application}"
        )
        return True

    metadata_context_match = any(
        indicator in log_entry.message for indicator in metadata_context_indicators
    )

    if metadata_context_match and log_entry.log_name and "GCEGuestAgent" in log_entry.log_name:
        logging.info(
            f"Skipping metadata context canceled alert during maintenance window for {log_entry.application}"
        )
        return True

    return False
