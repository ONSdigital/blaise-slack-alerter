from lib.log_processor import ProcessedLogEntry


def all_preprod_alerts_except_erroneous_questionnaire_filter(
    log_entry: ProcessedLogEntry,
) -> bool:
    if not isinstance(log_entry.message, str):
        return False

    if not log_entry.log_name:
        return False

    if "ons-blaise-v2-prod" in log_entry.log_name:
        return False

    if "AUDIT_LOG: Failed to install questionnaire" in log_entry.message:
        return False

    return True
