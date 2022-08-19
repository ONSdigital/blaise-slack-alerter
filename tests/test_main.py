import base64
import json
import logging
import os

import pytest
import requests_mock
from flask import Request

from main import log_error, send_slack_alert


def test_log_error(caplog, log_matching):
    request = Request.from_values()
    with caplog.at_level(logging.ERROR):
        response = log_error(request)

    error = log_matching(logging.ERROR, "Example error message")
    assert error.message == "Example error message"
    assert error.reason == "proof_of_concept"
    assert response == "Error logged"


@pytest.fixture(autouse=True, scope="module")
def run_around_tests():
    old_slack_url = os.environ.get("SLACK_URL", "")
    old_gcp_project_name = os.environ.get("GCP_PROJECT_NAME", "")
    os.environ["SLACK_URL"] = "https://slack.co/webhook/1234"
    os.environ["GCP_PROJECT_NAME"] = "project-dev"
    yield
    os.environ["SLACK_URL"] = old_slack_url
    os.environ["GCP_PROJECT_NAME"] = old_gcp_project_name


@pytest.fixture
def context():
    return dict()


def test_bad_pubsub_envelope(context):
    event = {
        "@type": "type.googleapis.com/google.pubsub.v1.PubsubMessage",
        "attributes": {
            "logging.googleapis.com/timestamp": "2022-07-22T20:36:21.891133Z"
        },
    }

    with requests_mock.Mocker() as http_mock:
        http_mock.post("https://slack.co/webhook/1234")
        response = send_slack_alert(event, context)

    assert response == "Alert sent (invalid envelope)"

    assert http_mock.call_count is 1
    assert json.loads(http_mock.request_history[0].text) == dict(
        blocks=[
            dict(
                text={
                    "text": ":alert: Error with bad format received",
                    "type": "plain_text",
                },
                type="header",
            ),
            dict(
                fields=[
                    dict(text="*Platform:*\nunknown", type="mrkdwn"),
                    dict(text="*Application:*\nunknown", type="mrkdwn"),
                    dict(text="*Log Time:*\nunknown", type="mrkdwn"),
                    dict(text="*Project:*\nproject-dev", type="mrkdwn"),
                ],
                type="section",
            ),
            dict(type="divider"),
            dict(
                text=dict(
                    text=(
                        "{\n"
                        '  "@type": "type.googleapis.com/google.pubsub.v1.PubsubMessage",\n'
                        '  "attributes": {\n'
                        '    "logging.googleapis.com/timestamp": "2022-07-22T20:36:21.891133Z"\n'
                        "  }\n"
                        "}"
                    ),
                    type="plain_text",
                ),
                type="section",
            ),
            dict(type="divider"),
            dict(
                text=dict(
                    text=(
                        "This message was not in an expected format; "
                        "consider extending the alerting lambda to support this message type."
                    ),
                    type="mrkdwn",
                ),
                type="section",
            ),
        ]
    )


def test_send_raw_string_slack_alert(context):
    event = {
        "@type": "type.googleapis.com/google.pubsub.v1.PubsubMessage",
        "attributes": {
            "logging.googleapis.com/timestamp": "2022-07-22T20:36:21.891133Z"
        },
        "data": base64.b64encode(
            json.dumps("This is a raw string message").encode("ascii")
        ),
    }

    with requests_mock.Mocker() as http_mock:
        http_mock.post("https://slack.co/webhook/1234")
        response = send_slack_alert(event, context)

    assert response == "Alert sent"

    assert http_mock.call_count is 1
    assert json.loads(http_mock.request_history[0].text) == dict(
        blocks=[
            dict(
                text=dict(
                    text=":alert: UNKNOWN: This is a raw string message",
                    type="plain_text",
                ),
                type="header",
            ),
            dict(
                fields=[
                    dict(text="*Platform:*\nunknown", type="mrkdwn"),
                    dict(text="*Application:*\nunknown", type="mrkdwn"),
                    dict(text="*Log Time:*\nunknown", type="mrkdwn"),
                    dict(text="*Project:*\nproject-dev", type="mrkdwn"),
                ],
                type="section",
            ),
            dict(type="divider"),
            dict(text=dict(text="{}", type="plain_text"), type="section"),
            dict(type="divider"),
            dict(
                text=dict(
                    text=(
                        "*Next Steps*\n"
                        "1. Add some :eyes: to show you are investigating\n"
                        "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=project-dev "
                        "| Check the system is online>\n"
                        "3. Determine the cause of the error\n"
                        "4. Follow the <https://confluence.ons.gov.uk/pages/viewpage.action?pageId=98502389 "
                        "| Managing Prod Alerts> process"
                    ),
                    type="mrkdwn",
                ),
                type="section",
            ),
        ]
    )


