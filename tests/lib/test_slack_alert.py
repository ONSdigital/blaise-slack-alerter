import base64
import json
import logging
from unittest.mock import Mock

import pytest

from lib import slack_alerts
from lib.slack.slack_message import SlackMessage


@pytest.fixture
def log_entry():
    return {
        "httpRequest": {
            "protocol": "HTTP/1.1",
            "requestMethod": "POST",
            "requestUrl": "http://2d6a1bd9287ab235a784946879c51af7-dot-x79ccfe7bb2c6e43c-tp.appspot.com/",
            "userAgent": "Go-http-client/1.1",
        },
        "insertId": "62db0a45000d98fd76d18556",
        "labels": {
            "execution_id": "g20q2f9bu4zv",
            "instance_id": "00c61b117c5cb084daa8e085dcd1c6ca236366286b0a91db80c76fbf8dc1f9e97aeb943bc85bd477141c1aec556add2491a34f3c8748ce3d1e1c",
            "python_logger": "root",
        },
        "logName": "projects/ons-blaise-v2-dev-el5/logs/cloudfunctions.googleapis.com%2Fcloud-functions",
        "receiveTimestamp": "2022-07-22T20:36:22.219592062Z",
        "resource": {
            "labels": {
                "function_name": "log-error",
                "project_id": "ons-blaise-v2-dev-el5",
                "region": "europe-west2",
            },
            "type": "cloud_function",
        },
        "severity": "ERROR",
        "sourceLocation": {
            "file": "/workspace/main.py",
            "function": "log_error",
            "line": "16",
        },
        "spanId": "e185e2a30ab1ba11",
        "textPayload": "Example error message",
        "timestamp": "2022-07-22T20:36:21.891133Z",
        "trace": "60c2d64cfc0da3cbc3afcd6b8e9bd9af",
        "traceSampled": True,
    }


@pytest.fixture
def send_alert():
    return Mock()


def test_bad_pubsub_envelope(caplog, log_matching, send_alert):
    event = {
        "@type": "type.googleapis.com/google.pubsub.v1.PubsubMessage",
        "attributes": {
            "logging.googleapis.com/timestamp": "2022-07-22T20:36:21.891133Z"
        },
    }

    with caplog.at_level(logging.INFO):
        response = slack_alerts.execute(event, environment="dev", send_alert=send_alert)

    assert response == "Alert sent (invalid envelope)"

    warning = log_matching(
        logging.WARNING, "Invalid PubSub envelope: Field 'data' was missing."
    )
    assert json.loads(warning.textPayload) == event

    log_matching(logging.INFO, "Sending raw message to Slack")

    send_alert.assert_called_with(
        SlackMessage(
            title="Error with bad format received",
            fields=dict(Platform="unknown", Application="unknown"),
            content=json.dumps(event, indent=2),
            footnote=(
                "This message was not in an expected format; "
                "consider extending the alerting lambda to support this message type."
            ),
        )
    )


def test_send_raw_string_slack_alert(caplog, log_entry, send_alert, log_matching):
    event = {
        "@type": "type.googleapis.com/google.pubsub.v1.PubsubMessage",
        "attributes": {
            "logging.googleapis.com/timestamp": "2022-07-22T20:36:21.891133Z"
        },
        "data": base64.b64encode(
            json.dumps("This is a raw string message").encode("ascii")
        ),
    }

    with caplog.at_level(logging.INFO):
        response = slack_alerts.execute(event, environment="dev", send_alert=send_alert)

    info = log_matching(logging.INFO, "Sending message to Slack")
    assert info.textPayload == "This is a raw string message"

    assert response == "Alert sent"

    send_alert.assert_called_with(
        SlackMessage(
            title="UNKNOWN: This is a raw string message",
            fields=dict(Platform="unknown", Application="unknown"),
            content="{}",
            footnote=(
                "*Next Steps*\n"
                "1. Add some :eyes: to show you are investigating\n"
                "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=ons-blaise-v2-dev | Check the system is online>\n"
                "3. Determine the cause of the error\n"
                "4. Follow the <https://confluence.ons.gov.uk/pages/viewpage.action?pageId=98502389 | Managing Prod Alerts> process"
            ),
        )
    )


def test_send_slack_alert(caplog, log_matching, log_entry, send_alert):
    event = {
        "@type": "type.googleapis.com/google.pubsub.v1.PubsubMessage",
        "attributes": {
            "logging.googleapis.com/timestamp": "2022-07-22T20:36:21.891133Z"
        },
        "data": base64.b64encode(json.dumps(log_entry).encode("ascii")),
    }

    with caplog.at_level(logging.INFO):
        response = slack_alerts.execute(event, environment="dev", send_alert=send_alert)

    info = log_matching(logging.INFO, "Sending message to Slack")
    assert info.textPayload == "Example error message"

    assert response == "Alert sent"

    send_alert.assert_called_with(
        SlackMessage(
            title="ERROR: Example error message",
            fields=dict(Platform="cloud_function", Application="unknown"),
            content="{}",
            footnote=(
                "*Next Steps*\n"
                "1. Add some :eyes: to show you are investigating\n"
                "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=ons-blaise-v2-dev | Check the system is online>\n"
                "3. <https://console.cloud.google.com/logs/query;query=%0A;cursorTimestamp=2022-07-22T20:36:22.219592062Z?referrer=search&project=ons-blaise-v2-dev | View the logs>\n"
                "4. Follow the <https://confluence.ons.gov.uk/pages/viewpage.action?pageId=98502389 | Managing Prod Alerts> process"
            ),
        )
    )
