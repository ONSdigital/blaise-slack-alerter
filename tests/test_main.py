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
            "ip": "203.0.113.1",
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
            "ip: 203.0.113.1\n"
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


def test_skip_data_delivery_json_error(run_slack_alerter, number_of_http_calls, caplog):
    # arrange
    example_log_entry = {
        "insertId": "yhmlfg26ror8hccek",
        "jsonPayload": {
            "event_type": "error",
            "event_category": "0",
            "source_name": "OSConfigAgent",
            "record_number": "1880074",
            "user": "",
            "channel": "application",
            "description": "2023-02-25T03:46:49.1619Z OSConfigAgent Error main.go:231: unexpected end of JSON input\r\n",
            "time_generated": "2023-02-25 03:46:49 +0000",
            "computer_name": "blaise-gusty-data-entry-1",
            "time_written": "2023-02-25 03:46:49 +0000",
            "event_id": "882",
            "string_inserts": [
                "2023-02-25T03:46:49.1619Z OSConfigAgent Error main.go:231: unexpected end of JSON input"
            ],
            "message": "2023-02-25T03:46:49.1619Z OSConfigAgent Error main.go:231: unexpected end of JSON input\r\n",
        },
        "resource": {
            "type": "gce_instance",
            "labels": {
                "instance_id": "458491889528639951",
                "project_id": "ons-blaise-v2-prod",
                "zone": "europe-west2-a",
            },
        },
        "timestamp": "2023-02-25T03:46:49Z",
        "severity": "ERROR",
        "labels": {"compute.googleapis.com/resource_name": "blaise-gusty-data-entry-1"},
        "logName": "projects/ons-blaise-v2-prod/logs/winevt.raw",
        "receiveTimestamp": "2023-02-25T03:46:57.099633534Z",
    }
    event = create_event(example_log_entry)

    # act
    with caplog.at_level(logging.INFO):
        response = run_slack_alerter(event)

    # assert
    assert response == "Alert skipped"
    assert number_of_http_calls() == 0
    assert (
        "root",
        logging.INFO,
        "Skipping os config agent alert",
    ) in caplog.record_tuples


def test_skip_audit_logs_error(run_slack_alerter, number_of_http_calls, caplog):
    # arrange
    example_log_entry = {
        "protoPayload": {
            "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
            "status": {"code": 7},
            "authenticationInfo": {
                "principalEmail": "pipeline-bucket-reader@ons-blaise-v2-shared.iam.gserviceaccount.com",
                "serviceAccountKeyName": "//iam.googleapis.com/projects/ons-blaise-v2-shared/serviceAccounts/pipeline-bucket-reader@ons-blaise-v2-shared.iam.gserviceaccount.com/keys/221e50eb36c76f17c5f6883a5a0bb29c1535ba8a",
            },
            "requestMetadata": {
                "callerIp": "gcp-internal-ip",
                "callerSuppliedUserAgent": "apitools Python/3.7.9 gsutil/5.3 (win32) analytics/enabled interactive/False command/cp google-cloud-sdk/360.0.0,gzip(gfe)",
                "callerNetwork": "//compute.googleapis.com/projects/ons-blaise-v2-prod/global/networks/__unknown__",
                "requestAttributes": {
                    "time": "2023-04-14T00:42:09.609760345Z",
                    "auth": {},
                },
                "destinationAttributes": {},
            },
            "serviceName": "storage.googleapis.com",
            "methodName": "storage.objects.list",
            "authorizationInfo": [
                {
                    "resource": "projects/_/buckets/ons-blaise-v2-prod-winvm-data",
                    "permission": "storage.objects.list",
                    "resourceAttributes": {},
                }
            ],
            "resourceName": "projects/_/buckets/ons-blaise-v2-prod-winvm-data",
            "resourceLocation": {"currentLocations": ["europe-west2"]},
        },
        "insertId": "pt5jaee3fznz",
        "resource": {
            "type": "gcs_bucket",
            "labels": {
                "location": "europe-west2",
                "bucket_name": "ons-blaise-v2-prod-winvm-data",
                "project_id": "ons-blaise-v2-prod",
            },
        },
        "timestamp": "2023-04-14T00:42:09.598152915Z",
        "severity": "ERROR",
        "logName": "projects/ons-blaise-v2-prod/logs/cloudaudit.googleapis.com%2Fdata_access",
        "receiveTimestamp": "2023-04-14T00:42:11.064730027Z",
    }
    event = create_event(example_log_entry)

    # act
    with caplog.at_level(logging.INFO):
        response = run_slack_alerter(event)

    # assert
    assert response == "Alert skipped"
    assert number_of_http_calls() == 0
    assert ("root", logging.INFO, "Skipping audit log alert") in caplog.record_tuples


def test_skip_osconfig_agent_unexpected_end_of_json_input_error(
    run_slack_alerter, number_of_http_calls, caplog
):
    # arrange
    example_log_entry = {
        "insertId": "ak4u0bf38r70c",
        "jsonPayload": {
            "localTimestamp": "2023-05-18T13:22:14.1873+01:00",
            "omitempty": None,
            "message": "unexpected end of JSON input",
        },
        "resource": {
            "type": "gce_instance",
            "labels": {
                "zone": "europe-west2-a",
                "instance_id": "2340080223918060770",
                "project_id": "ons-blaise-v2-prod",
            },
        },
        "timestamp": "2023-05-18T12:22:14.230839200Z",
        "severity": "ERROR",
        "labels": {
            "instance_name": "restapi-3",
            "agent_version": "20230330.00.0+win@1",
        },
        "logName": "projects/ons-blaise-v2-prod/logs/OSConfigAgent",
        "sourceLocation": {
            "file": "main.go",
            "line": "231",
            "function": "main.runTaskLoop",
        },
        "receiveTimestamp": "2023-05-18T12:22:16.434926842Z",
    }
    event = create_event(example_log_entry)

    # act
    with caplog.at_level(logging.INFO):
        response = run_slack_alerter(event)

    # assert
    assert response == "Alert skipped"
    assert number_of_http_calls() == 0
    assert (
        "root",
        logging.INFO,
        "Skipping os config agent alert",
    ) in caplog.record_tuples


def test_skip_agent_connect_error(run_slack_alerter, number_of_http_calls, caplog):
    # arrange
    example_log_entry = {
        "insertId": "qysctppk7v9cttt1g",
        "jsonPayload": {
            "event_id": "100",
            "event_category": "0",
            "time_generated": "2023-06-06 15:36:14 +0100",
            "user": "",
            "time_written": "2023-06-06 15:36:14 +0100",
            "message": "2023-06-06 14:36:14Z: Agent connect error: The HTTP request timed out after 00:01:00.. Retrying until reconnected.\r\n",
            "channel": "application",
            "computer_name": "data-delivery",
            "event_type": "error",
            "string_inserts": [
                "2023-06-06 14:36:14Z: Agent connect error: The HTTP request timed out after 00:01:00.. Retrying until reconnected."
            ],
            "description": "2023-06-06 14:36:14Z: Agent connect error: The HTTP request timed out after 00:01:00.. Retrying until reconnected.\r\n",
            "record_number": "1807900",
            "source_name": "VstsAgentService",
        },
        "resource": {
            "type": "gce_instance",
            "labels": {
                "instance_id": "9047556346870592737",
                "project_id": "ons-blaise-v2-prod",
                "zone": "europe-west2-a",
            },
        },
        "timestamp": "2023-06-06T14:36:14Z",
        "severity": "ERROR",
        "labels": {"compute.googleapis.com/resource_name": "data-delivery"},
        "logName": "projects/ons-blaise-v2-prod/logs/winevt.raw",
        "receiveTimestamp": "2023-06-06T14:36:21.643430478Z",
    }
    event = create_event(example_log_entry)

    # act
    with caplog.at_level(logging.INFO):
        response = run_slack_alerter(event)

    # assert
    assert response == "Alert skipped"
    assert number_of_http_calls() == 0
    assert (
        "root",
        logging.INFO,
        "Skipping agent connect alert",
    ) in caplog.record_tuples


