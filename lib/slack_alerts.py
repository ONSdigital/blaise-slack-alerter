import json
import logging

from lib.cloud_functions import InvalidCloudFunctionEvent, parse_event
from lib.cloud_logging import parse_log_entry
from lib.log_processor import APP_LOG_PAYLOAD_FACTORIES, ProcessedLogEntry
from lib.log_processor import process_log_entry
from lib.send_alert import SendAlert
from lib.slack.slack_message import SlackMessage


def execute(event, project_name: str, send_alert: SendAlert) -> str:
    try:
        log_data = parse_event(event).data
    except InvalidCloudFunctionEvent:
        logging.warning(
            f"Invalid PubSub envelope: Field 'data' was missing.",
            extra=dict(textPayload=json.dumps(event)),
        )
        logging.info(f"Sending raw message to Slack")
        send_alert(
            SlackMessage(
                title="Error with bad format received",
                fields=dict(
                    Platform="unknown", Application="unknown", Project=project_name
                ),
                content=json.dumps(event, indent=2),
                footnote=(
                    "This message was not in an expected format; "
                    "consider extending the alerting lambda to support this message type."
                ),
            )
        )
        return "Alert sent (invalid envelope)"

    if isinstance(log_data, str):
        processed_log_entry = ProcessedLogEntry(message=log_data)
    else:
        log_entry = parse_log_entry(log_data)
        processed_log_entry = process_log_entry(log_entry, APP_LOG_PAYLOAD_FACTORIES)

    logging.info(
        f"Sending message to Slack", extra=dict(textPayload=processed_log_entry.message)
    )
    send_alert(create_slack_message(project_name, processed_log_entry))
    return "Alert sent"


def create_slack_message(
    project_name: str, processed_log_entry: ProcessedLogEntry
) -> SlackMessage:
    uptime_url = f"https://console.cloud.google.com/monitoring/uptime?referrer=search&project={project_name}"
    log_link_url = f"https://console.cloud.google.com/logs/query;query=%0A;cursorTimestamp={processed_log_entry.timestamp}?referrer=search&project={project_name}"
    managing_alerts_link = (
        "https://confluence.ons.gov.uk/pages/viewpage.action?pageId=98502389"
    )

    log_action_line = (
        f"3. <{log_link_url} | View the logs>"
        if processed_log_entry.timestamp is not None
        else "3. Determine the cause of the error"
    )

    content = (
        processed_log_entry.data
        if isinstance(processed_log_entry.data, str)
        else json.dumps(processed_log_entry.data, indent=2)
    )

    return SlackMessage(
        title=f"{processed_log_entry.severity or 'UNKNOWN'}: {processed_log_entry.message}",
        fields=dict(
            Platform=processed_log_entry.platform or "unknown",
            Application=processed_log_entry.application or "unknown",
            Project=project_name,
        ),
        content=content,
        footnote=(
            "*Next Steps*\n"
            "1. Add some :eyes: to show you are investigating\n"
            f"2. <{uptime_url} | Check the system is online>\n"
            f"{log_action_line}\n"
            f"4. Follow the <{managing_alerts_link} | Managing Prod Alerts> process"
        ),
    )
