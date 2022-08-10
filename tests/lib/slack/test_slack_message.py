from dataclasses import replace

import pytest

from lib.log_processor import ProcessedLogEntry
from lib.slack.slack_message import create_from_processed_log_entry, SlackMessage


@pytest.fixture
def processed_log_entry() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="Example error",
        data={"example_field": "example value"},
        severity="ERROR",
        platform="cloud_functions",
        application="my-app",
        log_name="/log/my-log",
        timestamp="2022-08-10T14:54:03.318939Z",
    )


def test_create_from_processed_log_entry(processed_log_entry):
    message = create_from_processed_log_entry(
        processed_log_entry, project_name="example-gcp-project"
    )

    assert message == SlackMessage(
        title="ERROR: Example error",
        fields=dict(
            Platform="cloud_functions",
            Application="my-app",
            Project="example-gcp-project",
        ),
        content='{\n  "example_field": "example value"\n}',
        footnote=(
            "*Next Steps*\n"
            "1. Add some :eyes: to show you are investigating\n"
            "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=example-gcp-project | Check the system is online>\n"
            "3. <https://console.cloud.google.com/logs/query;query=%0A;cursorTimestamp=2022-08-10T14:54:03.318939Z?referrer=search&project=example-gcp-project | View the logs>\n"
            "4. Follow the <https://confluence.ons.gov.uk/pages/viewpage.action?pageId=98502389 | Managing Prod Alerts> process"
        ),
    )


def test_create_from_processed_log_with_string_data(processed_log_entry):
    message = create_from_processed_log_entry(
        replace(processed_log_entry, data="This data is a string"),
        project_name="example-gcp-project",
    )

    assert message.content == "This data is a string"


def test_create_from_processed_log_with_no_severity(processed_log_entry):
    message = create_from_processed_log_entry(
        replace(processed_log_entry, severity=None), project_name="example-gcp-project"
    )

    assert message.title == "UNKNOWN: Example error"


def test_create_from_processed_log_with_no_platform(processed_log_entry):
    message = create_from_processed_log_entry(
        replace(processed_log_entry, platform=None), project_name="example-gcp-project"
    )

    assert message.fields["Platform"] == "unknown"


def test_create_from_processed_log_with_no_application(processed_log_entry):
    message = create_from_processed_log_entry(
        replace(processed_log_entry, application=None),
        project_name="example-gcp-project",
    )

    assert message.fields["Application"] == "unknown"


def test_create_from_processed_log_with_no_timestamp(processed_log_entry):
    message = create_from_processed_log_entry(
        replace(processed_log_entry, timestamp=None), project_name="example-gcp-project"
    )

    assert message.footnote == (
        "*Next Steps*\n"
        "1. Add some :eyes: to show you are investigating\n"
        "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=example-gcp-project | Check the system is online>\n"
        "3. Determine the cause of the error\n"
        "4. Follow the <https://confluence.ons.gov.uk/pages/viewpage.action?pageId=98502389 | Managing Prod Alerts> process"
    )
