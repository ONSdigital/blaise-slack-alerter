import base64
import json
import logging
from unittest.mock import Mock

import pytest

from lib import slack_alerts
from lib.slack.slack_message import SlackMessage


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


def test_send_raw_string_slack_alert(caplog, send_alert, log_matching):
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


def test_send_gce_instance_slack_alert(caplog, log_matching, send_alert):
    gce_instance_log_entry = {
        "insertId": "iqfd5yh5469d5wxx",
        "jsonPayload": {
            "channel": "application",
            "computer_name": "vm-mgmt",
            "description": "Error description from VM",
            "event_category": "0",
            "event_id": "0",
            "event_type": "error",
            "message": "Error message from VM",
            "record_number": "6569254",
            "source_name": "Blaise",
            "string_inserts": [],
            "time_generated": "2022-08-02 20:06:38 +0100",
            "time_written": "2022-08-02 20:06:38 +0100",
            "user": "",
        },
        "labels": {"compute.googleapis.com/resource_name": "vm-mgmt"},
        "logName": "projects/secret-project/logs/winevt.raw",
        "receiveTimestamp": "2022-08-02T19:06:42.275819947Z",
        "resource": {
            "labels": {
                "instance_id": "89453598437598",
                "project_id": "secret-project",
                "zone": "europe-west2-a",
            },
            "type": "gce_instance",
        },
        "severity": "ERROR",
        "timestamp": "2022-08-02T19:06:38Z",
    }

    event = {
        "@type": "type.googleapis.com/google.pubsub.v1.PubsubMessage",
        "attributes": {
            "logging.googleapis.com/timestamp": "2022-07-22T20:36:21.891133Z"
        },
        "data": base64.b64encode(json.dumps(gce_instance_log_entry).encode("ascii")),
    }

    with caplog.at_level(logging.INFO):
        response = slack_alerts.execute(event, environment="dev", send_alert=send_alert)

    info = log_matching(logging.INFO, "Sending message to Slack")
    assert info.textPayload == "Error message from VM"

    assert response == "Alert sent"

    send_alert.assert_called_with(
        SlackMessage(
            title="ERROR: Error message from VM",
            fields=dict(Platform="gce_instance", Application="vm-mgmt"),
            content=json.dumps(
                {
                    "channel": "application",
                    "description": "Error description from VM",
                    "event_category": "0",
                    "event_id": "0",
                    "event_type": "error",
                    "record_number": "6569254",
                    "source_name": "Blaise",
                    "string_inserts": [],
                    "time_generated": "2022-08-02 20:06:38 +0100",
                    "time_written": "2022-08-02 20:06:38 +0100",
                    "user": "",
                },
                indent=2,
            ),
            footnote=(
                "*Next Steps*\n"
                "1. Add some :eyes: to show you are investigating\n"
                "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=ons-blaise-v2-dev | Check the system is online>\n"
                "3. <https://console.cloud.google.com/logs/query;query=%0A;cursorTimestamp=2022-08-02T19:06:42.275819947Z?referrer=search&project=ons-blaise-v2-dev | View the logs>\n4. Follow the <https://confluence.ons.gov.uk/pages/viewpage.action?pageId=98502389 | Managing Prod Alerts> process"
            ),
        )
    )


def test_send_cloud_function_slack_alert(caplog, log_matching, send_alert):
    cloud_function_log_entry = {
        "httpRequest": {
            "protocol": "HTTP/1.1",
            "requestMethod": "POST",
            "requestUrl": "http://example.appspot.com",
            "userAgent": "Go-http-client/1.1",
        },
        "insertId": "62db0a45000d98fd76d18556",
        "labels": {
            "execution_id": "12312321321312",
            "instance_id": "54354325432542354325432",
            "python_logger": "root",
        },
        "logName": "projects/secret-project/logs/cloudfunctions.googleapis.com%2Fcloud-functions",
        "receiveTimestamp": "2022-07-22T20:36:22.219592062Z",
        "resource": {
            "labels": {
                "function_name": "log-error",
                "project_id": "secret-project",
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
        "spanId": "4h4315h43534",
        "textPayload": "Example error message",
        "timestamp": "2022-07-22T20:36:21.891133Z",
        "trace": "5435435432534fdf45353554",
        "traceSampled": True,
    }

    event = {
        "@type": "type.googleapis.com/google.pubsub.v1.PubsubMessage",
        "attributes": {
            "logging.googleapis.com/timestamp": "2022-07-22T20:36:21.891133Z"
        },
        "data": base64.b64encode(json.dumps(cloud_function_log_entry).encode("ascii")),
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
