import base64
import json
import logging
import os
from typing import Union

import pytest
import requests_mock
from flask import Request

from lib.slack import SlackMessage
from lib.slack.slack_message_formatter import convert_slack_message_to_blocks
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


def create_event(data: Union[dict, str]) -> dict:
    return {
        "@type": "type.googleapis.com/google.pubsub.v1.PubsubMessage",
        "attributes": {
            "logging.googleapis.com/timestamp": "2022-07-22T20:36:21.891133Z"
        },
        "data": base64.b64encode(json.dumps(data).encode("ascii")),
    }


def test_bad_pubsub_envelope(context):
    event = create_event("")

    del event["data"]

    with requests_mock.Mocker() as http_mock:
        http_mock.post("https://slack.co/webhook/1234")
        response = send_slack_alert(event, context)

    assert response == "Alert sent (invalid envelope)"

    assert http_mock.call_count is 1
    assert json.loads(
        http_mock.request_history[0].text
    ) == convert_slack_message_to_blocks(
        SlackMessage(
            title="Error with bad format received",
            fields={
                "Platform": "unknown",
                "Application": "unknown",
                "Log Time": "unknown",
                "Project": "project-dev",
            },
            content="{\n"
            '  "@type": "type.googleapis.com/google.pubsub.v1.PubsubMessage",\n'
            '  "attributes": {\n'
            '    "logging.googleapis.com/timestamp": "2022-07-22T20:36:21.891133Z"\n'
            "  }\n"
            "}",
            footnote=(
                "This message was not in an expected format; "
                "consider extending the alerting lambda to support this message type."
            ),
        )
    )


