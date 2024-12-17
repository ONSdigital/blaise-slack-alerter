import base64
import json
import logging
import os
from typing import Union

import pytest
import pytz
import requests_mock
from dateutil.parser import parse
from flask import Request

from lib.cloud_logging.log_query_link import create_log_query_link
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


@pytest.fixture()
def http_mock():
    with requests_mock.Mocker() as http_mock:
        yield http_mock


@pytest.fixture()
def number_of_http_calls(http_mock):
    def get():
        return http_mock.call_count

    return get


@pytest.fixture()
def run_slack_alerter(context, http_mock):
    def run(event):
        http_mock.post("https://slack.co/webhook/1234")
        return send_slack_alert(event, context)

    return run


@pytest.fixture()
def get_webhook_payload(http_mock):
    def get():
        assert (
            http_mock.call_count is 1
        ), f"Expected one call to the Slack webhook, got {http_mock.call_count}"
        return json.loads(http_mock.request_history[0].text)

    return get


def create_event(data: Union[dict, str]) -> dict:
    return {
        "@type": "type.googleapis.com/google.pubsub.v1.PubsubMessage",
        "attributes": {
            "logging.googleapis.com/timestamp": "2022-07-22T20:36:21.891133Z"
        },
        "data": base64.b64encode(json.dumps(data).encode("ascii")),
    }


