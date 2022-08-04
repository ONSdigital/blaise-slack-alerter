import json
from dataclasses import dataclass
from typing import Dict, Any

from lib.log_processor import ProcessedLogEntry


@dataclass(frozen=True)
class SlackMessage:
    title: str
    fields: Dict[str, str]
    content: str
    footnote: str


def create_from_raw(event: Any, project_name: str) -> SlackMessage:
    return SlackMessage(
        title="Error with bad format received",
        fields=dict(Platform="unknown", Application="unknown", Project=project_name),
        content=json.dumps(event, indent=2),
        footnote=(
            "This message was not in an expected format; "
            "consider extending the alerting lambda to support this message type."
        ),
    )


def create_from_processed_log_entry(
    processed_log_entry: ProcessedLogEntry, project_name: str
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
