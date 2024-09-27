import logging
from datetime import datetime, timedelta
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

    if ("") not in log_entry.message:
        return False
    
    Failed to execute job MTLS_MDS_Credential_Boostrapper: 
    Failed to schedule job MTLS_MDS_Credential_Boostrapper 
    
    Failed to execute job MTLS_MDS_Credential_Boostrapper: 
    
    logging.info(f"Skipping bootstrapper alert")
    return True