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


def test_send_cloud_function_slack_alert(run_slack_alerter, get_webhook_payload):
    cloud_function_log_entry = {
        "receiveTimestamp": "2022-07-22T20:36:22.219592062Z",
        "resource": {
            "labels": {
                "function_name": "log-error",
            },
            "type": "cloud_function",
        },
        "severity": "ERROR",
        "textPayload": "Example error message",
    }
    event = create_event(cloud_function_log_entry)

    response = run_slack_alerter(event)

    assert response == "Alert sent"
    expected_log_query_link = create_log_query_link(
        {
            "resource.type": "cloud_function",
            "resource.labels.function_name": "log-error",
        },
        ["WARNING", "ERROR", "CRITICAL", "ALERT", "EMERGENCY", "DEBUG"],
        parse("2022-07-22T20:36:22.219592Z"),
        "project-dev",
    )

    assert get_webhook_payload() == convert_slack_message_to_blocks(
        SlackMessage(
            title=":alert: ERROR: Example error message",
            fields={
                "Platform": "cloud_function",
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


def test_send_cloud_function_timeout_slack_alert(
    run_slack_alerter, get_webhook_payload
):
    cloud_function_log_entry = {
        "receiveTimestamp": "2022-12-15T04:09:02.428095884Z",
        "resource": {
            "labels": {
                "function_name": "log-error",
            },
            "type": "cloud_function",
        },
        "severity": "DEBUG",
        "textPayload": "Function execution took 540141 ms. Finished with status: timeout",
    }
    event = create_event(cloud_function_log_entry)

    response = run_slack_alerter(event)

    assert response == "Alert sent"
    expected_log_query_link = create_log_query_link(
        {
            "resource.type": "cloud_function",
            "resource.labels.function_name": "log-error",
        },
        ["WARNING", "ERROR", "CRITICAL", "ALERT", "EMERGENCY", "DEBUG"],
        parse("2022-12-15T04:09:02.428095Z").astimezone(pytz.timezone("Europe/London")),
        "project-dev",
    )
    assert get_webhook_payload() == convert_slack_message_to_blocks(
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


def test_skip_data_delivery_json_error(run_slack_alerter, number_of_http_calls):
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

    response = run_slack_alerter(event)

    assert response == "Alert skipped"
    assert number_of_http_calls() == 0


def test_skip_audit_logs_error(run_slack_alerter, number_of_http_calls):
    example_log_entry = {
        "protoPayload": {
            "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
            "status": {"code": 7},
            "authenticationInfo": {
                "principalEmail": "pipeline-bucket-reader@ons-blaise-v2-shared.iam.gserviceaccount.com",
                "serviceAccountKeyName": "//iam.googleapis.com/projects/ons-blaise-v2-shared/serviceAccounts/pipeline-bucket-reader@ons-blaise-v2-shared.iam.gserviceaccount.com/keys/221e50eb36c76f17c5f6883a5a0bb29c1535ba8a",
            },
            "requestMetadata": {
                "callerIp": "10.6.0.52",
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

    response = run_slack_alerter(event)

    assert response == "Alert skipped"
    assert number_of_http_calls() == 0


def test_skip_osconfig_agent_unexpected_end_of_json_input_error(
    run_slack_alerter, number_of_http_calls
):
    null = None
    example_log_entry = {
        "insertId": "ak4u0bf38r70c",
        "jsonPayload": {
            "localTimestamp": "2023-05-18T13:22:14.1873+01:00",
            "omitempty": null,
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

    response = run_slack_alerter(event)

    assert response == "Alert skipped"
    assert number_of_http_calls() == 0


def test_skip_agent_connect_error(run_slack_alerter, number_of_http_calls):
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

    response = run_slack_alerter(event)

    assert response == "Alert skipped"
    assert number_of_http_calls() == 0


def test_skip_rproxy_lookupEffectiveGuestPolicies_error(
    run_slack_alerter, number_of_http_calls
):
    null = None
    example_log_entry = {
        "insertId": "i1tjpyftm0qks",
        "jsonPayload": {
            "message": 'Error running LookupEffectiveGuestPolicies: error calling LookupEffectiveGuestPolicies: code: "NotFound", message: "Requested entity was not found.", details: []',
            "localTimestamp": "2023-09-28T08:45:35.1241Z",
            "omitempty": null,
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

    response = run_slack_alerter(event)

    assert response == "Alert skipped"
    assert number_of_http_calls() == 0


def test_skip_watching_metadata_invalid_character_error(
    run_slack_alerter, number_of_http_calls
):
    null = None
    example_log_entry = {
        "insertId": "19s550gfh2251m",
        "jsonPayload": {
            "localTimestamp": "2023-09-18T15:12:28.8451+01:00",
            "message": "Error watching metadata: invalid character '<' looking for beginning of value",
            "omitempty": null,
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

    response = run_slack_alerter(event)

    assert response == "Alert skipped"
    assert number_of_http_calls() == 0


def test_skip_watching_metadata_invalid_character_second_version_error(
    run_slack_alerter, number_of_http_calls
):
    null = None
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

    response = run_slack_alerter(event)

    assert response == "Alert skipped"
    assert number_of_http_calls() == 0


def test_skip_watching_ip_space_exhausted_error(
    run_slack_alerter, number_of_http_calls
):
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

    response = run_slack_alerter(event)

    assert response == "Alert skipped"
    assert number_of_http_calls() == 0


def test_skip_sandbox_alerts_except_training():
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
    response = run_slack_alerter(event)

    # assert
    assert response == "Alert skipped"
    assert number_of_http_calls() == 0
