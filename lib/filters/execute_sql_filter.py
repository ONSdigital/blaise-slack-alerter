import logging
from datetime import datetime, timedelta
from lib.log_processor import ProcessedLogEntry


def execute_sql_filter(log_entry: ProcessedLogEntry) -> bool:

    if not isinstance(log_entry.severity, str):
        return False

    if not isinstance(log_entry.message, str):
        return False

    if log_entry.severity != "ERROR":
        return False

    if (
        log_entry is None
        or not isinstance(log_entry.data, dict)
        or log_entry.data.get("methodName") != "cloudsql.instances.executeSql"
    ):
        return False

    logging.info(f"Skipping execute sql alert")
    return True
