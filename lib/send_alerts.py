import json
import logging

from lib.alerter import Alerter
from lib.cloud_functions import InvalidCloudFunctionEvent, parse_event
from lib.cloud_logging import parse_log_entry
from lib.log_processor import (
    apply_argument_to_all,
    APP_LOG_PAYLOAD_FACTORIES,
    ProcessedLogEntry,
)
from lib.log_processor import process_log_entry


def execute(event, alerter: Alerter) -> str:
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
        factories = apply_argument_to_all(APP_LOG_PAYLOAD_FACTORIES, log_entry)
        processed_log_entry = process_log_entry(log_entry, factories)

    logging.info(
        f"Sending message to Slack", extra=dict(textPayload=processed_log_entry.message)
    )
    alerter.send_alert(alerter.create_alert(processed_log_entry))
    return "Alert sent"