def test_skip_rproxy_lookupEffectiveGuestPolicies_error(
    run_slack_alerter, number_of_http_calls, caplog
):
    # arrange
    example_log_entry = {
        "insertId": "i1tjpyftm0qks",
        "jsonPayload": {
            "message": 'Error running LookupEffectiveGuestPolicies: error calling LookupEffectiveGuestPolicies: code: "NotFound", message: "Requested entity was not found.", details: []',
            "localTimestamp": "2023-09-28T08:45:35.1241Z",
            "omitempty": None,
        },
        "resource": {
            "type": "gce_instance",
            "labels": {
                "zone": "europe-west2-a",
            },
        },
        "timestamp": "2023-09-28T08:45:35.136331729Z",
        "severity": "ERROR",
        "labels": {"instance_name": "rproxy-b0bd8e4b", "agent_version": "20230403.00"},
        "logName": "projects/ons-blaise-v2-prod/logs/OSConfigAgent",
        "sourceLocation": {
            "file": "policies.go",
            "line": "49",
            "function": "github.com/GoogleCloudPlatform/osconfig/policies.run",
        },
        "receiveTimestamp": "2023-09-28T08:45:36.225541583Z",
    }
    event = create_event(example_log_entry)

    # act
    with caplog.at_level(logging.INFO):
        response = run_slack_alerter(event)

    # assert
    assert response == "Alert skipped"
    assert number_of_http_calls() == 0
    assert (
        "root",
        logging.INFO,
        "Skipping rproxy lookupEffectiveGuestPolicies alert",
    ) in caplog.record_tuples


def test_skip_watching_metadata_invalid_character_error(
    run_slack_alerter, number_of_http_calls, caplog
):
    # arrange
    example_log_entry = {
        "insertId": "19s550gfh2251m",
        "jsonPayload": {
            "localTimestamp": "2023-09-18T15:12:28.8451+01:00",
            "message": "Error watching metadata: invalid character '<' looking for beginning of value",
            "omitempty": None,
        },
        "resource": {
            "type": "gce_instance",
            "labels": {
                "project_id": "ons-blaise-v2-prod",
                "instance_id": "5203162520768539890",
                "zone": "europe-west2-a",
            },
        },
        "timestamp": "2023-09-18T14:12:28.853979600Z",
        "severity": "ERROR",
        "labels": {"instance_name": "blaise-gusty-data-entry-4"},
        "logName": "projects/ons-blaise-v2-prod/logs/GCEGuestAgent",
        "sourceLocation": {
            "file": "metadata.go",
            "line": "74",
            "function": "github.com/GoogleCloudPlatform/guest-agent/google_guest_agent/events/metadata.(*Watcher).Run",
        },
        "receiveTimestamp": "2023-09-18T14:12:29.912569518Z",
    }
    event = create_event(example_log_entry)

    # act
    with caplog.at_level(logging.INFO):
        response = run_slack_alerter(event)

    # assert
    assert response == "Alert skipped"
    assert number_of_http_calls() == 0
    assert (
        "root",
        logging.INFO,
        "Skipping watching metadata invalid character alert",
    ) in caplog.record_tuples


def test_skip_watching_metadata_invalid_character_second_version_error(
    run_slack_alerter, number_of_http_calls, caplog
):
    # arrange
    example_log_entry = {
        "insertId": "hohgijl11degyrvc0",
        "jsonPayload": {
            "user": "",
            "event_id": "882",
            "message": "2023/10/10 23:06:39 GCEGuestAgent: Error watching metadata: invalid character '<' looking for beginning of value\r\n",
            "time_written": "2023-10-10 23:06:39 +0100",
            "time_generated": "2023-10-10 23:06:39 +0100",
            "event_type": "error",
            "string_inserts": [
                "2023/10/10 23:06:39 GCEGuestAgent: Error watching metadata: invalid character '<' looking for beginning of value"
            ],
            "channel": "application",
            "source_name": "GCEGuestAgent",
            "record_number": "2884381",
            "computer_name": "blaise-gusty-data-entry-1",
            "description": "2023/10/10 23:06:39 GCEGuestAgent: Error watching metadata: invalid character '<' looking for beginning of value\r\n",
            "event_category": "0",
        },
        "resource": {
            "type": "gce_instance",
            "labels": {
                "project_id": "ons-blaise-v2-prod",
                "instance_id": "458491889528639951",
                "zone": "europe-west2-a",
            },
        },
        "timestamp": "2023-10-10T22:06:39Z",
        "severity": "ERROR",
        "labels": {"compute.googleapis.com/resource_name": "blaise-gusty-data-entry-1"},
        "logName": "projects/ons-blaise-v2-prod/logs/winevt.raw",
        "receiveTimestamp": "2023-10-10T22:06:45.651910670Z",
    }
    event = create_event(example_log_entry)

    # act
    with caplog.at_level(logging.INFO):
        response = run_slack_alerter(event)

    # assert
    assert response == "Alert skipped"
    assert number_of_http_calls() == 0
    assert (
        "root",
        logging.INFO,
        "Skipping watching metadata invalid character alert",
    ) in caplog.record_tuples


def test_skip_watching_ip_space_exhausted_error(
    run_slack_alerter, number_of_http_calls, caplog
):
    # arrange
    example_log_entry = {
        "protoPayload": {
            "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
            "status": {
                "code": 8,
                "message": "IP_SPACE_EXHAUSTED",
                "details": [
                    {
                        "@type": "type.googleapis.com/google.protobuf.Struct",
                        "value": {
                            "ipSpaceExhausted": {
                                "networkOrSubnetworkResource": {
                                    "resourceType": "SUBNETWORK",
                                    "resourceName": "aet-europewest2-vpcconnect-sbnt",
                                    "project": {"canonicalProjectId": "628324858917"},
                                    "scope": {
                                        "scopeType": "REGION",
                                        "scopeName": "europe-west2",
                                    },
                                }
                            }
                        },
                    }
                ],
            },
            "authenticationInfo": {
                "principalEmail": "628324858917@cloudservices.gserviceaccount.com"
            },
            "requestMetadata": {
                "callerSuppliedUserAgent": "GCE Managed Instance Group for Tesseract"
            },
            "serviceName": "compute.googleapis.com",
            "methodName": "v1.compute.instances.insert",
            "resourceName": "projects/628324858917/zones/europe-west2-b/instances/aet-europewest2-vpcconnect-2t8s",
            "request": {"@type": "type.googleapis.com/compute.instances.insert"},
        },
        "insertId": "-mqmnq7c67w",
        "resource": {
            "type": "gce_instance",
            "labels": {
                "zone": "europe-west2-b",
                "instance_id": "8585884535477906154",
                "project_id": "ons-blaise-v2-prod",
            },
        },
        "timestamp": "2023-09-14T23:15:40.216920Z",
        "severity": "ERROR",
        "logName": "projects/ons-blaise-v2-prod/logs/cloudaudit.googleapis.com%2Factivity",
        "operation": {
            "id": "operation-1694733317846-60559d9663528-e8055062-e3b64477",
            "producer": "compute.googleapis.com",
            "last": True,
        },
        "receiveTimestamp": "2023-09-14T23:15:41.197750677Z",
    }
    event = create_event(example_log_entry)

    # act
    with caplog.at_level(logging.INFO):
        response = run_slack_alerter(event)

    # assert
    assert response == "Alert skipped"
    assert number_of_http_calls() == 0
    assert (
        "root",
        logging.INFO,
        "Skipping ip space exhausted alert",
    ) in caplog.record_tuples


