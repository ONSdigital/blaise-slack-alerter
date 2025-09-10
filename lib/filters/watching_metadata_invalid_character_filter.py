import logging

from lib.log_processor import ProcessedLogEntry


def watching_metadata_invalid_character_filter(log_entry: ProcessedLogEntry) -> bool:

    if not isinstance(log_entry.platform, str):
        return False

    if log_entry.platform != "gce_instance":
        return False

    if not isinstance(log_entry.message, str):
        return False

    if not isinstance(log_entry.log_name, str):
        return False

    if (
        "Error watching metadata: invalid character '<' looking for beginning of value"
        not in log_entry.message
    ):
        return False

    if log_entry.log_name:
        if (
            "/winevt.raw" not in log_entry.log_name
            and "/GCEGuestAgent" not in log_entry.log_name
        ):
            return False

    logging.info("Skipping watching metadata invalid character alert")
    return True
