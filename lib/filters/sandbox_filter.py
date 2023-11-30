from lib.log_processor import ProcessedLogEntry


def is_formal_environment(log_name):
    project_name = log_name.split("/")[1]
    formal_environments = [
        "ons-blaise-v2-dev",
        "ons-blaise-v2-dev-training",
        "ons-blaise-v2-preprod",
        "ons-blaise-v2-prod",
    ]

    if any(
        formal_environment == project_name for formal_environment in formal_environments
    ):
        return True

    return False


def sandbox_filter(log_entry: ProcessedLogEntry) -> bool:
    if not log_entry.log_name:
        return False

    if is_formal_environment(log_entry.log_name):
        return False

    return True
