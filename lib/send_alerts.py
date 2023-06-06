import json
import logging
from typing import List

from lib.alerter import Alerter
from lib.cloud_functions import InvalidCloudFunctionEvent, parse_event
from lib.cloud_logging import parse_log_entry
from lib.filters.auditlog_filter import auditlog_filter
from lib.filters.agent_connect_filter import agent_connect_filter
from lib.log_processor import (
    ProcessedLogEntry,
    CreateAppLogPayloadFromLogEntry,
)
from lib.log_processor import process_log_entry
from lib.filters.osconfig_agent_filter import osconfig_agent_filter


def log_entry_skipped(log_entry: ProcessedLogEntry):
    filters = [osconfig_agent_filter, auditlog_filter, agent_connect_filter]

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
        log_data = parse_event(event).data
    except InvalidCloudFunctionEvent:
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
