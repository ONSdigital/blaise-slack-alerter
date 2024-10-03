import json
import logging
from typing import List

from lib.alerter import Alerter
from lib.cloud_run_revision import InvalidCloudRunRevisionEvent, parse_event
from lib.cloud_logging import parse_log_entry
from lib.filters.all_preprod_and_training_alerts_except_erroneous_questionnaire_filter import (
    all_preprod_and_training_alerts_except_erroneous_questionnaire_filter,
)
from lib.filters.sandbox_filter import sandbox_filter
from lib.filters.auditlog_filter import auditlog_filter
from lib.filters.agent_connect_filter import agent_connect_filter
from lib.filters.osconfig_agent_filter import osconfig_agent_filter
from lib.filters.ip_space_exhausted_filter import ip_space_exhausted_filter
from lib.filters.rproxy_lookupEffectiveGuestPolicies_filter import (
    rproxy_lookupEffectiveGuestPolicies_filter,
)
from lib.filters.watching_metadata_invalid_character_filter import (
    watching_metadata_invalid_character_filter,
)
from lib.log_processor import (
    ProcessedLogEntry,
    CreateAppLogPayloadFromLogEntry,
)
from lib.log_processor import process_log_entry
from lib.filters.no_instance_filter import no_instance_filter
from lib.filters.invalid_login_attempt_filter import invalid_login_attempt_filter
from lib.filters.requested_entity_was_not_found_filter import (
    requested_entity_was_not_found_filter,
)
from lib.filters.execute_sql_filter import execute_sql_filter
from lib.filters.paramiko_filter import paramiko_filter
from lib.filters.bootstrapper_filter import bootstrapper_filter


def log_entry_skipped(log_entry: ProcessedLogEntry):
    filters = [
        sandbox_filter,
        all_preprod_and_training_alerts_except_erroneous_questionnaire_filter,
        osconfig_agent_filter,
        auditlog_filter,
        agent_connect_filter,
        rproxy_lookupEffectiveGuestPolicies_filter,
        watching_metadata_invalid_character_filter,
        ip_space_exhausted_filter,
        no_instance_filter,
        invalid_login_attempt_filter,
        requested_entity_was_not_found_filter,
        execute_sql_filter,
        paramiko_filter,
        bootstrapper_filter,
    ]

    for filter in filters:
        if filter(log_entry):
            return True

    return False


def send_alerts(
    event,
    alerter: Alerter,
    app_log_payload_factories: List[CreateAppLogPayloadFromLogEntry],
) -> str:
    try:
        logging.info("EVENT LOG HERE")
        logging.debug(event)
        log_data = parse_event(event).data
    except InvalidCloudRunRevisionEvent:
        logging.warning(
            f"Invalid PubSub envelope: Field 'data' was missing.",
            extra=dict(textPayload=json.dumps(event)),
        )
        logging.info(f"Sending raw message to Slack")
        alerter.send_alert(alerter.create_raw_alert(event))
        return "Alert sent (invalid envelope)"

    if isinstance(log_data, str):
        processed_log_entry = ProcessedLogEntry(message=log_data)
    else:
        log_entry = parse_log_entry(log_data)
        processed_log_entry = process_log_entry(log_entry, app_log_payload_factories)

    if log_entry_skipped(processed_log_entry):
        return "Alert skipped"

    logging.info(
        f"Sending message to Slack", extra=dict(textPayload=processed_log_entry.message)
    )
    alert = alerter.create_alert(processed_log_entry)
    alerter.send_alert(alert)
    return "Alert sent"
