import logging

from lib.log_processor import ProcessedLogEntry


def _is_failed_to_install(log_entry: ProcessedLogEntry) -> bool:
    message = log_entry.message or ""
    if "AUDIT_LOG: Failed to install questionnaire" in message:
        return True
    return False


def _is_preprod(log_name: str) -> bool:
    if "ons-blaise-v2-preprod" in log_name:
        return True
    return False


def _is_training(log_name: str) -> bool:
    if "ons-blaise-v2-dev-training" in log_name:
        return True
    return False


def all_preprod_and_training_alerts_except_erroneous_questionnaire_filter(
    log_entry: ProcessedLogEntry,
) -> bool:
    if not isinstance(log_entry.message, str):
        return False

    if not log_entry.log_name:
        return False

    if "ons-blaise-v2-prod" in log_entry.log_name:
        return False

    if (
        _is_preprod(log_entry.log_name) or _is_training(log_entry.log_name)
    ) and _is_failed_to_install(log_entry):
        return False

    logging.info(f"Skipping preprod/training alert")
    return True