def test_send_raw_string_slack_alert(context):
    event = create_event("This is a raw string message")

    with requests_mock.Mocker() as http_mock:
        http_mock.post("https://slack.co/webhook/1234")
        response = send_slack_alert(event, context)

    assert response == "Alert sent"

    assert http_mock.call_count is 1
    assert json.loads(
        http_mock.request_history[0].text
    ) == convert_slack_message_to_blocks(
        SlackMessage(
            title=":alert: UNKNOWN: This is a raw string message",
            fields={
                "Platform": "unknown",
                "Application": "unknown",
                "Log Time": "unknown",
                "Project": "project-dev",
            },
            content="{}",
            footnote=(
                "*Next Steps*\n"
                "1. Add some :eyes: to show you are investigating\n"
                "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=project-dev "
                "| Check the system is online>\n"
                "3. Determine the cause of the error\n"
                "4. Follow the <https://confluence.ons.gov.uk/pages/viewpage.action?pageId=98502389 "
                "| Managing Prod Alerts> process"
            ),
        )
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

    event = create_event(gce_instance_log_entry)

    with requests_mock.Mocker() as http_mock:
        http_mock.post("https://slack.co/webhook/1234")
        response = send_slack_alert(event, context)

    assert response == "Alert sent"

    assert http_mock.call_count is 1
    assert json.loads(
        http_mock.request_history[0].text
    ) == convert_slack_message_to_blocks(
        SlackMessage(
            title=":alert: ERROR: Error message from VM",
            fields={
                "Platform": "gce_instance",
                "Application": "vm-mgmt",
                "Log Time": "2022-08-02 19:06:42",
                "Project": "project-dev",
            },
            content="description: Error description from VM\n" "event_type: error",
            footnote=(
                "*Next Steps*\n"
                "1. Add some :eyes: to show you are investigating\n"
                "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=project-dev "
                "| Check the system is online>\n"
                "3. <https://console.cloud.google.com/logs/query;query=resource.type:%22gce_instance%22%20resource.labels.instance_id:%2289453598437598%22%20severity%3D%28WARNING%20OR%20ERROR%20OR%20CRITICAL%20OR%20ALERT%20OR%20EMERGENCY%20OR%20DEBUG%29;cursorTimestamp=2022-08-02T19:06:42.275819Z?referrer=search&project=project-dev "
                "| View the logs>\n"
                "4. Follow the <https://confluence.ons.gov.uk/pages/viewpage.action?pageId=98502389 "
                "| Managing Prod Alerts> process"
            ),
        )
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

    event = create_event(cloud_function_log_entry)

    with requests_mock.Mocker() as http_mock:
        http_mock.post("https://slack.co/webhook/1234")
        response = send_slack_alert(event, context)

    assert response == "Alert sent"

    assert http_mock.call_count is 1
    assert json.loads(
        http_mock.request_history[0].text
    ) == convert_slack_message_to_blocks(
        SlackMessage(
            title=":alert: ERROR: Example error message",
            fields={
                "Platform": "cloud_function",
                "Application": "log-error",
                "Log Time": "2022-07-22 20:36:22",
                "Project": "project-dev",
            },
            content="",
            footnote=(
                "*Next Steps*\n"
                "1. Add some :eyes: to show you are investigating\n"
                "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=project-dev "
                "| Check the system is online>\n"
                "3. "
                "<https://console.cloud.google.com/logs/query;query=resource.type:%22cloud_function%22%20resource.labels.function_name:%22log-error%22%20severity%3D%28WARNING%20OR%20ERROR%20OR%20CRITICAL%20OR%20ALERT%20OR%20EMERGENCY%20OR%20DEBUG%29;cursorTimestamp=2022-07-22T20:36:22.219592Z?referrer=search&project=project-dev "
                "| View the logs>\n"
                "4. Follow the <https://confluence.ons.gov.uk/pages/viewpage.action?pageId=98502389 "
                "| Managing Prod Alerts> process"
            ),
        )
    )


def test_send_cloud_function_timeout_slack_alert(context):
    cloud_function_log_entry = {
        "httpRequest": {
            "protocol": "HTTP/1.1",
            "requestMethod": "POST",
            "requestUrl": "http://example.appspot.com",
            "userAgent": "Go-http-client/1.1",
        },
        "insertId": "120vmazff6yru6",
        "labels": {"execution_id": "zgvo2jb4fhlj"},
        "logName": "projects/secret-project/logs/cloudfunctions.googleapis.com%2Fcloud-functions",
        "receiveTimestamp": "2022-12-15T04:09:02.428095884Z",
        "resource": {
            "labels": {
                "function_name": "log-error",
                "project_id": "secret-project",
                "region": "europe-west2",
            },
            "type": "cloud_function",
        },
        "severity": "DEBUG",
        "textPayload": "Function execution took 540141 ms. Finished with status: timeout",
        "timestamp": "2022-12-15T04:09:02.421848610Z",
        "trace": "projects/ons-blaise-v2-prod/traces/6476b882189959963206ce9b6b78a6ff",
    }

    event = create_event(cloud_function_log_entry)

    with requests_mock.Mocker() as http_mock:
        http_mock.post("https://slack.co/webhook/1234")
        response = send_slack_alert(event, context)

    assert response == "Alert sent"

    assert http_mock.call_count is 1
    assert json.loads(
        http_mock.request_history[0].text
    ) == convert_slack_message_to_blocks(
        SlackMessage(
            title=":alert: DEBUG: Function execution took 540141 ms. Finished with status: timeout",
            fields={
                "Platform": "cloud_function",
                "Application": "log-error",
                "Log Time": "2022-12-15 04:09:02",
                "Project": "project-dev",
            },
            content="",
            footnote=(
                "*Next Steps*\n"
                "1. Add some :eyes: to show you are investigating\n"
                "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=project-dev "
                "| Check the system is online>\n"
                "3. "
                "<https://console.cloud.google.com/logs/query;query=resource.type:%22cloud_function%22%20resource.labels.function_name:%22log-error%22%20severity%3D%28WARNING%20OR%20ERROR%20OR%20CRITICAL%20OR%20ALERT%20OR%20EMERGENCY%20OR%20DEBUG%29;cursorTimestamp=2022-12-15T04:09:02.428095Z?referrer=search&project=project-dev "
                "| View the logs>\n"
                "4. Follow the <https://confluence.ons.gov.uk/pages/viewpage.action?pageId=98502389 "
                "| Managing Prod Alerts> process"
            ),
        )
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

    event = create_event(app_engine_log_entry)

    with requests_mock.Mocker() as http_mock:
        http_mock.post("https://slack.co/webhook/1234")
        response = send_slack_alert(event, context)

    assert response == "Alert sent"

    assert http_mock.call_count is 1
    assert json.loads(
        http_mock.request_history[0].text
    ) == convert_slack_message_to_blocks(
        SlackMessage(
            title=":alert: ERROR: Example GAE Error",
            fields={
                "Platform": "gae_app",
                "Application": "app-name",
                "Log Time": "2022-08-03 14:48:46",
                "Project": "project-dev",
            },
            content="status: 500\n"
            "host: 0.20220803t140821.app-name.project-name.nw.r.appspot.com\n"
            "method: GET\n"
            "resource: /_ah/stop\n"
            "ip: 0.1.0.3\n"
            "latency: 0.004229s\n"
            "responseSize: 3013\n"
            "httpVersion: HTTP/1.1",
            footnote=(
                "*Next Steps*\n"
                "1. Add some :eyes: to show you are "
                "investigating\n"
                "2. "
                "<https://console.cloud.google.com/monitoring/uptime?referrer=search&project=project-dev "
                "| Check the system is online>\n"
                "3. "
                "<https://console.cloud.google.com/logs/query;query=resource.type:%22gae_app%22%20resource.labels.module_id:%22app-name%22%20severity%3D%28WARNING%20OR%20ERROR%20OR%20CRITICAL%20OR%20ALERT%20OR%20EMERGENCY%20OR%20DEBUG%29;cursorTimestamp=2022-08-03T14:48:46.538301Z?referrer=search&project=project-dev "
                "| View the logs>\n"
                "4. Follow the "
                "<https://confluence.ons.gov.uk/pages/viewpage.action?pageId=98502389 "
                "| Managing Prod Alerts> process"
            ),
        )
    )


def test_send_audit_log_slack_alert(caplog, log_matching):
    audit_log_log_entry = {
        "protoPayload": {
            "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
            "status": {
                "code": 3,
                "message": "serving status cannot be changed for Automatic Scaling versions",
            },
            "authenticationInfo": {
                "principalEmail": "concourse@ons-blaise-v2-prod.iam.gserviceaccount.com",
                "serviceAccountKeyName": "//iam.googleapis.com/projects/ons-blaise-v2-prod/serviceAccounts/concourse@ons-blaise-v2-prod.iam.gserviceaccount.com/keys/0772af21bb3c6fdc858833af9590797c0ec0c5d5",
            },
            "requestMetadata": {
                "callerIp": "gce-internal-ip",
                "requestAttributes": {
                    "time": "2022-09-06T21:32:11.279689Z",
                    "auth": {},
                },
                "destinationAttributes": {},
            },
            "serviceName": "appengine.googleapis.com",
            "methodName": "google.appengine.v1.Versions.UpdateVersion",
            "authorizationInfo": [
                {
                    "resource": "apps/ons-blaise-v2-prod/services/default/versions/20210216t165030",
                    "permission": "appengine.versions.update",
                    "granted": True,
                    "resourceAttributes": {},
                }
            ],
            "resourceName": "apps/ons-blaise-v2-prod/services/default/versions/20210216t165030",
            "resourceLocation": {"currentLocations": ["europe-west2"]},
        },
        "insertId": "-y4awqhd1brg",
        "resource": {
            "type": "gae_app",
            "labels": {
                "zone": "",
                "project_id": "ons-blaise-v2-prod",
                "version_id": "20210216t165030",
                "module_id": "default",
            },
        },
        "timestamp": "2022-09-06T21:32:11.237805Z",
        "severity": "ERROR",
        "logName": "projects/ons-blaise-v2-prod/logs/cloudaudit.googleapis.com%2Factivity",
        "receiveTimestamp": "2022-09-06T21:32:11.332410850Z",
    }

    event = create_event(audit_log_log_entry)

    with requests_mock.Mocker() as http_mock:
        http_mock.post("https://slack.co/webhook/1234")
        response = send_slack_alert(event, context)

    assert response == "Alert sent"

    assert http_mock.call_count is 1
    assert json.loads(
        http_mock.request_history[0].text
    ) == convert_slack_message_to_blocks(
        SlackMessage(
            title=":alert: ERROR: [AuditLog] serving status cannot be changed for Automatic Scaling versions",
            fields={
                "Platform": "gae_app",
                "Application": "[unknown]",
                "Log Time": "2022-09-06 21:32:11",
                "Project": "project-dev",
            },
            content="serviceName: appengine.googleapis.com\n"
            "methodName: google.appengine.v1.Versions.UpdateVersion\n"
            "requestMetadata.callerIp: gce-internal-ip\n"
            "requestMetadata.requestAttributes.time: 2022-09-06T21:32:11.279689Z",
            footnote=(
                "*Next Steps*\n"
                "1. Add some :eyes: to show you are "
                "investigating\n"
                "2. "
                "<https://console.cloud.google.com/monitoring/uptime?referrer=search&project=project-dev "
                "| Check the system is online>\n"
                "3. "
                "<https://console.cloud.google.com/logs/query;query=protoPayload.@type:%22type.googleapis.com/google.cloud.audit.AuditLog%22%20severity%3D%28WARNING%20OR%20ERROR%20OR%20CRITICAL%20OR%20ALERT%20OR%20EMERGENCY%20OR%20DEBUG%29;cursorTimestamp=2022-09-06T21:32:11.332410Z?referrer=search&project=project-dev "
                "| View the logs>\n"
                "4. Follow the "
                "<https://confluence.ons.gov.uk/pages/viewpage.action?pageId=98502389 "
                "| Managing Prod Alerts> process"
            ),
        )
    )
