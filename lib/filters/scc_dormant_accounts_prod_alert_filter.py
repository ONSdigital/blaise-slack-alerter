import logging
from typing import Optional

from lib.log_processor import ProcessedLogEntry


def scc_dormant_accounts_prod_alert_filter(
    log_entry: Optional[ProcessedLogEntry],
) -> bool:
    """
    Filters out ERROR alerts from an organisation level service account.

    This organisation level service account queries for service accounts in projects to check if they exist,
    and if not found, generates "Service account does not exist" errors that clutter alert channels.
    These alerts are deemed safe to ignore.
    """
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

    logging.info("Skipping external 'SCC Dormant Accounts Alert' service account alert")
    return True