def test_skip_sandbox_alerts_skips_alerts_for_sandboxes(
    run_slack_alerter, number_of_http_calls, caplog
):
    # arrange
    example_log_entry = {
        "insertId": "65675a1e000906c02cfcdb54",
        "jsonPayload": {
            "logName": "projects/ons-blaise-v2-dev-jw09/logs/%40google-cloud%2Fprofiler",
            "message": "Successfully collected profile HEAP.",
            "resource": {
                "type": "gae_app",
                "labels": {
                    "version_id": "20231129t144628",
                    "module_id": "dqs-ui",
                    "zone": "europe-west2-1",
                },
            },
            "timestamp": "2023-11-29T15:34:54.591Z",
        },
        "resource": {
            "type": "gae_app",
            "labels": {
                "module_id": "dqs-ui",
                "zone": "europe-west2-1",
                "project_id": "ons-blaise-v2-dev-jw09",
                "version_id": "20231129t144628",
            },
        },
        "timestamp": "2023-11-29T15:34:54.591552Z",
        "severity": "DEBUG",
        "labels": {
            "clone_id": "0087599d4250c01bc120294e520c07b780b217e53173b5358cac87748d40d22082f17f1f7fa68823b4a41fe1f57308d3702a9095b6b347e32e672d8952a88afb65"
        },
        "logName": "projects/ons-blaise-v2-dev-jw09/logs/stdout",
        "receiveTimestamp": "2023-11-29T15:34:54.921342975Z",
    }
    event = create_event(example_log_entry)

    # act
    with caplog.at_level(logging.INFO):
        response = run_slack_alerter(event)

    # assert
    assert response == "Alert skipped"
    assert number_of_http_calls() == 0
    assert ("root", logging.INFO, "Skipping sandbox alert") in caplog.record_tuples


def test_skip_sandbox_alerts_does_not_skip_alerts_for_formal_environments(
    run_slack_alerter, number_of_http_calls, caplog
):
    # arrange
    example_log_entry = {
        "insertId": "65675a1e000906c02cfcdb54",
        "jsonPayload": {
            "logName": "projects/ons-blaise-v2-prod/logs/%40google-cloud%2Fprofiler",
            "message": "Successfully collected profile HEAP.",
            "resource": {
                "type": "gae_app",
                "labels": {
                    "version_id": "20231129t144628",
                    "module_id": "dqs-ui",
                    "zone": "europe-west2-1",
                },
            },
            "timestamp": "2023-11-29T15:34:54.591Z",
        },
        "resource": {
            "type": "gae_app",
            "labels": {
                "module_id": "dqs-ui",
                "zone": "europe-west2-1",
                "project_id": "ons-blaise-v2-prod",
                "version_id": "20231129t144628",
            },
        },
        "timestamp": "2023-11-29T15:34:54.591552Z",
        "severity": "DEBUG",
        "labels": {
            "clone_id": "0087599d4250c01bc120294e520c07b780b217e53173b5358cac87748d40d22082f17f1f7fa68823b4a41fe1f57308d3702a9095b6b347e32e672d8952a88afb65"
        },
        "logName": "projects/ons-blaise-v2-prod/logs/stdout",
        "receiveTimestamp": "2023-11-29T15:34:54.921342975Z",
    }
    event = create_event(example_log_entry)

    # act
    with caplog.at_level(logging.INFO):
        response = run_slack_alerter(event)

    # assert
    assert response != "Alert skipped"
    assert number_of_http_calls() == 1
    assert ("root", logging.INFO, "Skipping sandbox alert") not in caplog.record_tuples


def test_skip_all_preprod_and_training_alerts_except_erroneous_questionnaire(
    run_slack_alerter, number_of_http_calls, caplog
):
    # arrange
    example_log_entry = {
        "protoPayload": {
            "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
            "status": {
                "code": 8,
                "message": "IP_SPACE_EXHAUSTED",
                "details": [
                    {
                        "@type": "type.googleapis.com/google.protobuf.Struct",
                        "value": {
                            "ipSpaceExhausted": {
                                "networkOrSubnetworkResource": {
                                    "resourceType": "SUBNETWORK",
                                    "resourceName": "aet-europewest2-vpcconnect-sbnt",
                                    "project": {"canonicalProjectId": "628324858917"},
                                    "scope": {
                                        "scopeType": "REGION",
                                        "scopeName": "europe-west2",
                                    },
                                }
                            }
                        },
                    }
                ],
            },
            "authenticationInfo": {
                "principalEmail": "628324858917@cloudservices.gserviceaccount.com"
            },
            "requestMetadata": {
                "callerSuppliedUserAgent": "GCE Managed Instance Group for Tesseract"
            },
            "serviceName": "compute.googleapis.com",
            "methodName": "v1.compute.instances.insert",
            "resourceName": "projects/628324858917/zones/europe-west2-b/instances/aet-europewest2-vpcconnect-2t8s",
            "request": {"@type": "type.googleapis.com/compute.instances.insert"},
        },
        "insertId": "-mqmnq7c67w",
        "resource": {
            "type": "gce_instance",
            "labels": {
                "zone": "europe-west2-b",
                "instance_id": "8585884535477906154",
                "project_id": "ons-blaise-v2-preprod",
            },
        },
        "timestamp": "2023-09-14T23:15:40.216920Z",
        "severity": "ERROR",
        "logName": "projects/ons-blaise-v2-preprod/logs/cloudaudit.googleapis.com%2Factivity",
        "operation": {
            "id": "operation-1694733317846-60559d9663528-e8055062-e3b64477",
            "producer": "compute.googleapis.com",
            "last": True,
        },
        "receiveTimestamp": "2023-09-14T23:15:41.197750677Z",
    }
    event = create_event(example_log_entry)

    # act
    with caplog.at_level(logging.INFO):
        response = run_slack_alerter(event)

    # assert
    assert response == "Alert skipped"
    assert number_of_http_calls() == 0
    assert (
        "root",
        logging.INFO,
        "Skipping preprod/training alert",
    ) in caplog.record_tuples


@pytest.mark.parametrize(
    "application_input",
    [
        "nisra-case-mover-processor",
        "bert-call-history",
        "nifi-receipt",
        "bert-deliver-mi-hub-reports-processor",
        "bert-call-history-cleanup",
        "bts-create-totalmobile-jobs-processor",
        "publishMsg",
        "daybatch-create",
    ],
)
def test_skip_all_prod_aborted_where_no_available_instance_alerts(
    run_slack_alerter, number_of_http_calls, caplog, application_input
):
    # arrange
    example_log_entry = {
        "textPayload": "The request was aborted because there was no available instance. Additional troubleshooting documentation can be found at: https://cloud.google.com/functions/docs/troubleshooting#scalability",
        "insertId": "6645c7ad000a6dbe74ce0e75",
        "httpRequest": {
            "requestMethod": "POST",
            "requestUrl": "https://9bcbb5f410a6aff0441c475c88588883-dot-k743d1e1feb222eb6p-tp.appspot.com/_ah/push-handlers/pubsub/projects/ons-blaise-v2-prod/topics/ons-blaise-v2-prod-nisra-process?pubsub_trigger=true",
            "requestSize": "1178",
            "status": 500,
            "userAgent": "CloudPubSub-Google",
            "remoteIp": "2001:db8::100",
            "latency": "0s",
            "protocol": "HTTP/1.1",
        },
        "resource": {
            "type": "cloud_run_revision",
            "labels": {
                "project_id": "ons-blaise-v2-prod",
                "region": "europe-west2",
                "service_name": application_input,
            },
        },
        "timestamp": "2024-05-16T08:45:23.261465Z",
        "severity": "ERROR",
        "labels": {"infrastructure": "error"},
        "logName": "projects/ons-blaise-v2-prod/logs/cloudfunctions.googleapis.com%2Fcloud-functions",
        "trace": "projects/ons-blaise-v2-prod/traces/5997e419d1a18af83270d7deb0b1b2f3",
        "receiveTimestamp": "2024-05-16T08:45:33.699415689Z",
        "spanId": "1777605421925520598",
    }

    event = create_event(example_log_entry)

    # act
    with caplog.at_level(logging.INFO):
        response = run_slack_alerter(event)

    # assert
    assert response == "Alert skipped"
    assert number_of_http_calls() == 0
    assert (
        "root",
        logging.INFO,
        "Skipping no instance agent alert",
    ) in caplog.record_tuples


