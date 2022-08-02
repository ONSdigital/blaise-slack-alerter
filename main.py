import logging
import os

from flask import Request
from google.cloud.logging_v2.handlers import StructuredLogHandler, setup_logging

from lib import slack_alerts
from lib.slack import SlackMessage
from lib.slack.alerter import create_slack_alerter

setup_logging(StructuredLogHandler())


def send_slack_alert(event: dict, _context) -> str:
    slack_url = os.environ["SLACK_URL"]
    environment = os.environ["ENVIRONMENT"]
    return slack_alerts.execute(
        event, environment=environment, send_alert=create_slack_alerter(slack_url)
    )


def log_error(_request: Request) -> str:
    logging.error("Example error message", extra=dict(reason="proof_of_concept"))
    return "Error logged"


def send_to_slack() -> None:
    slack_url = os.environ["SLACK_URL"]
    send_alert = create_slack_alerter(slack_url)

    send_alert(
        SlackMessage(
            title="ERROR: Example error message where something went wrong",
            fields=dict(Platform="gce_instance", Application="bts"),
            content="Message content goes here",
            footnote="Actions go here",
        )
    )


if __name__ == "__main__":
    send_to_slack()
