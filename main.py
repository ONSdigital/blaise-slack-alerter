import logging
import os

from flask import Request
from google.cloud.logging_v2.handlers import StructuredLogHandler, setup_logging

from lib import send_alerts
from lib.slack import SlackAlerter

setup_logging(StructuredLogHandler())


def send_alert(event: dict, _context) -> str:
    slack_url = os.environ["SLACK_URL"]
    project_name = os.environ["GCP_PROJECT_NAME"]
    alerter = SlackAlerter(slack_url, project_name)
    return send_alerts.execute(event, alerter=alerter)


def log_error(_request: Request) -> str:
    logging.error("Example error message", extra=dict(reason="proof_of_concept"))
    return "Error logged"