def test_skip_invalid_login_attempt_alerts(
    run_slack_alerter, number_of_http_calls, caplog
):
    # arrange
    example_log_entry = {
        "protoPayload": {
            "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
            "status": {
                "code": 7,
                "message": 'Required "container.clusters.list" permission(s) for "projects/ons-blaise-v2-prod".',
            },
            "authenticationInfo": {"principalEmail": "ri...e@gm...m"},
            "requestMetadata": {"requestAttributes": {}, "destinationAttributes": {}},
            "serviceName": "container.googleapis.com",
            "methodName": "google.container.v1.ClusterManager.ListClusters",
            "authorizationInfo": [
                {
                    "resource": "projects/ons-blaise-v2-prod",
                    "permission": "container.clusters.list",
                    "resourceAttributes": {
                        "service": "cloudresourcemanager.googleapis.com",
                        "name": "projects/ons-blaise-v2-prod",
                        "type": "cloudresourcemanager.googleapis.com/Project",
                    },
                    "permissionType": "ADMIN_READ",
                }
            ],
            "resourceName": "projects/ons-blaise-v2-prod/zones/-",
            "request": {
                "@type": "type.googleapis.com/google.container.v1alpha1.ListClustersRequest",
                "parent": "projects/ons-blaise-v2-prod/locations/-",
            },
            "resourceLocation": {"currentLocations": ["-"]},
            "policyViolationInfo": {"orgPolicyViolationInfo": {}},
        },
        "insertId": "qx4ozlctr2",
        "resource": {
            "type": "gke_cluster",
            "labels": {
                "project_id": "ons-blaise-v2-prod",
                "cluster_name": "",
                "location": "-",
            },
        },
        "timestamp": "2024-05-02T08:55:17.007657529Z",
        "severity": "ERROR",
        "logName": "projects/ons-blaise-v2-prod/logs/cloudaudit.googleapis.com%2Fdata_access",
        "receiveTimestamp": "2024-05-02T08:55:17.757250577Z",
    }

    event = create_event(example_log_entry)

    # act
    with caplog.at_level(logging.INFO):
        response = run_slack_alerter(event)

    # assert
    assert response == "Alert skipped"
    assert number_of_http_calls() == 0
    assert (
        "root",
        logging.INFO,
        "Skipping invalid login attempt alert",
    ) in caplog.record_tuples


def test_skip_requested_entity_was_not_found_alerts(
    run_slack_alerter, number_of_http_calls, caplog
):
    # arrange
    example_log_entry = {
        "protoPayload": {
            "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
            "status": {
                "code": 5,
                "message": "generic::not_found: Requested entity was not found.",
            },
            "authenticationInfo": {
                "principalEmail": "service-628324858917@container-analysis.iam.gserviceaccount.com",
                "principalSubject": "serviceAccount:service-628324858917@container-analysis.iam.gserviceaccount.com",
            },
            "requestMetadata": {
                "callerIp": "gcp-internal-ip",
                "callerSuppliedUserAgent": "ContainerAnalysis/boq_artifact-analysis-scanlistener_20240614.04_p1 go-containerregistry,gzip(gfe)",
                "requestAttributes": {},
                "destinationAttributes": {},
            },
            "serviceName": "artifactregistry.googleapis.com",
            "methodName": "Docker-GetManifest",
            "authorizationInfo": [
                {
                    "resource": "projects/ons-blaise-v2-prod/locations/europe-west2/repositories/gcf-artifacts",
                    "permission": "artifactregistry.repositories.downloadArtifacts",
                    "granted": True,
                    "resourceAttributes": {},
                    "permissionType": "DATA_READ",
                }
            ],
            "resourceName": "projects/ons-blaise-v2-prod/locations/europe-west2/repositories/gcf-artifacts/dockerImages/publish_msg%2Fcache",
            "request": {
                "@type": "type.googleapis.com/google.logging.type.HttpRequest",
                "requestMethod": "GET",
                "requestUrl": "/v2/ons-blaise-v2-prod/gcf-artifacts/publish_msg/cache/manifests/sha256:a28cec80810f824b2e15005b1dc93877e1b9c7b7b3466d4f4b593c9c5db64868",
            },
            "resourceLocation": {
                "currentLocations": ["europe-west2"],
                "originalLocations": ["europe-west2"],
            },
        },
        "insertId": "1rtjfyxd1d41",
        "resource": {
            "type": "audited_resource",
            "labels": {
                "project_id": "ons-blaise-v2-prod",
                "method": "Docker-GetManifest",
                "service": "artifactregistry.googleapis.com",
            },
        },
        "timestamp": "2024-07-04T23:50:15.079183701Z",
        "severity": "ERROR",
        "logName": "projects/ons-blaise-v2-prod/logs/cloudaudit.googleapis.com%2Fdata_access",
        "receiveTimestamp": "2024-07-04T23:50:15.816848898Z",
    }

    event = create_event(example_log_entry)

    # act
    with caplog.at_level(logging.INFO):
        response = run_slack_alerter(event)

    # assert
    assert response == "Alert skipped"
    assert number_of_http_calls() == 0
    assert (
        "root",
        logging.INFO,
        "Skipping requested entity was not found alert",
    ) in caplog.record_tuples


def test_skip_execute_sql_alerts_error(run_slack_alerter, number_of_http_calls, caplog):
    # arrange
    example_log_entry = {
        "protoPayload": {
            "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
            "status": {
                "code": 3,
                "message": "Some of your SQL statements failed to execute (Learn more at https://cloud.google.com/sql/docs/mysql/manage-data-using-studio). Details: This API does not support reading BLOB columns.",
            },
            "authenticationInfo": {"principalEmail": "jane.blaise@example.com"},
            "requestMetadata": {
                "callerIp": "gcp-internal-ip",
                "requestAttributes": {
                    "time": "2024-08-01T10:32:44.863464Z",
                    "auth": {},
                },
                "destinationAttributes": {},
            },
            "serviceName": "cloudsql.googleapis.com",
            "methodName": "cloudsql.instances.executeSql",
            "authorizationInfo": [
                {
                    "resource": "projects/ons-blaise-v2-prod/instances/blaise-prod-5587401e",
                    "permission": "cloudsql.instances.executeSql",
                    "granted": True,
                    "resourceAttributes": {
                        "service": "sqladmin.googleapis.com",
                        "name": "projects/ons-blaise-v2-prod/instances/blaise-prod-5587401e",
                        "type": "sqladmin.googleapis.com/Instance",
                    },
                    "permissionType": "DATA_WRITE",
                }
            ],
            "resourceName": "projects/ons-blaise-v2-prod/instances/blaise-prod-5587401e",
            "request": {
                "project": "ons-blaise-v2-prod",
                "body": {"user": "blaise", "database": "blaise"},
                "instance": "blaise-prod-5587401e",
                "@type": "type.googleapis.com/google.cloud.sql.v1beta4.SqlInstancesExecuteSqlRequest",
            },
        },
        "insertId": "e6g2mre8ysqr",
        "resource": {
            "type": "cloudsql_database",
            "labels": {
                "project_id": "ons-blaise-v2-prod",
                "database_id": "ons-blaise-v2-prod:blaise-prod-5587401e",
                "region": "europe-west2",
            },
        },
        "timestamp": "2024-08-01T10:32:44.372162Z",
        "severity": "ERROR",
        "logName": "projects/ons-blaise-v2-prod/logs/cloudaudit.googleapis.com%2Fdata_access",
        "receiveTimestamp": "2024-08-01T10:32:45.035865832Z",
    }

    event = create_event(example_log_entry)

    # act
    with caplog.at_level(logging.INFO):
        response = run_slack_alerter(event)

    # assert
    assert response == "Alert skipped"
    assert number_of_http_calls() == 0
    assert (
        "root",
        logging.INFO,
        "Skipping execute sql alert",
    ) in caplog.record_tuples


