import logging

from lib.log_processor import ProcessedLogEntry


def paramiko_filter(log_entry: ProcessedLogEntry) -> bool:

    if not isinstance(log_entry.severity, str):
        return False

    if not isinstance(log_entry.message, str):
        return False

    if log_entry.severity != "ERROR":
        return False

    if log_entry.platform != "cloud_run_revision":
        return False

    if (
        "/layers/google.python.pip/pip/lib/python3.9/site-packages/paramiko/sftp_file.py"
    ) not in log_entry.message:
        return False

    logging.info(f"Skipping paramiko error alert")
    return True
