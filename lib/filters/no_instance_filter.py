import logging

from lib.log_processor import ProcessedLogEntry


def no_instance_filter(log_entry: ProcessedLogEntry) -> bool:

    if not isinstance(log_entry.platform, str):
        return False

    if log_entry.platform != "cloud_function":
        return False

    if not isinstance(log_entry.message, str):
        return False

    if (
        "The request was aborted because there was no available instance"
        not in log_entry.message
    ):
        return False

    if not isinstance(log_entry.log_name, str):
        return False

    if "cloudfunctions" not in log_entry.log_name:
        return False

    logging.info(f"Skipping no instance agent alert")

    return True