def test_skip_paramiko_alerts_error(run_slack_alerter, number_of_http_calls, caplog):
    # arrange
    example_log_entry = {
        "textPayload": 'Traceback (most recent call last):\n  File "/layers/google.python.pip/pip/lib/python3.9/site-packages/paramiko/sftp_file.py", line 76, in __del__\n    self._close(async_=True)\n  File "/layers/google.python.pip/pip/lib/python3.9/site-packages/paramiko/sftp_file.py", line 97, in _close\n    BufferedFile.close(self)\n  File "/layers/google.python.pip/pip/lib/python3.9/site-packages/paramiko/file.py", line 85, in close\n    self.flush()\n  File "/layers/google.python.pip/pip/lib/python3.9/site-packages/paramiko/file.py", line 93, in flush\n    self._write_all(self._wbuffer.getvalue())\nValueError: I/O operation on closed file.',
        "insertId": "66f1ab17000e1ad26f7ffcbe",
        "resource": {
            "type": "cloud_run_revision",
            "labels": {
                "location": "europe-west2",
                "service_name": "nisra-case-mover-processor",
                "project_id": "ons-blaise-v2-prod",
                "configuration_name": "nisra-case-mover-processor",
                "revision_name": "nisra-case-mover-processor-00012-sew",
            },
        },
        "timestamp": "2024-09-23T17:53:27.924370Z",
        "severity": "ERROR",
        "labels": {
            "goog-managed-by": "cloudfunctions",
            "instanceId": "007989f2a1c448ded395a411cba085e03c4c09a74e9ee072633331ebe6126caee9691b90d1dc5f22fa5e473acab476a9bc0e3e1eb33eb8244d17d2d8ec4ad67f91d55627",
        },
        "logName": "projects/ons-blaise-v2-prod/logs/run.googleapis.com%2Fstderr",
        "receiveTimestamp": "2024-09-23T17:53:28.255311165Z",
        "errorGroups": [{"id": "CKakz9W_soaPWw"}],
    }

    event = create_event(example_log_entry)

    # act
    with caplog.at_level(logging.INFO):
        response = run_slack_alerter(event)

    # assert
    assert response == "Alert skipped"
    assert number_of_http_calls() == 0
    assert (
        "root",
        logging.INFO,
        "Skipping paramiko error alert",
    ) in caplog.record_tuples


def test_skip_bootstrapper_alerts(run_slack_alerter, number_of_http_calls, caplog):
    # arrange
    example_log_entry = {
        "insertId": "g4ydtwlpwtc5vggzg",
        "jsonPayload": {
            "channel": "application",
            "message": "2024/09/20 01:31:12 GCEGuestAgent: Failed to schedule job MTLS_MDS_Credential_Boostrapper with error: ShouldEnable() returned false, cannot schedule job MTLS_MDS_Credential_Boostrapper\r\n",
            "event_id": "882",
            "user": "",
            "description": "2024/09/20 01:31:12 GCEGuestAgent: Failed to schedule job MTLS_MDS_Credential_Boostrapper with error: ShouldEnable() returned false, cannot schedule job MTLS_MDS_Credential_Boostrapper\r\n",
            "time_written": "2024-09-20 01:31:12 +0100",
            "time_generated": "2024-09-20 01:31:12 +0100",
            "string_inserts": [
                "2024/09/20 01:31:12 GCEGuestAgent: Failed to schedule job MTLS_MDS_Credential_Boostrapper with error: ShouldEnable() returned false, cannot schedule job MTLS_MDS_Credential_Boostrapper"
            ],
            "event_type": "error",
            "record_number": "352403810",
            "computer_name": "restapi-4",
            "source_name": "GCEGuestAgent",
            "event_category": "0",
        },
        "resource": {
            "type": "gce_instance",
            "labels": {
                "zone": "europe-west2-a",
                "project_id": "ons-blaise-v2-prod",
                "instance_id": "6542796480007992547",
            },
        },
        "timestamp": "2024-09-20T00:31:12Z",
        "severity": "ERROR",
        "labels": {"compute.googleapis.com/resource_name": "restapi-4"},
        "logName": "projects/ons-blaise-v2-prod/logs/winevt.raw",
        "receiveTimestamp": "2024-09-20T00:33:40.603402854Z",
    }

    event = create_event(example_log_entry)

    # act
    with caplog.at_level(logging.INFO):
        response = run_slack_alerter(event)

    # assert
    assert response == "Alert skipped"
    assert number_of_http_calls() == 0
    assert (
        "root",
        logging.INFO,
        "Skipping bootstrapper alert",
    ) in caplog.record_tuples


def test_skip_generic_not_found_alerts_latest(
    run_slack_alerter, number_of_http_calls, caplog
):
    # arrange
    example_log_entry = {
        "protoPayload": {
            "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
            "status": {
                "code": 5,
                "message": 'generic::not_found: Failed to fetch "latest"',
            },
            "authenticationInfo": {
                "principalEmail": "628324858917@cloudbuild.gserviceaccount.com",
                "serviceAccountDelegationInfo": [
                    {
                        "firstPartyPrincipal": {
                            "principalEmail": "cloud-build-argo-foreman@prod.google.com"
                        }
                    }
                ],
                "principalSubject": "serviceAccount:628324858917@cloudbuild.gserviceaccount.com",
            },
            "requestMetadata": {
                "callerIp": "203.0.113.2",
                "callerSuppliedUserAgent": "go-containerregistry,gzip(gfe)",
                "requestAttributes": {},
                "destinationAttributes": {},
            },
            "serviceName": "artifactregistry.googleapis.com",
            "methodName": "Docker-HeadManifest",
            "authorizationInfo": [
                {
                    "resource": "projects/ons-blaise-v2-prod/locations/europe-west2/repositories/gcf-artifacts",
                    "permission": "artifactregistry.repositories.downloadArtifacts",
                    "granted": True,
                    "resourceAttributes": {},
                    "permissionType": "DATA_READ",
                }
            ],
            "resourceName": "projects/ons-blaise-v2-prod/locations/europe-west2/repositories/gcf-artifacts/dockerImages/ons--blaise--v2--prod__europe--west2__nifi--receipt%2Fcache",
            "request": {
                "@type": "type.googleapis.com/google.logging.type.HttpRequest",
                "requestUrl": "/v2/ons-blaise-v2-prod/gcf-artifacts/ons--blaise--v2--prod__europe--west2__nifi--receipt/cache/manifests/latest",
                "requestMethod": "HEAD",
            },
            "resourceLocation": {
                "currentLocations": ["europe-west2"],
                "originalLocations": ["europe-west2"],
            },
        },
        "insertId": "1h15w4udgp0q",
        "resource": {
            "type": "audited_resource",
            "labels": {
                "project_id": "ons-blaise-v2-prod",
                "service": "artifactregistry.googleapis.com",
                "method": "Docker-HeadManifest",
            },
        },
        "timestamp": "2024-12-02T12:01:35.011476126Z",
        "severity": "ERROR",
        "logName": "projects/ons-blaise-v2-prod/logs/cloudaudit.googleapis.com%2Fdata_access",
        "receiveTimestamp": "2024-12-02T12:01:35.148295977Z",
    }

    event = create_event(example_log_entry)

    # act
    with caplog.at_level(logging.INFO):
        response = run_slack_alerter(event)

    # assert
    assert response == "Alert skipped"
    assert number_of_http_calls() == 0
    assert (
        "root",
        logging.INFO,
        "Skipping generic not found alert",
    ) in caplog.record_tuples


