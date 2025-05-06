import logging
from lib.log_processor import ProcessedLogEntry


def scc_dormant_accounts_prod_alert_filter(log_entry: ProcessedLogEntry) -> bool:
    TARGET_EXTERNAL_SERVICE_ACCOUNT = (
        "scc-dormant-accounts-alert@ons-gcp-monitoring-prod.iam.gserviceaccount.com"
    )

    if log_entry is None:
        return False

    if log_entry.severity != "ERROR":
        return False

    if (
        not isinstance(log_entry.platform, str)
        or log_entry.platform != "service_account"
    ):
        return False

    if not isinstance(log_entry.message, str):
        return False

    if (
        not isinstance(log_entry.data, dict)
        or not isinstance(log_entry.data.get("authenticationInfo"), dict)
        or not isinstance(
            log_entry.data.get("authenticationInfo", {}).get("principalEmail"),
            str,
        )
    ):
        return False

    if not (
        log_entry.data.get("authenticationInfo", {}).get("principalEmail")
        == TARGET_EXTERNAL_SERVICE_ACCOUNT
    ):
        return False

    logging.info(
        f"Skipping external 'SCC Dormant Accounts Alert' service account alert"
    )
    return True
