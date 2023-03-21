import json
import logging
from typing import List

from lib.alerter import Alerter
from lib.cloud_functions import InvalidCloudFunctionEvent, parse_event
from lib.cloud_logging import parse_log_entry
from lib.log_processor import (
    ProcessedLogEntry,
    CreateAppLogPayloadFromLogEntry,
)
from lib.log_processor import process_log_entry


def skip_log_entry(log_entry):
    entry_data = log_entry.data

    # Skip "OSConfigAgent Error: unexpected end of JSON input" logs
    if log_entry.message == "Unknown JSON Error":
        if (
            "OSConfigAgent Error" in entry_data["description"]
            and "unexpected end of JSON input" in entry_data["description"]
        ):
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

    if skip_log_entry(processed_log_entry):
        return "Alert skipped"

    logging.info(
        f"Sending message to Slack", extra=dict(textPayload=processed_log_entry.message)
    )
    alert = alerter.create_alert(processed_log_entry)
    alerter.send_alert(alert)
    return "Alert sent"