def test_skip_generic_not_found_alerts_version(
    run_slack_alerter, number_of_http_calls, caplog
):
    # arrange
    example_log_entry = {
        "protoPayload": {
            "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
            "status": {
                "code": 5,
                "message": 'generic::not_found: Failed to fetch "version_1"',
            },
            "authenticationInfo": {
                "principalEmail": "628324858917@cloudbuild.gserviceaccount.com",
                "serviceAccountDelegationInfo": [
                    {
                        "firstPartyPrincipal": {
                            "principalEmail": "cloud-build-argo-foreman@prod.google.com"
                        }
                    }
                ],
                "principalSubject": "serviceAccount:628324858917@cloudbuild.gserviceaccount.com",
            },
            "requestMetadata": {
                "callerIp": "203.0.113.3",
                "callerSuppliedUserAgent": "go-containerregistry/v0.19.1,gzip(gfe)",
                "requestAttributes": {},
                "destinationAttributes": {},
            },
            "serviceName": "artifactregistry.googleapis.com",
            "methodName": "Docker-HeadManifest",
            "authorizationInfo": [
                {
                    "resource": "projects/ons-blaise-v2-prod/locations/europe-west2/repositories/gcf-artifacts",
                    "permission": "artifactregistry.repositories.downloadArtifacts",
                    "granted": True,
                    "resourceAttributes": {},
                    "permissionType": "DATA_READ",
                }
            ],
            "resourceName": "projects/ons-blaise-v2-prod/locations/europe-west2/repositories/gcf-artifacts/dockerImages/ons--blaise--v2--prod__europe--west2__nifi--receipt",
            "request": {
                "requestMethod": "HEAD",
                "@type": "type.googleapis.com/google.logging.type.HttpRequest",
                "requestUrl": "/v2/ons-blaise-v2-prod/gcf-artifacts/ons--blaise--v2--prod__europe--west2__nifi--receipt/manifests/version_1",
            },
            "resourceLocation": {
                "currentLocations": ["europe-west2"],
                "originalLocations": ["europe-west2"],
            },
        },
        "insertId": "1snjiu3dbkh4",
        "resource": {
            "type": "audited_resource",
            "labels": {
                "method": "Docker-HeadManifest",
                "service": "artifactregistry.googleapis.com",
                "project_id": "ons-blaise-v2-prod",
            },
        },
        "timestamp": "2024-12-02T12:01:36.494768789Z",
        "severity": "ERROR",
        "logName": "projects/ons-blaise-v2-prod/logs/cloudaudit.googleapis.com%2Fdata_access",
        "receiveTimestamp": "2024-12-02T12:01:36.786461532Z",
    }

    event = create_event(example_log_entry)

    # act
    with caplog.at_level(logging.INFO):
        response = run_slack_alerter(event)

    # assert
    assert response == "Alert skipped"
    assert number_of_http_calls() == 0
    assert (
        "root",
        logging.INFO,
        "Skipping generic not found alert",
    ) in caplog.record_tuples


def test_skip_generic_not_found_alerts_with_uuid(
    run_slack_alerter, number_of_http_calls, caplog
):
    # arrange
    example_log_entry = {
        "protoPayload": {
            "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
            "status": {
                "code": 5,
                "message": 'generic::not_found: Failed to fetch "79cce210-187e-4c0c-8b38-4efe12e4c88e"',
            },
            "authenticationInfo": {
                "principalEmail": "628324858917@cloudbuild.gserviceaccount.com",
                "serviceAccountDelegationInfo": [
                    {
                        "firstPartyPrincipal": {
                            "principalEmail": "cloud-build-argo-foreman@prod.google.com"
                        }
                    }
                ],
                "principalSubject": "serviceAccount:628324858917@cloudbuild.gserviceaccount.com",
            },
            "requestMetadata": {
                "callerIp": "203.0.113.4",
                "callerSuppliedUserAgent": "go-containerregistry/v0.19.1,gzip(gfe)",
                "requestAttributes": {},
                "destinationAttributes": {},
            },
            "serviceName": "artifactregistry.googleapis.com",
            "methodName": "Docker-HeadManifest",
            "authorizationInfo": [
                {
                    "resource": "projects/ons-blaise-v2-prod/locations/europe/repositories/eu.gcr.io",
                    "permission": "artifactregistry.repositories.downloadArtifacts",
                    "granted": "true",
                    "resourceAttributes": {},
                    "permissionType": "DATA_READ",
                }
            ],
            "resourceName": "projects/ons-blaise-v2-prod/locations/europe/repositories/eu.gcr.io/dockerImages/app-engine-tmp%2Fapp%2Fdashboard-ui%2Fttl-18h",
            "request": {
                "requestMethod": "HEAD",
                "@type": "type.googleapis.com/google.logging.type.HttpRequest",
                "requestUrl": "/v2/ons-blaise-v2-prod/eu.gcr.io/app-engine-tmp/app/dashboard-ui/ttl-18h/manifests/79cce210-187e-4c0c-8b38-4efe12e4c88e",
            },
            "resourceLocation": {
                "currentLocations": ["europe"],
                "originalLocations": ["europe"],
            },
        },
        "insertId": "46xft1d29ve",
        "resource": {
            "type": "audited_resource",
            "labels": {
                "method": "Docker-HeadManifest",
                "project_id": "ons-blaise-v2-prod",
                "service": "artifactregistry.googleapis.com",
            },
        },
        "timestamp": "2024-12-11T16:35:06.591915301Z",
        "severity": "ERROR",
        "logName": "projects/ons-blaise-v2-prod/logs/cloudaudit.googleapis.com%2Fdata_access",
        "receiveTimestamp": "2024-12-11T16:35:07.046014612Z",
    }

    event = create_event(example_log_entry)

    # act
    with caplog.at_level(logging.INFO):
        response = run_slack_alerter(event)

    # assert
    assert response == "Alert skipped"
    assert number_of_http_calls() == 0
    assert (
        "root",
        logging.INFO,
        "Skipping generic not found alert",
    ) in caplog.record_tuples