def test_send_gce_instance_slack_alert(context):
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

    with requests_mock.Mocker() as http_mock:
        http_mock.post("https://slack.co/webhook/1234")
        response = send_slack_alert(event, context)

    assert response == "Alert sent"

    assert http_mock.call_count is 1
    assert json.loads(http_mock.request_history[0].text) == dict(
        blocks=[
            dict(
                text=dict(
                    text=":alert: ERROR: Error message from VM", type="plain_text"
                ),
                type="header",
            ),
            dict(
                fields=[
                    dict(text="*Platform:*\ngce_instance", type="mrkdwn"),
                    dict(text="*Application:*\nvm-mgmt", type="mrkdwn"),
                    dict(text="*Log Time:*\n2022-08-02 19:06:42", type="mrkdwn"),
                    dict(text="*Project:*\nproject-dev", type="mrkdwn"),
                ],
                type="section",
            ),
            dict(type="divider"),
            dict(
                text=dict(
                    text=(
                        "{\n"
                        '  "channel": "application",\n'
                        '  "description": "Error description from VM",\n'
                        '  "event_category": "0",\n'
                        '  "event_id": "0",\n'
                        '  "event_type": "error",\n'
                        '  "record_number": "6569254",\n'
                        '  "source_name": "Blaise",\n'
                        "...\n"
                        "[truncated]"
                    ),
                    type="plain_text",
                ),
                type="section",
            ),
            dict(type="divider"),
            dict(
                text=dict(
                    text=(
                        "*Next Steps*\n"
                        "1. Add some :eyes: to show you are investigating\n"
                        "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=project-dev "
                        "| Check the system is online>\n"
                        '3. <https://console.cloud.google.com/logs/query;query=severity:"WARNING"%20OR%20severity:"ERROR"%20OR%20severity:"CRITICAL"%20OR%20severity:"ALERT"%20OR%20severity:"EMERGENCY";cursorTimestamp=2022-08-02T19:06:42.275819Z?referrer=search&project=project-dev '
                        "| View the logs>\n"
                        "4. Follow the <https://confluence.ons.gov.uk/pages/viewpage.action?pageId=98502389 "
                        "| Managing Prod Alerts> process"
                    ),
                    type="mrkdwn",
                ),
                type="section",
            ),
        ]
    )


def test_send_cloud_function_slack_alert(context):
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

    with requests_mock.Mocker() as http_mock:
        http_mock.post("https://slack.co/webhook/1234")
        response = send_slack_alert(event, context)

    assert response == "Alert sent"

    assert http_mock.call_count is 1
    assert json.loads(http_mock.request_history[0].text) == dict(
        blocks=[
            dict(
                text=dict(
                    text=":alert: ERROR: Example error message", type="plain_text"
                ),
                type="header",
            ),
            dict(
                fields=[
                    dict(text="*Platform:*\ncloud_function", type="mrkdwn"),
                    dict(text="*Application:*\nlog-error", type="mrkdwn"),
                    dict(text="*Log Time:*\n2022-07-22 20:36:22", type="mrkdwn"),
                    dict(text="*Project:*\nproject-dev", type="mrkdwn"),
                ],
                type="section",
            ),
            dict(type="divider"),
            dict(
                text=dict(
                    text=(
                        "*Next Steps*\n"
                        "1. Add some :eyes: to show you are investigating\n"
                        "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=project-dev "
                        "| Check the system is online>\n"
                        '3. <https://console.cloud.google.com/logs/query;query=resource.type:"cloud_function"%20resource.labels.function_name:"log-error"%20severity:"WARNING"%20OR%20severity:"ERROR"%20OR%20severity:"CRITICAL"%20OR%20severity:"ALERT"%20OR%20severity:"EMERGENCY";cursorTimestamp=2022-07-22T20:36:22.219592Z?referrer=search&project=project-dev '
                        "| View the logs>\n"
                        "4. Follow the <https://confluence.ons.gov.uk/pages/viewpage.action?pageId=98502389 "
                        "| Managing Prod Alerts> process"
                    ),
                    type="mrkdwn",
                ),
                type="section",
            ),
        ]
    )


