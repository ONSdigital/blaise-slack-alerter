import logging

from lib.log_processor import ProcessedLogEntry


def bootstrapper_filter(log_entry: ProcessedLogEntry) -> bool:

    if not isinstance(log_entry.severity, str):
        return False

    if not isinstance(log_entry.message, str):
        return False

    if log_entry.severity != "ERROR":
        return False

    if log_entry.platform != "gce_instance":
        return False

    if (
        "Failed to execute job MTLS_MDS_Credential_Boostrapper with error:"
        not in log_entry.message
        and "Failed to schedule job MTLS_MDS_Credential_Boostrapper with error:"
        not in log_entry.message
    ):
        return False

    logging.info("Skipping bootstrapper alert")
    return True