def test_skip_socket_exception_alerts(run_slack_alerter, number_of_http_calls, caplog):
    # arrange
    example_log_entry = {
        "textPayload": "Socket exception: Connection reset by peer (104)",
        "insertId": "67043d0900053abd778cf0bc",
        "httpRequest": {},
        "resource": {
            "type": "cloud_run_revision",
            "labels": {
                "project_id": "ons-blaise-v2-prod",
                "configuration_name": "nisra-case-mover-processor",
                "service_name": "nisra-case-mover-processor",
                "location": "europe-west2",
                "revision_name": "nisra-case-mover-processor-00017-jeg",
            },
        },
        "timestamp": "2024-10-07T19:56:57.342717Z",
        "severity": "ERROR",
        "labels": {
            "goog-managed-by": "cloudfunctions",
            "instanceId": "007989f2a133de4fee2c331909aca0d04d3c03445e79e08dcfd070aaaa797bf94922ed1cc41c359b986e4653c00bf33ce25ac252d7d382b8d656f0d25242a09d9ef85f1b",
            "python_logger": "paramiko.transport",
        },
        "logName": "projects/ons-blaise-v2-prod/logs/run.googleapis.com%2Fstderr",
        "sourceLocation": {
            "file": "/layers/google.python.pip/pip/lib/python3.9/site-packages/paramiko/transport.py",
            "line": "1909",
            "function": "_log",
        },
        "receiveTimestamp": "2024-10-07T19:56:57.346635669Z",
    }
    event = create_event(example_log_entry)

    # act
    with caplog.at_level(logging.INFO):
        response = run_slack_alerter(event)

    # assert
    assert response == "Alert skipped"
    assert number_of_http_calls() == 0
    assert (
        "root",
        logging.INFO,
        "Skipping socket exception alert",
    ) in caplog.record_tuples


def test_skip_scc_dormant_accounts_prod_alert_service_account_keys_error(
    run_slack_alerter, number_of_http_calls, caplog
):
    # arrange
    example_log_entry = {
        "protoPayload": {
            "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
            "status": {
                "code": "5",
                "message": "Service account key f7ade4740059a1f5137bea2ff20b0952f012cf17 does not exist.",
            },
            "authenticationInfo": {
                "principalEmail": "scc-dormant-accounts-alert@ons-gcp-monitoring-prod.iam.gserviceaccount.com",
                "serviceAccountDelegationInfo": [
                    {
                        "firstPartyPrincipal": {
                            "principalEmail": "service-719628633551@serverless-robot-prod.iam.gserviceaccount.com"
                        }
                    }
                ],
                "principalSubject": "serviceAccount:scc-dormant-accounts-alert@ons-gcp-monitoring-prod.iam.gserviceaccount.com",
            },
            "requestMetadata": {
                "callerIp": "203.0.113.5",
                "callerSuppliedUserAgent": "grpc-python/1.70.0 grpc-c/45.0.0 (linux; chttp2),gzip(gfe)",
                "requestAttributes": {
                    "time": "2025-02-17T01:28:44.251600949Z",
                    "auth": {},
                },
                "destinationAttributes": {},
            },
            "serviceName": "iam.googleapis.com",
            "methodName": "google.iam.admin.v1.GetServiceAccountKey",
            "authorizationInfo": [
                {
                    "resource": "projects/-/serviceAccounts/110247389061820088971",
                    "permission": "iam.serviceAccountKeys.get",
                    "granted": "true",
                    "resourceAttributes": {
                        "name": "projects/-/serviceAccounts/110247389061820088971"
                    },
                    "permissionType": "ADMIN_READ",
                }
            ],
            "resourceName": "projects/-/serviceAccounts/110247389061820088971/keys/f7ade4740059a1f5137bea2ff20b0952f012cf17",
            "request": {
                "name": "projects/ons-blaise-v2-prod/serviceAccounts/628324858917-compute@developer.gserviceaccount.com/keys/f7ade4740059a1f5137bea2ff20b0952f012cf17",
                "@type": "type.googleapis.com/google.iam.admin.v1.GetServiceAccountKeyRequest",
            },
        },
        "insertId": "10cyfzcf1hve2j",
        "resource": {
            "type": "service_account",
            "labels": {
                "email_id": "628324858917-compute@developer.gserviceaccount.com",
                "project_id": "ons-blaise-v2-prod",
                "unique_id": "110247389061820088971",
            },
        },
        "timestamp": "2025-02-17T01:28:44.233811231Z",
        "severity": "ERROR",
        "logName": "projects/ons-blaise-v2-prod/logs/cloudaudit.googleapis.com%2Fdata_access",
        "receiveTimestamp": "2025-02-17T01:28:45.898607418Z",
    }
    event = create_event(example_log_entry)

    # act
    with caplog.at_level(logging.INFO):
        response = run_slack_alerter(event)

    # assert
    assert response == "Alert skipped"
    assert number_of_http_calls() == 0
    assert (
        "root",
        logging.INFO,
        "Skipping external 'SCC Dormant Accounts Alert' service account alert",
    ) in caplog.record_tuples


def test_skip_scc_dormant_accounts_prod_alert_service_account_not_found_error(
    run_slack_alerter, number_of_http_calls, caplog
):
    # arrange
    example_log_entry = {
        "protoPayload": {
            "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
            "status": {
                "code": 5,
                "message": "Service account projects/ons-blaise-v2-prod/serviceAccounts/blaise-cloud-functions@ons-blaise-v2-prod.iam.gserviceaccount.com does not exist.",
            },
            "authenticationInfo": {
                "principalEmail": "scc-dormant-accounts-alert@ons-gcp-monitoring-prod.iam.gserviceaccount.com",
                "serviceAccountDelegationInfo": [
                    {
                        "firstPartyPrincipal": {
                            "principalEmail": "service-719628633551@serverless-robot-prod.iam.gserviceaccount.com"
                        }
                    }
                ],
                "principalSubject": "serviceAccount:scc-dormant-accounts-alert@ons-gcp-monitoring-prod.iam.gserviceaccount.com",
            },
            "requestMetadata": {
                "callerIp": "203.0.113.6",
                "callerSuppliedUserAgent": "grpc-python/1.71.0 grpc-c/46.0.0 (linux; chttp2),gzip(gfe)",
                "requestAttributes": {
                    "time": "2025-03-14T01:27:24.596234977Z",
                    "auth": {},
                },
                "destinationAttributes": {},
            },
            "serviceName": "iam.googleapis.com",
            "methodName": "google.iam.admin.v1.GetServiceAccount",
            "authorizationInfo": [
                {
                    "resource": "projects/ons-blaise-v2-prod",
                    "permission": "iam.serviceAccounts.list",
                    "granted": "true",
                    "resourceAttributes": {},
                    "permissionType": "ADMIN_READ",
                }
            ],
            "resourceName": "projects/-/serviceAccounts/105250506097979753968",
            "request": {
                "@type": "type.googleapis.com/google.iam.admin.v1.GetServiceAccountRequest",
                "name": "projects/ons-blaise-v2-prod/serviceAccounts/blaise-cloud-functions@ons-blaise-v2-prod.iam.gserviceaccount.com",
            },
        },
        "insertId": "voy2d9edl9sk",
        "resource": {
            "type": "service_account",
            "labels": {
                "unique_id": "",
                "email_id": "",
                "project_id": "ons-blaise-v2-prod",
            },
        },
        "timestamp": "2025-03-14T01:27:24.512834663Z",
        "severity": "ERROR",
        "logName": "projects/ons-blaise-v2-prod/logs/cloudaudit.googleapis.com%2Fdata_access",
        "receiveTimestamp": "2025-03-14T01:27:24.891395117Z",
    }
    event = create_event(example_log_entry)

    # act
    with caplog.at_level(logging.INFO):
        response = run_slack_alerter(event)

    # assert
    assert response == "Alert skipped"
    assert number_of_http_calls() == 0
    assert (
        "root",
        logging.INFO,
        "Skipping external 'SCC Dormant Accounts Alert' service account alert",
    ) in caplog.record_tuples


