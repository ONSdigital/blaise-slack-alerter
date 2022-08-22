import json
import sys

import requests

from lib.slack.slack_message import SlackMessage
from lib.slack.slack_message_formatter import convert_slack_message_to_blocks


def send_slack_message(slack_url: str, message: SlackMessage) -> None:
    slack_data = convert_slack_message_to_blocks(message)

    byte_length = str(sys.getsizeof(slack_data))
    headers = {"Content-Type": "application/json", "Content-Length": byte_length}
    response = requests.post(slack_url, data=json.dumps(slack_data), headers=headers)

    if response.status_code != 200:
        raise SlackAlertFailed(response.status_code, response.text, slack_data)


class SlackAlertFailed(RuntimeError):
    pass
