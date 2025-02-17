import logging
import re

from lib.log_processor import ProcessedLogEntry

def service_account_key_filter(log_entry: ProcessedLogEntry) -> bool:
    if not isinstance(log_entry.platform, str):
        return False

    if log_entry.platform != "service_account":
        return False

    if not isinstance(log_entry.message, str):
        return False

    if ("Service account key" and "does not exist.") not in log_entry.message:
        return False
    
    account_key_pattern = r"[a-fA-F0-9]{40}"
    pattern = rf"Service account key {account_key_pattern} does not exist\."

    if not re.search(pattern, log_entry.message):
        return False


    logging.info(f"Skipping service account key alert")
    return True