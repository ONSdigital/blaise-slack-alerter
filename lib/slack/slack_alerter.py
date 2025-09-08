from typing import Any

from lib.log_processor import ProcessedLogEntry
from lib.slack.send_slack_message import send_slack_message
from lib.slack.slack_message import (SlackMessage,
                                     create_from_processed_log_entry,
                                     create_from_raw)


class SlackAlerter:
    def __init__(self, slack_url: str, project_name: str):
        self._slack_url = slack_url
        self._project_name = project_name

    def send_alert(self, message: SlackMessage) -> None:
        send_slack_message(self._slack_url, message)

    def create_raw_alert(self, raw: Any) -> SlackMessage:
        return create_from_raw(raw, self._project_name)

    def create_alert(self, entry: ProcessedLogEntry) -> SlackMessage:
        return create_from_processed_log_entry(entry, self._project_name)