def test_skip_permission_denied_by_iam(run_slack_alerter, number_of_http_calls, caplog):
    # arrange
    example_log_entry = {
        "protoPayload": {
            "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
            "status": {"code": 2, "message": "permission denied by IAM"},
            "authenticationInfo": {},
            "requestMetadata": {
                "callerIp": "203.0.113.7",
                "callerSuppliedUserAgent": "Fuzz Faster U Fool v2.1.0,gzip(gfe)",
            },
            "serviceName": "artifactregistry.googleapis.com",
            "methodName": "Docker-GetTags",
            "authorizationInfo": [
                {
                    "resource": "projects/ons-blaise-v2-prod/locations/europe/repositories/eu.gcr.io",
                    "permission": "artifactregistry.repositories.downloadArtifacts",
                    "granted": False,
                    "resourceAttributes": {},
                    "permissionType": "DATA_READ",
                }
            ],
            "resourceName": "projects/ons-blaise-v2-prod/locations/europe/repositories/eu.gcr.io",
            "request": {
                "requestMethod": "GET",
                "requestUrl": "/v2/ons-blaise-v2-prod/eu.gcr.io/tags/list",
                "@type": "type.googleapis.com/google.logging.type.HttpRequest",
            },
            "resourceLocation": {
                "currentLocations": ["europe"],
                "originalLocations": ["europe"],
            },
        },
        "insertId": "1q7acrxd7195",
        "resource": {
            "type": "audited_resource",
            "labels": {
                "method": "Docker-GetTags",
                "service": "artifactregistry.googleapis.com",
                "project_id": "ons-blaise-v2-prod",
            },
        },
        "timestamp": "2025-03-03T05:07:51.689323290Z",
        "severity": "ERROR",
        "logName": "projects/ons-blaise-v2-prod/logs/cloudaudit.googleapis.com%2Fdata_access",
        "receiveTimestamp": "2025-03-03T05:07:51.704386101Z",
    }
    event = create_event(example_log_entry)

    # act
    with caplog.at_level(logging.INFO):
        response = run_slack_alerter(event)

    # assert
    assert response == "Alert skipped"
    assert number_of_http_calls() == 0
    assert (
        "root",
        logging.INFO,
        "Skipping permission denied by IAM alert",
    ) in caplog.record_tuples


def test_skip_org_policy_constraint_physicalZoneSeparation_not_found_alerts(
    run_slack_alerter, number_of_http_calls, caplog
):
    # arrange
    example_log_entry = {
        "protoPayload": {
            "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
            "status": {
                "code": 5,
                "message": "com.google.apps.framework.request.StatusException: <eye3 title='NOT_FOUND'/> generic::NOT_FOUND: No constraint found with name 'constraints/gcp.requiresPhysicalZoneSeparation'.",
            },
            "authenticationInfo": {"principalEmail": "test.user1@example.com"},
            "requestMetadata": {
                "callerIp": "2001:db8::1",
                "callerSuppliedUserAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 OPR/119.0.0.0,gzip(gfe),gzip(gfe)",
                "requestAttributes": {
                    "time": "2025-07-11T08:21:33.991820655Z",
                    "auth": {},
                },
                "destinationAttributes": {},
            },
            "serviceName": "orgpolicy.googleapis.com",
            "methodName": "google.cloud.orgpolicy.v2.OrgPolicy.GetEffectivePolicy",
            "authorizationInfo": [
                {
                    "resource": "projects/ons-blaise-v2-prod/policies/gcp.requiresPhysicalZoneSeparation",
                    "permission": "orgpolicy.policy.get",
                    "granted": True,
                    "resourceAttributes": {},
                    "permissionType": "ADMIN_READ",
                }
            ],
            "resourceName": "projects/ons-blaise-v2-prod/policies/gcp.requiresPhysicalZoneSeparation",
            "request": {
                "@type": "type.googleapis.com/google.cloud.orgpolicy.v2.GetEffectivePolicyRequest",
                "name": "projects/ons-blaise-v2-prod/policies/gcp.requiresPhysicalZoneSeparation",
            },
        },
        "insertId": "14u34yud232p",
        "resource": {
            "type": "audited_resource",
            "labels": {
                "method": "google.cloud.orgpolicy.v2.OrgPolicy.GetEffectivePolicy",
                "service": "orgpolicy.googleapis.com",
                "project_id": "ons-blaise-v2-prod",
            },
        },
        "timestamp": "2025-07-11T08:21:33.984397510Z",
        "severity": "ERROR",
        "logName": "projects/ons-blaise-v2-prod/logs/cloudaudit.googleapis.com%2Fdata_access",
        "receiveTimestamp": "2025-07-11T08:21:34.086169195Z",
    }
    event = create_event(example_log_entry)

    # act
    with caplog.at_level(logging.INFO):
        response = run_slack_alerter(event)

    # assert
    assert response == "Alert skipped"
    assert number_of_http_calls() == 0
    assert (
        "root",
        logging.INFO,
        "Skipping 'org policy constraint not found: constraints/gcp.requiresPhysicalZoneSeparation' alert",
    ) in caplog.record_tuples


def test_skip_org_policy_constraint_disableServiceAccountHmacKeyCreation_not_found_alerts(
    run_slack_alerter, number_of_http_calls, caplog
):
    # arrange
    example_log_entry = {
        "protoPayload": {
            "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
            "status": {
                "code": 5,
                "message": "com.google.apps.framework.request.StatusException: <eye3 title='NOT_FOUND'/> generic::NOT_FOUND: No constraint found with name 'constraints/storage.disableServiceAccountHmacKeyCreation'.",
            },
            "authenticationInfo": {"principalEmail": "test.user2@example.com"},
            "requestMetadata": {
                "callerIp": "2001:db8::2",
                "callerSuppliedUserAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36,gzip(gfe)",
                "requestAttributes": {
                    "time": "2025-07-14T10:15:22.123456789Z",
                    "auth": {},
                },
                "destinationAttributes": {},
            },
            "serviceName": "orgpolicy.googleapis.com",
            "methodName": "google.cloud.orgpolicy.v2.OrgPolicy.GetEffectivePolicy",
            "authorizationInfo": [
                {
                    "resource": "projects/ons-blaise-v2-prod/policies/storage.disableServiceAccountHmacKeyCreation",
                    "permission": "orgpolicy.policy.get",
                    "granted": True,
                    "resourceAttributes": {},
                    "permissionType": "ADMIN_READ",
                }
            ],
            "resourceName": "projects/ons-blaise-v2-prod/policies/storage.disableServiceAccountHmacKeyCreation",
            "request": {
                "@type": "type.googleapis.com/google.cloud.orgpolicy.v2.GetEffectivePolicyRequest",
                "name": "projects/ons-blaise-v2-prod/policies/storage.disableServiceAccountHmacKeyCreation",
            },
        },
        "insertId": "28x45zud987q",
        "resource": {
            "type": "audited_resource",
            "labels": {
                "method": "google.cloud.orgpolicy.v2.OrgPolicy.GetEffectivePolicy",
                "service": "orgpolicy.googleapis.com",
                "project_id": "ons-blaise-v2-prod",
            },
        },
        "timestamp": "2025-07-14T10:15:22.098765432Z",
        "severity": "ERROR",
        "logName": "projects/ons-blaise-v2-prod/logs/cloudaudit.googleapis.com%2Fdata_access",
        "receiveTimestamp": "2025-07-14T10:15:22.234567890Z",
    }
    event = create_event(example_log_entry)

    # act
    with caplog.at_level(logging.INFO):
        response = run_slack_alerter(event)

    # assert
    assert response == "Alert skipped"
    assert number_of_http_calls() == 0
    assert (
        "root",
        logging.INFO,
        "Skipping 'org policy constraint not found: constraints/storage.disableServiceAccountHmacKeyCreation' alert",
    ) in caplog.record_tuples
