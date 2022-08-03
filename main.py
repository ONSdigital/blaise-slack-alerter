import logging
import os

from flask import Request
from google.cloud.logging_v2.handlers import StructuredLogHandler, setup_logging

from lib import slack_alerts
from lib.slack.alerter import create_slack_alerter

setup_logging(StructuredLogHandler())


def send_slack_alert(event: dict, _context) -> str:
    slack_url = os.environ["SLACK_URL"]
    project_name = os.environ["GCP_PROJECT_NAME"]
    return slack_alerts.execute(
        event, project_name=project_name, send_alert=create_slack_alerter(slack_url)
    )


def log_error(_request: Request) -> str:
    logging.error("Example error message", extra=dict(reason="proof_of_concept"))
    return "Error logged"
