import logging

from lib.log_processor import ProcessedLogEntry


def _is_formal_environment(log_name: str) -> bool:
    project_name = log_name.split("/")[1]
    formal_environments = [
        "ons-blaise-v2-dev",
        "ons-blaise-v2-dev-training",
        "ons-blaise-v2-preprod",
        "ons-blaise-v2-prod",
    ]

    if not any(
        formal_environment == project_name for formal_environment in formal_environments
    ):
        return False

    return True


def sandbox_filter(log_entry: ProcessedLogEntry) -> bool:
    if not log_entry.log_name:
        return False

    if _is_formal_environment(log_entry.log_name):
        return False

    logging.info(f"Skipping sandbox alert")
    return True