def test_send_app_engine_slack_alert(caplog, log_matching):
    app_engine_log_entry = {
        "httpRequest": {"status": 500},
        "insertId": "62ea8ace00082d55ac0d62b5",
        "labels": {"clone_id": "3248384304320984320483204832048"},
        "logName": "projects/project-name/logs/appengine.googleapis.com%2Frequest_log",
        "operation": {
            "first": True,
            "id": "324254354325434543543",
            "last": True,
            "producer": "appengine.googleapis.com/request_id",
        },
        "protoPayload": {
            "@type": "type.googleapis.com/google.appengine.logging.v1.RequestLog",
            "appEngineRelease": "1.9.71",
            "appId": "g~project-name",
            "endTime": "2022-08-03T14:48:46.535746Z",
            "finished": True,
            "first": True,
            "host": "0.20220803t140821.app-name.project-name.nw.r.appspot.com",
            "httpVersion": "HTTP/1.1",
            "instanceId": "45545245342",
            "ip": "0.1.0.3",
            "latency": "0.004229s",
            "line": [
                {
                    "logMessage": "Example GAE Error",
                    "severity": "ERROR",
                    "time": "2022-08-03T14:48:46.535735Z",
                }
            ],
            "method": "GET",
            "moduleId": "app-name",
            "requestId": "5435342543254325423543254325432543252345",
            "resource": "/_ah/stop",
            "responseSize": "3013",
            "spanId": "7842417449535267939",
            "startTime": "2022-08-03T14:48:46.531517Z",
            "status": 500,
            "traceId": "9998776867876876",
            "traceSampled": True,
            "urlMapEntry": "<unused>",
            "versionId": "20220803t140821",
        },
        "receiveTimestamp": "2022-08-03T14:48:46.538301573Z",
        "resource": {
            "labels": {
                "module_id": "app-name",
                "project_id": "project-name",
                "version_id": "123123123123",
                "zone": "europe-west2-3",
            },
            "type": "gae_app",
        },
        "severity": "ERROR",
        "spanId": "7842417449535267939",
        "timestamp": "2022-08-03T14:48:46.531517Z",
        "trace": "projects/project-name/traces/123123123123123123123",
        "traceSampled": True,
    }

    event = {
        "@type": "type.googleapis.com/google.pubsub.v1.PubsubMessage",
        "attributes": {
            "logging.googleapis.com/timestamp": "2022-07-22T20:36:21.891133Z"
        },
        "data": base64.b64encode(json.dumps(app_engine_log_entry).encode("ascii")),
    }

    with requests_mock.Mocker() as http_mock:
        http_mock.post("https://slack.co/webhook/1234")
        response = send_slack_alert(event, context)

    assert response == "Alert sent"

    assert http_mock.call_count is 1
    assert json.loads(http_mock.request_history[0].text) == dict(
        blocks=[
            dict(
                text=dict(text=":alert: ERROR: Example GAE Error", type="plain_text"),
                type="header",
            ),
            dict(
                fields=[
                    dict(text="*Platform:*\ngae_app", type="mrkdwn"),
                    dict(text="*Application:*\napp-name", type="mrkdwn"),
                    dict(text="*Log Time:*\n2022-08-03 14:48:46", type="mrkdwn"),
                    dict(text="*Project:*\nproject-dev", type="mrkdwn"),
                ],
                type="section",
            ),
            dict(type="divider"),
            dict(
                text=dict(
                    text="{\n"
                    '  "@type": "type.googleapis.com/google.appengine.logging.v1.RequestLog",\n'
                    '  "appEngineRelease": "1.9.71",\n'
                    '  "appId": "g~project-name",\n'
                    '  "endTime": "2022-08-03T14:48:46.535746Z",\n'
                    '  "finished": true,\n'
                    '  "first": true,\n'
                    '  "host": "0.20220803t140821.app-name.project-name.nw.r.appspot.com",\n'
                    "...\n"
                    "[truncated]",
                    type="plain_text",
                ),
                type="section",
            ),
            dict(type="divider"),
            dict(
                text=dict(
                    text="*Next Steps*\n"
                    "1. Add some :eyes: to show you are "
                    "investigating\n"
                    "2. "
                    "<https://console.cloud.google.com/monitoring/uptime?referrer=search&project=project-dev "
                    "| Check the system is online>\n"
                    "3. "
                    '<https://console.cloud.google.com/logs/query;query=resource.type:"gae_app"%20resource.labels.module_id:"app-name"%20severity:"WARNING"%20OR%20severity:"ERROR"%20OR%20severity:"CRITICAL"%20OR%20severity:"ALERT"%20OR%20severity:"EMERGENCY";cursorTimestamp=2022-08-03T14:48:46.538301Z?referrer=search&project=project-dev '
                    "| View the logs>\n"
                    "4. Follow the "
                    "<https://confluence.ons.gov.uk/pages/viewpage.action?pageId=98502389 "
                    "| Managing Prod Alerts> process",
                    type="mrkdwn",
                ),
                type="section",
            ),
        ]
    )
