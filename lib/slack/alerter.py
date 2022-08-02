import json
import sys

import requests

from lib.send_alert import SendAlert
from lib.slack.slack_alert_failed import SlackAlertFailed
from lib.slack.slack_message import SlackMessage


def create_slack_alerter(slack_url: str) -> SendAlert:
    def send_alert(message: SlackMessage) -> None:
        slack_data = dict(
            blocks=[
                dict(
                    type="header",
                    text=dict(type="plain_text", text=f":alert: {message.title}"),
                ),
                dict(
                    type="section",
                    fields=[
                        dict(type="mrkdwn", text=f"*{key}:*\n{value}")
                        for key, value in message.fields.items()
                    ],
                ),
                dict(type="divider"),
                dict(
                    type="section",
                    text=dict(type="plain_text", text=message.content),
                ),
                dict(type="divider"),
                dict(type="section", text=dict(type="mrkdwn", text=message.footnote)),
            ]
        )

        byte_length = str(sys.getsizeof(slack_data))
        headers = {"Content-Type": "application/json", "Content-Length": byte_length}
        response = requests.post(
            slack_url, data=json.dumps(slack_data), headers=headers
        )

        print(response.text)

        if response.status_code != 200:
            raise SlackAlertFailed(response.status_code, response.text)

    return send_alert
