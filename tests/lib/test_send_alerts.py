import base64
import json
import logging
from unittest.mock import Mock

import pytest
from dateutil.parser import parse

from lib import send_alerts
from lib.alerter import Alerter
from lib.log_processor import ProcessedLogEntry, APP_LOG_PAYLOAD_FACTORIES
from lib.slack.slack_message import SlackMessage


@pytest.fixture
def message():
    return SlackMessage(title="example message", fields={}, content="", footnote="")


@pytest.fixture
def alerter(message) -> Mock:
    alerter = Mock(spec=Alerter)
    alerter.create_alert.return_value = message
    alerter.create_raw_alert.return_value = message
    return alerter


@pytest.fixture
def factories():
    return APP_LOG_PAYLOAD_FACTORIES


class TestWithBadPubSubEnvelope:
    @pytest.fixture
    def event(self):
        return {
            "@type": "type.googleapis.com/google.pubsub.v1.PubsubMessage",
            "attributes": {
                "logging.googleapis.com/timestamp": "2022-07-22T20:36:21.891133Z"
            },
        }

    def test_it_sends_the_alert(self, event, alerter, message, factories):
        send_alerts.send_alerts(
            event, alerter=alerter, app_log_payload_factories=factories
        )

        alerter.create_raw_alert.assert_called_with(event)
        alerter.send_alert.assert_called_with(message)

    def test_it_returns_string(self, event, alerter, factories):
        response = send_alerts.send_alerts(
            event, alerter=alerter, app_log_payload_factories=factories
        )
        assert response == "Alert sent (invalid envelope)"

    def test_it_logs_a_bad_pubsub_envelope_warning(
        self, caplog, event, log_matching, alerter, message, factories
    ):
        with caplog.at_level(logging.INFO):
            send_alerts.send_alerts(
                event, alerter=alerter, app_log_payload_factories=factories
            )
        warning = log_matching(
            logging.WARNING, "Invalid PubSub envelope: Field 'data' was missing."
        )
        assert json.loads(warning.textPayload) == event

    def test_it_logs_a_sending_raw_message_info(
        self, caplog, event, log_matching, alerter, message, factories
    ):
        with caplog.at_level(logging.INFO):
            send_alerts.send_alerts(
                event, alerter=alerter, app_log_payload_factories=factories
            )
        log_matching(logging.INFO, "Sending raw message to Slack")


class TestWithRawStringLog:
    @pytest.fixture()
    def event(self):
        return {
            "@type": "type.googleapis.com/google.pubsub.v1.PubsubMessage",
            "attributes": {
                "logging.googleapis.com/timestamp": "2022-07-22T20:36:21.891133Z"
            },
            "data": base64.b64encode(
                json.dumps("This is a raw string message").encode("ascii")
            ),
        }

    def test_it_sends_the_alert(self, event, alerter, message, factories):
        send_alerts.send_alerts(
            event, alerter=alerter, app_log_payload_factories=factories
        )
        alerter.create_alert.assert_called_with(
            ProcessedLogEntry(
                message="This is a raw string message",
                data={},
                severity=None,
                platform=None,
                application=None,
                log_name=None,
                timestamp=None,
            )
        )
        alerter.send_alert.assert_called_with(message)

    def test_it_returns_a_string(self, event, alerter, factories):
        response = send_alerts.send_alerts(
            event, alerter=alerter, app_log_payload_factories=factories
        )
        assert response == "Alert sent"

    def test_it_logs_an_info_message(
        self, event, caplog, alerter, log_matching, factories
    ):
        with caplog.at_level(logging.INFO):
            send_alerts.send_alerts(
                event, alerter=alerter, app_log_payload_factories=factories
            )

        info = log_matching(logging.INFO, "Sending message to Slack")
        assert info.textPayload == "This is a raw string message"


class TestWithStructuredLog:
    @pytest.fixture()
    def event(self):
        payload = {
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

        return {
            "@type": "type.googleapis.com/google.pubsub.v1.PubsubMessage",
            "attributes": {
                "logging.googleapis.com/timestamp": "2022-07-22T20:36:21.891133Z"
            },
            "data": base64.b64encode(json.dumps(payload).encode("ascii")),
        }

    def test_it_sends_the_alert(self, event, alerter, message, factories):
        send_alerts.send_alerts(
            event, alerter=alerter, app_log_payload_factories=factories
        )

        alerter.create_alert.assert_called_with(
            ProcessedLogEntry(
                message="Error message from VM",
                data=dict(
                    channel="application",
                    description="Error description from VM",
                    event_category="0",
                    event_id="0",
                    event_type="error",
                    record_number="6569254",
                    source_name="Blaise",
                    string_inserts=[],
                    time_generated="2022-08-02 20:06:38 +0100",
                    time_written="2022-08-02 20:06:38 +0100",
                    user="",
                ),
                severity="ERROR",
                platform="gce_instance",
                application="vm-mgmt",
                log_name="projects/secret-project/logs/winevt.raw",
                timestamp=parse("2022-08-02T19:06:42.275819947Z"),
            )
        )
        alerter.send_alert.assert_called_with(message)

    def test_it_returns_a_string(self, event, alerter, factories):
        response = send_alerts.send_alerts(
            event, alerter=alerter, app_log_payload_factories=factories
        )
        assert response == "Alert sent"

    def test_it_logs_an_info_message(
        self, event, caplog, alerter, log_matching, factories
    ):
        with caplog.at_level(logging.INFO):
            send_alerts.send_alerts(
                event, alerter=alerter, app_log_payload_factories=factories
            )

        info = log_matching(logging.INFO, "Sending message to Slack")
        assert info.textPayload == "Error message from VM"
