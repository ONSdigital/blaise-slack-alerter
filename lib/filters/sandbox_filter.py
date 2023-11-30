from lib.log_processor import ProcessedLogEntry


def is_sandbox_environment(project_name):
    formal_environments = [
        # "ons-blaise-v2-dev",
        "ons-blaise-v2-dev-training",
        "ons-blaise-v2-preprod",
        "ons-blaise-v2-prod",
    ]

    if any(match in project_name for match in formal_environments):
        return False

    return True


def sandbox_filter(log_entry: ProcessedLogEntry) -> bool:
    if not log_entry.log_name:
        return False

    if is_sandbox_environment(log_entry.log_name):
        return True

    return False
