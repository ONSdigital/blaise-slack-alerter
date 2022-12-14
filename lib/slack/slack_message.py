import json
from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional

from lib.cloud_logging.log_query_link import create_log_query_link
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
        fields={
            "Platform": "unknown",
            "Application": "unknown",
            "Log Time": "unknown",
            "Project": project_name,
        },
        content=json.dumps(event, indent=2),
        footnote=(
            "This message was not in an expected format; "
            "consider extending the alerting lambda to support this message type."
        ),
    )


def create_from_processed_log_entry(
    processed_log_entry: ProcessedLogEntry, project_name: str
) -> SlackMessage:
    title, full_message = _create_title(processed_log_entry)

    return SlackMessage(
        title=title,
        fields={
            "Platform": processed_log_entry.platform or "unknown",
            "Application": processed_log_entry.application or "unknown",
            "Log Time": _create_log_time(processed_log_entry),
            "Project": project_name,
        },
        content=_create_content(processed_log_entry, full_message),
        footnote=_create_footnote(processed_log_entry, project_name),
    )


def _create_title(processed_log_entry: ProcessedLogEntry) -> Tuple[str, Optional[str]]:
    message_lines = processed_log_entry.message.split("\n")

    title = f":alert: {processed_log_entry.severity or 'UNKNOWN'}: {message_lines[0]}"

    full_message = processed_log_entry.message if len(message_lines) > 1 else None

    if len(title) > 150:
        title = f"{title[:145]}..."
        full_message = processed_log_entry.message

    return title, full_message


def _create_log_time(processed_log_entry):
    return (
        processed_log_entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        if processed_log_entry.timestamp is not None
        else "unknown"
    )


def _create_content(
    processed_log_entry: ProcessedLogEntry, full_message: Optional[str]
):
    content = (
        processed_log_entry.data
        if isinstance(processed_log_entry.data, str)
        else json.dumps(processed_log_entry.data, indent=2)
    )

    if processed_log_entry.most_important_values and isinstance(
        processed_log_entry.data, dict
    ):
        important_values = [
            f"{value}: {_get_value(processed_log_entry.data, value)}"
            for value in processed_log_entry.most_important_values
            if _get_value(processed_log_entry.data, value) is not None
        ]

        if len(important_values) > 0:
            content = "\n".join(important_values)

    if full_message:
        content = (
            "**Error Message**\n"
            f"{processed_log_entry.message}\n"
            "\n"
            "**Extra Content**\n"
            f"{content}"
        )

    content = _trim_number_of_lines(content, max_lines=10)

    content = _trim_length(content, max_chars=2900)

    return content


def _create_footnote(processed_log_entry: ProcessedLogEntry, project_name: str) -> str:
    uptime_url = f"https://console.cloud.google.com/monitoring/uptime?referrer=search&project={project_name}"

    severities = ["WARNING", "ERROR", "CRITICAL", "ALERT", "EMERGENCY", "DEBUG"]
    log_link_url = (
        create_log_query_link(
            fields=processed_log_entry.log_query,
            severities=severities,
            cursor_timestamp=processed_log_entry.timestamp,
            project_name=project_name,
        )
        if processed_log_entry.timestamp
        else None
    )
    log_action_line = (
        f"3. <{log_link_url} | View the logs>"
        if log_link_url is not None
        else "3. Determine the cause of the error"
    )

    managing_alerts_link = (
        "https://confluence.ons.gov.uk/pages/viewpage.action?pageId=98502389"
    )

    return (
        "*Next Steps*\n"
        "1. Add some :eyes: to show you are investigating\n"
        f"2. <{uptime_url} | Check the system is online>\n"
        f"{log_action_line}\n"
        f"4. Follow the <{managing_alerts_link} | Managing Prod Alerts> process"
    )


def _trim_number_of_lines(content, max_lines):
    lines = content.split("\n")
    if len(lines) > max_lines:
        content = "\n".join(lines[0 : max_lines - 2]) + "\n" "...\n" "[truncated]"
    return content


def _trim_length(content, max_chars):
    if len(content) > max_chars:
        content = f"{content[:max_chars]}...\n[truncated]"
    return content


def _get_value(dictionary, path: str) -> Optional[Any]:
    parts = path.split(".")
    result = dictionary
    for part in parts:
        result = result.get(part, {})
    return None if isinstance(result, dict) else result