def test_bad_pubsub_envelope(get_webhook_payload, run_slack_alerter):
    event = create_event("")
    del event["data"]

    response = run_slack_alerter(event)

    assert response == "Alert sent (invalid envelope)"
    assert get_webhook_payload() == convert_slack_message_to_blocks(
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


def test_send_raw_string_slack_alert(get_webhook_payload, run_slack_alerter):
    event = create_event("This is a raw string message")
    response = run_slack_alerter(event)

    assert response == "Alert sent"
    assert get_webhook_payload() == convert_slack_message_to_blocks(
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


def test_send_gce_instance_slack_alert(run_slack_alerter, get_webhook_payload):
    gce_instance_log_entry = {
        "jsonPayload": {
            "computer_name": "vm-mgmt",
            "description": "Error description from VM",
            "event_type": "error",
            "message": "Error message from VM",
        },
        "receiveTimestamp": "2022-08-02T19:06:42.275819947Z",
        "resource": {
            "labels": {
                "instance_id": "89453598437598",
            },
            "type": "gce_instance",
        },
        "severity": "ERROR",
    }
    event = create_event(gce_instance_log_entry)

    response = run_slack_alerter(event)

    assert response == "Alert sent"
    expected_log_query_link = create_log_query_link(
        {
            "resource.type": "gce_instance",
            "resource.labels.instance_id": "89453598437598",
        },
        ["WARNING", "ERROR", "CRITICAL", "ALERT", "EMERGENCY", "DEBUG"],
        parse("2022-08-02T19:06:42.275819Z"),
        "project-dev",
    )

    assert get_webhook_payload() == convert_slack_message_to_blocks(
        SlackMessage(
            title=":alert: ERROR: Error message from VM",
            fields={
                "Platform": "gce_instance",
                "Application": "vm-mgmt",
                "Log Time": "2022-08-02 20:06:42",
                "Project": "project-dev",
            },
            content="description: Error description from VM\n" "event_type: error",
            footnote=(
                "*Next Steps*\n"
                "1. Add some :eyes: to show you are investigating\n"
                "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=project-dev "
                "| Check the system is online>\n"
                f"3. <{expected_log_query_link} | View the logs>\n"
                "4. Follow the <https://confluence.ons.gov.uk/pages/viewpage.action?pageId=98502389 "
                "| Managing Prod Alerts> process"
            ),
        )
    )


def test_send_cloud_run_revision_slack_alert(run_slack_alerter, get_webhook_payload):
    cloud_run_revision_log_entry = {
        "receiveTimestamp": "2022-07-22T20:36:22.219592062Z",
        "resource": {
            "labels": {
                "service_name": "log-error",
            },
            "type": "cloud_run_revision",
        },
        "severity": "ERROR",
        "textPayload": "Example error message",
    }
    event = create_event(cloud_run_revision_log_entry)

    response = run_slack_alerter(event)

    assert response == "Alert sent"
    expected_log_query_link = create_log_query_link(
        {
            "resource.type": "cloud_run_revision",
            "resource.labels.service_name": "log-error",
        },
        ["WARNING", "ERROR", "CRITICAL", "ALERT", "EMERGENCY", "DEBUG"],
        parse("2022-07-22T20:36:22.219592Z"),
        "project-dev",
    )

    assert get_webhook_payload() == convert_slack_message_to_blocks(
        SlackMessage(
            title=":alert: ERROR: Example error message",
            fields={
                "Platform": "cloud_run_revision",
                "Application": "log-error",
                "Log Time": "2022-07-22 21:36:22",
                "Project": "project-dev",
            },
            content="",
            footnote=(
                "*Next Steps*\n"
                "1. Add some :eyes: to show you are investigating\n"
                "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=project-dev "
                "| Check the system is online>\n"
                f"3. <{expected_log_query_link} | View the logs>\n"
                "4. Follow the <https://confluence.ons.gov.uk/pages/viewpage.action?pageId=98502389 "
                "| Managing Prod Alerts> process"
            ),
        )
    )


def test_send_cloud_run_revision_timeout_slack_alert(
    run_slack_alerter, get_webhook_payload
):
    cloud_run_revision_log_entry = {
        "receiveTimestamp": "2022-12-15T04:09:02.428095884Z",
        "resource": {
            "labels": {
                "service_name": "log-error",
            },
            "type": "cloud_run_revision",
        },
        "severity": "DEBUG",
        "textPayload": "Function execution took 540141 ms. Finished with status: timeout",
    }
    event = create_event(cloud_run_revision_log_entry)

    response = run_slack_alerter(event)

    assert response == "Alert sent"
    expected_log_query_link = create_log_query_link(
        {
            "resource.type": "cloud_run_revision",
            "resource.labels.service_name": "log-error",
        },
        ["WARNING", "ERROR", "CRITICAL", "ALERT", "EMERGENCY", "DEBUG"],
        parse("2022-12-15T04:09:02.428095Z").astimezone(pytz.timezone("Europe/London")),
        "project-dev",
    )
    assert get_webhook_payload() == convert_slack_message_to_blocks(
        SlackMessage(
            title=":alert: DEBUG: Function execution took 540141 ms. Finished with status: timeout",
            fields={
                "Platform": "cloud_run_revision",
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
                f"3. <{expected_log_query_link} | View the logs>\n"
                "4. Follow the <https://confluence.ons.gov.uk/pages/viewpage.action?pageId=98502389 "
                "| Managing Prod Alerts> process"
            ),
        )
    )


def test_send_app_engine_slack_alert(
    run_slack_alerter, caplog, log_matching, get_webhook_payload
):
    app_engine_log_entry = {
        "protoPayload": {
            "host": "0.20220803t140821.app-name.project-name.nw.r.appspot.com",
            "httpVersion": "HTTP/1.1",
            "ip": "0.1.0.3",
            "latency": "0.004229s",
            "line": [
                {
                    "logMessage": "Example GAE Error",
                }
            ],
            "method": "GET",
            "resource": "/_ah/stop",
            "responseSize": "3013",
            "status": 500,
        },
        "receiveTimestamp": "2022-08-03T14:48:46.538301573Z",
        "resource": {
            "labels": {
                "module_id": "app-name",
            },
            "type": "gae_app",
        },
        "severity": "ERROR",
    }
    event = create_event(app_engine_log_entry)

    response = run_slack_alerter(event)

    assert response == "Alert sent"
    expected_log_query_link = create_log_query_link(
        {"resource.type": "gae_app", "resource.labels.module_id": "app-name"},
        ["WARNING", "ERROR", "CRITICAL", "ALERT", "EMERGENCY", "DEBUG"],
        parse("2022-08-03T14:48:46.538301Z"),
        "project-dev",
    )
    assert get_webhook_payload() == convert_slack_message_to_blocks(
        SlackMessage(
            title=":alert: ERROR: Example GAE Error",
            fields={
                "Platform": "gae_app",
                "Application": "app-name",
                "Log Time": "2022-08-03 15:48:46",
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
                f"3. <{expected_log_query_link} | View the logs>\n"
                "4. Follow the "
                "<https://confluence.ons.gov.uk/pages/viewpage.action?pageId=98502389 "
                "| Managing Prod Alerts> process"
            ),
        )
    )


def test_send_audit_log_slack_alert(
    run_slack_alerter, caplog, log_matching, get_webhook_payload
):
    audit_log_log_entry = {
        "protoPayload": {
            "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
            "status": {
                "message": "serving status cannot be changed for Automatic Scaling versions",
            },
            "requestMetadata": {
                "callerIp": "gce-internal-ip",
                "requestAttributes": {
                    "time": "2022-09-06T21:32:11.279689Z",
                },
            },
            "serviceName": "appengine.googleapis.com",
            "methodName": "google.appengine.v1.Versions.UpdateVersion",
        },
        "resource": {
            "type": "gae_app",
        },
        "severity": "ERROR",
        "receiveTimestamp": "2022-09-06T21:32:11.332410850Z",
    }
    event = create_event(audit_log_log_entry)

    response = run_slack_alerter(event)

    assert response == "Alert sent"
    expected_log_query_link = create_log_query_link(
        {"protoPayload.@type": "type.googleapis.com/google.cloud.audit.AuditLog"},
        ["WARNING", "ERROR", "CRITICAL", "ALERT", "EMERGENCY", "DEBUG"],
        parse("2022-09-06T21:32:11.332410850Z"),
        "project-dev",
    )

    assert get_webhook_payload() == convert_slack_message_to_blocks(
        SlackMessage(
            title=":alert: ERROR: [AuditLog] serving status cannot be changed for Automatic Scaling versions",
            fields={
                "Platform": "gae_app",
                "Application": "[unknown]",
                "Log Time": "2022-09-06 22:32:11",
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
                f"3. <{expected_log_query_link} | View the logs>\n"
                "4. Follow the "
                "<https://confluence.ons.gov.uk/pages/viewpage.action?pageId=98502389 "
                "| Managing Prod Alerts> process"
            ),
        )
    )


def test_send_erroneous_questionnaire_for_preprod_alerts(
    run_slack_alerter, get_webhook_payload
):
    # arrange
    example_log_entry = {
        "insertId": "6538efc60003b62c3cbdd1b4",
        "jsonPayload": {
            "hostname": "localhost",
            "message": "AUDIT_LOG: Failed to install questionnaire OPN2310_FO0",
            "info": {},
            "time": 1698230214243,
            "req": {"url": "/api/install", "method": "POST"},
            "pid": 11,
            "level": 50,
        },
        "resource": {
            "type": "gae_app",
            "labels": {
                "version_id": "20231012t154121",
                "zone": "europe-west2-2",
                "project_id": "ons-blaise-v2-preprod",
                "module_id": "dqs-ui",
            },
        },
        "timestamp": "2023-10-25T10:36:54.243244Z",
        "severity": "ERROR",
        "labels": {
            "clone_id": "0037d6d5d3b46943e8ac10f4dbc904507f2621188b0db8eafc6bf828e40168d6d488d2d11a8c8307b7823978eda05e745c2762d66dba9c7642106aca409cfae42aa6b8"
        },
        "logName": "projects/ons-blaise-v2-preprod/logs/stdout",
        "receiveTimestamp": "2023-10-25T10:36:54.419325796Z",
    }
    event = create_event(example_log_entry)
    expected_log_query_link = create_log_query_link(
        {"resource.type": "gae_app", "resource.labels.module_id": "dqs-ui"},
        ["WARNING", "ERROR", "CRITICAL", "ALERT", "EMERGENCY", "DEBUG"],
        parse("2023-10-25T10:36:54.419325Z"),
        "project-dev",
    )

    # act
    response = run_slack_alerter(event)

    # assert
    assert response == "Alert sent"
    assert get_webhook_payload() == convert_slack_message_to_blocks(
        SlackMessage(
            title=":alert: ERROR: AUDIT_LOG: Failed to install questionnaire OPN2310_FO0",
            fields={
                "Platform": "gae_app",
                "Application": "dqs-ui",
                "Log Time": "2023-10-25 11:36:54",
                "Project": "project-dev",
            },
            content=(
                "{\n  "
                '"hostname": "localhost",\n  '
                '"info": {},\n  '
                '"time": 1698230214243,\n  '
                '"req": {\n'
                '    "url": "/api/install",\n'
                '    "method": "POST"\n'
                "  },\n"
                "...\n"
                "[truncated]"
            ),
            footnote=(
                "*Next Steps*\n"
                "1. Add some :eyes: to show you are investigating\n"
                "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=project-dev | Check the system is online>\n"
                f"3. <{expected_log_query_link} | View the logs>\n"
                "4. Follow the <https://confluence.ons.gov.uk/pages/viewpage.action?pageId=98502389 | Managing Prod Alerts> process"
            ),
        )
    )
