import dataclasses
from dataclasses import replace
from datetime import datetime

import pytest
from dateutil.parser import parse

from lib.cloud_logging.log_query_link import create_log_query_link
from lib.log_processor.processed_log_entry import ProcessedLogEntry
from lib.slack.slack_message import (SlackMessage, _create_footnote,
                                     create_from_processed_log_entry)


@pytest.fixture()
def log_timestamp() -> datetime:
    return parse("2022-08-10T14:54:03.318939Z")


@pytest.fixture()
def log_timestamp_gmt() -> datetime:
    return parse("2022-01-10T14:54:03.318939Z")


@pytest.fixture()
def processed_log_entry(log_timestamp: datetime) -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="Example error",
        data={"example_field": "example value"},
        severity="ERROR",
        platform="cloud_run_revisions",
        application="my-app",
        log_name="/log/my-log",
        timestamp=log_timestamp,
        log_query={},
        most_important_values=None,
    )


@pytest.fixture()
def log_query_link(log_timestamp: datetime) -> str:
    return create_log_query_link(
        fields={},
        severities=["WARNING", "ERROR", "CRITICAL", "ALERT", "EMERGENCY", "DEBUG"],
        cursor_timestamp=log_timestamp,
        project_name="example-gcp-project",
    )


@pytest.fixture()
def log_query_link_in_gmt(log_timestamp_gmt: datetime) -> str:
    return create_log_query_link(
        fields={},
        severities=["WARNING", "ERROR", "CRITICAL", "ALERT", "EMERGENCY", "DEBUG"],
        cursor_timestamp=log_timestamp_gmt,
        project_name="example-gcp-project",
    )


def test_create_from_processed_log_entry(
    processed_log_entry: ProcessedLogEntry, log_query_link: str
) -> None:
    message = create_from_processed_log_entry(
        processed_log_entry,
        project_name="example-gcp-project",
    )

    assert message == SlackMessage(
        title=":alert: ERROR: Example error",
        fields={
            "Platform": "cloud_run_revisions",
            "Application": "my-app",
            "Log Time": "2022-08-10 15:54:03",
            "Project": "example-gcp-project",
        },
        content='{\n  "example_field": "example value"\n}',
        footnote=(
            "*Next Steps*\n"
            "1. Add some :eyes: to show you are investigating\n"
            "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=example-gcp-project | Check the system is online>\n"
            f"3. <{log_query_link} | View the logs>\n"
            "4. Follow the <https://officefornationalstatistics.atlassian.net/wiki/spaces/QSS/pages/50299787/Troubleshooting+Playbook+-+Slack+Alerts | Managing Prod Alerts> process"
        ),
    )


def test_create_from_processed_log_entry_with_timestamp_in_gmt(
    processed_log_entry: ProcessedLogEntry,
    log_timestamp_gmt: datetime,
    log_query_link_in_gmt: str,
) -> None:
    message = create_from_processed_log_entry(
        replace(
            processed_log_entry,
            timestamp=log_timestamp_gmt,
        ),
        project_name="example-gcp-project",
    )

    assert message == SlackMessage(
        title=":alert: ERROR: Example error",
        fields={
            "Platform": "cloud_run_revisions",
            "Application": "my-app",
            "Log Time": "2022-01-10 14:54:03",
            "Project": "example-gcp-project",
        },
        content='{\n  "example_field": "example value"\n}',
        footnote=(
            "*Next Steps*\n"
            "1. Add some :eyes: to show you are investigating\n"
            "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=example-gcp-project | Check the system is online>\n"
            f"3. <{log_query_link_in_gmt} | View the logs>\n"
            "4. Follow the <https://officefornationalstatistics.atlassian.net/wiki/spaces/QSS/pages/50299787/Troubleshooting+Playbook+-+Slack+Alerts | Managing Prod Alerts> process"
        ),
    )


def test_create_from_processed_log_entry_with_most_important_fields(
    processed_log_entry: ProcessedLogEntry, log_query_link: str
) -> None:
    message = create_from_processed_log_entry(
        replace(
            processed_log_entry,
            data=dict(
                value1=dict(inner="Value One"), value2="Value Two", value3="Value Three"
            ),
            most_important_values=["value3", "value1.inner"],
        ),
        project_name="example-gcp-project",
    )

    assert message == SlackMessage(
        title=":alert: ERROR: Example error",
        fields={
            "Platform": "cloud_run_revisions",
            "Application": "my-app",
            "Log Time": "2022-08-10 15:54:03",
            "Project": "example-gcp-project",
        },
        content="value3: Value Three\nvalue1.inner: Value One",
        footnote=(
            "*Next Steps*\n"
            "1. Add some :eyes: to show you are investigating\n"
            "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=example-gcp-project | Check the system is online>\n"
            f"3. <{log_query_link} | View the logs>\n"
            "4. Follow the <https://officefornationalstatistics.atlassian.net/wiki/spaces/QSS/pages/50299787/Troubleshooting+Playbook+-+Slack+Alerts | Managing Prod Alerts> process"
        ),
    )


def test_create_from_processed_log_entry_with_most_important_field_not_found(
    processed_log_entry: ProcessedLogEntry, log_query_link: str
) -> None:
    message = create_from_processed_log_entry(
        replace(
            processed_log_entry,
            data=dict(
                value1=dict(inner="Value One"), value2="Value Two", value3="Value Three"
            ),
            most_important_values=["value3", "value1.deep.inner"],
        ),
        project_name="example-gcp-project",
    )

    assert message == SlackMessage(
        title=":alert: ERROR: Example error",
        fields={
            "Platform": "cloud_run_revisions",
            "Application": "my-app",
            "Log Time": "2022-08-10 15:54:03",
            "Project": "example-gcp-project",
        },
        content="value3: Value Three",
        footnote=(
            "*Next Steps*\n"
            "1. Add some :eyes: to show you are investigating\n"
            "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=example-gcp-project | Check the system is online>\n"
            f"3. <{log_query_link} | View the logs>\n"
            "4. Follow the <https://officefornationalstatistics.atlassian.net/wiki/spaces/QSS/pages/50299787/Troubleshooting+Playbook+-+Slack+Alerts | Managing Prod Alerts> process"
        ),
    )


def test_create_from_processed_log_entry_with_no_important_fields(
    processed_log_entry: ProcessedLogEntry, log_query_link: str
) -> None:
    message = create_from_processed_log_entry(
        replace(
            processed_log_entry,
            data=dict(value1="Value One", value2="Value Two", value3="Value Three"),
            most_important_values=["missing1", "missing2"],
        ),
        project_name="example-gcp-project",
    )

    assert message == SlackMessage(
        title=":alert: ERROR: Example error",
        fields={
            "Platform": "cloud_run_revisions",
            "Application": "my-app",
            "Log Time": "2022-08-10 15:54:03",
            "Project": "example-gcp-project",
        },
        content="{\n"
        '  "value1": "Value One",\n'
        '  "value2": "Value Two",\n'
        '  "value3": "Value Three"\n'
        "}",
        footnote=(
            "*Next Steps*\n"
            "1. Add some :eyes: to show you are investigating\n"
            "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=example-gcp-project | Check the system is online>\n"
            f"3. <{log_query_link} | View the logs>\n"
            "4. Follow the <https://officefornationalstatistics.atlassian.net/wiki/spaces/QSS/pages/50299787/Troubleshooting+Playbook+-+Slack+Alerts | Managing Prod Alerts> process"
        ),
    )


def test_create_from_processed_log_with_string_data(
    processed_log_entry: ProcessedLogEntry,
) -> None:
    message = create_from_processed_log_entry(
        replace(processed_log_entry, data="This data is a string"),
        project_name="example-gcp-project",
    )

    assert message.content == "This data is a string"


def test_create_from_processed_log_query_fields(processed_log_entry, log_timestamp):
    message = create_from_processed_log_entry(
        replace(processed_log_entry, log_query=dict(field1="value1", field2="value2")),
        project_name="example-gcp-project",
    )

    log_query_link = create_log_query_link(
        fields=dict(field1="value1", field2="value2"),
        severities=["WARNING", "ERROR", "CRITICAL", "ALERT", "EMERGENCY", "DEBUG"],
        cursor_timestamp=log_timestamp,
        project_name="example-gcp-project",
    )

    assert message.footnote == (
        "*Next Steps*\n"
        "1. Add some :eyes: to show you are investigating\n"
        "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=example-gcp-project | Check the system is online>\n"
        f"3. <{log_query_link} | View the logs>\n"
        "4. Follow the <https://officefornationalstatistics.atlassian.net/wiki/spaces/QSS/pages/50299787/Troubleshooting+Playbook+-+Slack+Alerts | Managing Prod Alerts> process"
    )


def test_create_from_processed_log_with_no_severity(processed_log_entry):
    message = create_from_processed_log_entry(
        replace(processed_log_entry, severity=None), project_name="example-gcp-project"
    )

    assert message.title == ":alert: UNKNOWN: Example error"


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

    assert message.fields["Log Time"] == "unknown"
    assert message.footnote == (
        "*Next Steps*\n"
        "1. Add some :eyes: to show you are investigating\n"
        "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=example-gcp-project | Check the system is online>\n"
        "3. Determine the cause of the error\n"
        "4. Follow the <https://officefornationalstatistics.atlassian.net/wiki/spaces/QSS/pages/50299787/Troubleshooting+Playbook+-+Slack+Alerts | Managing Prod Alerts> process"
    )


def test_create_from_processed_log_with_message_containing_newlines(
    processed_log_entry,
):
    message = create_from_processed_log_entry(
        replace(
            processed_log_entry,
            message="An error occurred\nIt was a terrible error",
            data="Extra content",
        ),
        project_name="example-gcp-project",
    )

    assert message.title == ":alert: ERROR: An error occurred"
    assert message.content == (
        "**Error Message**\n"
        "An error occurred\n"
        "It was a terrible error\n"
        "\n"
        "**Extra Content**\n"
        "Extra content"
    )


def test_create_from_processed_log_with_titles_over_150_characters(processed_log_entry):
    message = create_from_processed_log_entry(
        replace(
            processed_log_entry,
            message=(
                "This message creates a title over 150 characters long when combined with the severity "
                "because it is really really really really really really long"
            ),
            severity="ERROR",
            data="Extra content",
        ),
        project_name="example-gcp-project",
    )

    assert message.title == (
        ":alert: ERROR: This message creates a title over 150 characters long when combined with the severity "
        "because it is really really really really re..."
    )
    assert message.content == (
        "**Error Message**\n"
        "This message creates a title over 150 characters long when combined with the "
        "severity because it is really really really really really really long\n"
        "\n"
        "**Extra Content**\n"
        "Extra content"
    )


def test_create_from_processed_log_with_content_over_2900_characters(
    processed_log_entry,
):
    message = create_from_processed_log_entry(
        replace(
            processed_log_entry,
            message="Example Title",
            severity="ERROR",
            data="X" * 2901,
        ),
        project_name="example-gcp-project",
    )

    assert message.content == f"{'X' * 2900}...\n[truncated]"


def test_create_from_processed_log_with_content_over_2900_characters_with_extra_message(
    processed_log_entry,
):
    message = create_from_processed_log_entry(
        replace(
            processed_log_entry,
            message="Example Title\nAdditional Line",
            severity="ERROR",
            data="X" * 2901,
        ),
        project_name="example-gcp-project",
    )

    extra_chars = (
        "**Error Message**\nExample Title\nAdditional Line\n\n**Extra Content**\n"
    )

    assert message.content == (
        f"{extra_chars}{'X' * (2900 - len(extra_chars))}...\n[truncated]"
    )


def test_create_from_processed_log_with_content_with_10_line_(
    processed_log_entry,
):
    message = create_from_processed_log_entry(
        replace(
            processed_log_entry,
            message="Example Title",
            severity="ERROR",
            data=(
                "line1\n"
                "line2\n"
                "line3\n"
                "line4\n"
                "line5\n"
                "line6\n"
                "line7\n"
                "line8\n"
                "line9\n"
                "line10"
            ),
        ),
        project_name="example-gcp-project",
    )

    assert message.content == (
        "line1\n"
        "line2\n"
        "line3\n"
        "line4\n"
        "line5\n"
        "line6\n"
        "line7\n"
        "line8\n"
        "line9\n"
        "line10"
    )


def test_create_from_processed_log_with_content_over_10_lines(
    processed_log_entry,
):
    message = create_from_processed_log_entry(
        replace(
            processed_log_entry,
            message="Example Title",
            severity="ERROR",
            data=(
                "line1\n"
                "line2\n"
                "line3\n"
                "line4\n"
                "line5\n"
                "line6\n"
                "line7\n"
                "line8\n"
                "line9\n"
                "line10\n"
                "line11\n"
            ),
        ),
        project_name="example-gcp-project",
    )

    assert message.content == (
        "line1\n"
        "line2\n"
        "line3\n"
        "line4\n"
        "line5\n"
        "line6\n"
        "line7\n"
        "line8\n"
        "...\n"
        "[truncated]"
    )


def test_create_from_processed_log_with_content_over_10_lines_including_extra_content(
    processed_log_entry,
):
    message = create_from_processed_log_entry(
        replace(
            processed_log_entry,
            message="Example Title\nExtra Line",
            severity="ERROR",
            data=("line1\n" "line2\n" "line3\n" "line4\n" "line5\n" "line6"),
        ),
        project_name="example-gcp-project",
    )

    assert message.content == (
        "**Error Message**\n"
        "Example Title\n"
        "Extra Line\n"
        "\n"
        "**Extra Content**\n"
        "line1\n"
        "line2\n"
        "line3\n"
        "...\n"
        "[truncated]"
    )


def test_create_footnote_returns_default_instructions_with_view_the_logs_line(
    processed_log_entry,
):
    # arrange
    project_name = "foobar"

    # act
    result = _create_footnote(processed_log_entry, project_name)

    # assert
    assert result == (
        "*Next Steps*\n"
        "1. Add some :eyes: to show you are investigating\n"
        "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=foobar | Check the system is online>\n"
        "3. <https://console.cloud.google.com/logs/query;query=severity%3D%28WARNING%20OR%20ERROR%20OR%20CRITICAL%20OR%20ALERT%20OR%20EMERGENCY%20OR%20DEBUG%29;timeRange=2022-08-10T14:54:03.318939Z%2F2022-08-10T14:54:03.318939Z--PT1M?referrer=search&project=foobar | View the logs>\n"
        "4. Follow the <https://officefornationalstatistics.atlassian.net/wiki/spaces/QSS/pages/50299787/Troubleshooting+Playbook+-+Slack+Alerts | Managing Prod Alerts> process"
    )


def test_create_footnote_returns_default_instructions_without_view_the_logs_line(
    processed_log_entry,
):
    # arrange
    project_name = "foobar"
    processed_log_entry_without_timestamp = dataclasses.replace(
        processed_log_entry, timestamp=None
    )

    # act
    result = _create_footnote(processed_log_entry_without_timestamp, project_name)

    # assert
    assert result == (
        "*Next Steps*\n"
        "1. Add some :eyes: to show you are investigating\n"
        "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=foobar | Check the system is online>\n"
        "3. Determine the cause of the error\n"
        "4. Follow the <https://officefornationalstatistics.atlassian.net/wiki/spaces/QSS/pages/50299787/Troubleshooting+Playbook+-+Slack+Alerts | Managing Prod Alerts> process"
    )


@pytest.mark.parametrize(
    "data_delivery_application",
    [
        "data-delivery",
        "NiFiEncryptFunction",
        "nifi-notify",
        "nifi-receipt",
    ],
)
def test_create_footnote_returns_data_delivery_instructions_with_view_the_logs_line(
    processed_log_entry, data_delivery_application
):
    # arrange
    project_name = "foobar"
    processed_data_delivery_log_entry = dataclasses.replace(
        processed_log_entry, application=data_delivery_application
    )

    # act
    result = _create_footnote(processed_data_delivery_log_entry, project_name)

    # assert
    assert result == (
        "*Next Steps*\n"
        "1. Add some :eyes: to show you are investigating\n"
        "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=foobar | Check the system is online>\n"
        "3. <https://console.cloud.google.com/logs/query;query=severity%3D%28WARNING%20OR%20ERROR%20OR%20CRITICAL%20OR%20ALERT%20OR%20EMERGENCY%20OR%20DEBUG%29;timeRange=2022-08-10T14:54:03.318939Z%2F2022-08-10T14:54:03.318939Z--PT1M?referrer=search&project=foobar | View the logs>\n"
        "4. <https://officefornationalstatistics.atlassian.net/wiki/spaces/QSS/pages/50299847/Troubleshooting+Playbook+-+Data+Delivery | View the Data Delivery Troubleshooting Playbook>"
    )


@pytest.mark.parametrize(
    "data_delivery_application",
    [
        "data-delivery",
        "NiFiEncryptFunction",
        "nifi-notify",
        "nifi-receipt",
    ],
)
def test_create_footnote_returns_data_delivery_instructions_without_view_the_logs_line(
    processed_log_entry, data_delivery_application
):
    # arrange
    project_name = "foobar"
    processed_data_delivery_log_entry = dataclasses.replace(
        processed_log_entry, application=data_delivery_application, timestamp=None
    )

    # act
    result = _create_footnote(processed_data_delivery_log_entry, project_name)

    # assert
    assert result == (
        "*Next Steps*\n"
        "1. Add some :eyes: to show you are investigating\n"
        "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=foobar | Check the system is online>\n"
        "3. Determine the cause of the error\n"
        "4. <https://officefornationalstatistics.atlassian.net/wiki/spaces/QSS/pages/50299847/Troubleshooting+Playbook+-+Data+Delivery | View the Data Delivery Troubleshooting Playbook>"
    )


@pytest.mark.parametrize(
    "totalmobile_error",
    [
        "Unable to delete job reference LMS6666-FO0.123456 from Totalmobile",
        "Could not find questionnaire LMS6666-FO0 in Blaise",
        "Could not find case 123456 for questionnaire LMS6666-FO0 in Blaise",
        "ERROR: Exception on / [POST] for bts-create-totalmobile-jobs-processor",
    ],
)
def test_create_footnote_returns_totalmobile_instructions_with_view_the_logs_line(
    processed_log_entry, totalmobile_error
):
    # arrange
    project_name = "foobar"
    processed_totalmobile_log_entry = dataclasses.replace(
        processed_log_entry, message=totalmobile_error
    )

    # act
    result = _create_footnote(processed_totalmobile_log_entry, project_name)

    # assert
    assert result == (
        "*Next Steps*\n"
        "1. Add some :eyes: to show you are investigating\n"
        "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=foobar | Check the system is online>\n"
        "3. <https://console.cloud.google.com/logs/query;query=severity%3D%28WARNING%20OR%20ERROR%20OR%20CRITICAL%20OR%20ALERT%20OR%20EMERGENCY%20OR%20DEBUG%29;timeRange=2022-08-10T14:54:03.318939Z%2F2022-08-10T14:54:03.318939Z--PT1M?referrer=search&project=foobar | View the logs>\n"
        "4. <https://officefornationalstatistics.atlassian.net/wiki/spaces/QSS/pages/50326799/Troubleshooting+Playbook+-+BTS+Totalmobile | View the BTS/Totalmobile Troubleshooting Playbook>"
    )


@pytest.mark.parametrize(
    "totalmobile_error",
    [
        "Unable to delete job reference LMS6666-FO0.123456 from Totalmobile",
        "Could not find questionnaire LMS6666-FO0 in Blaise",
        "Could not find case 123456 for questionnaire LMS6666-FO0 in Blaise",
        "ERROR: Exception on / [POST] for bts-create-totalmobile-jobs-processor",
    ],
)
def test_create_footnote_returns_totalmobile_instructions_without_view_the_logs_line(
    processed_log_entry, totalmobile_error
):
    # arrange
    project_name = "foobar"
    processed_totalmobile_log_entry = dataclasses.replace(
        processed_log_entry, message=totalmobile_error, timestamp=None
    )

    # act
    result = _create_footnote(processed_totalmobile_log_entry, project_name)

    # assert
    assert result == (
        "*Next Steps*\n"
        "1. Add some :eyes: to show you are investigating\n"
        "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=foobar | Check the system is online>\n"
        "3. Determine the cause of the error\n"
        "4. <https://officefornationalstatistics.atlassian.net/wiki/spaces/QSS/pages/50326799/Troubleshooting+Playbook+-+BTS+Totalmobile | View the BTS/Totalmobile Troubleshooting Playbook>"
    )


def test_create_footnote_returns_totalmobile_instructions_from_cloud_scheduler_job_with_view_the_logs_line(
    processed_log_entry,
):
    # arrange
    project_name = "foobar"
    processed_totalmobile_log_entry = dataclasses.replace(
        processed_log_entry,
        log_query={
            "@type": "type.googleapis.com/google.cloud.scheduler.logging.AttemptFinished",
            "jobName": "projects/foobar/locations/europe-west2/jobs/bts-delete-totalmobile-jobs-completed-in-blaise",
            "status": "UNKNOWN",
            "targetType": "HTTP",
            "url": "https://bts-delete-totalmobile-jobs-completed-in-blaise-jogztar7aa-nw.a.run.app/",
        },
    )

    # act
    result = _create_footnote(processed_totalmobile_log_entry, project_name)

    # assert
    assert result == (
        "*Next Steps*\n"
        "1. Add some :eyes: to show you are investigating\n"
        "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=foobar | Check the system is online>\n"
        "3. <https://console.cloud.google.com/logs/query;query=@type:%22type.googleapis.com/google.cloud.scheduler.logging.AttemptFinished%22%20jobName:%22projects/foobar/locations/europe-west2/jobs/bts-delete-totalmobile-jobs-completed-in-blaise%22%20status:%22UNKNOWN%22%20targetType:%22HTTP%22%20url:%22https://bts-delete-totalmobile-jobs-completed-in-blaise-jogztar7aa-nw.a.run.app/%22%20severity%3D%28WARNING%20OR%20ERROR%20OR%20CRITICAL%20OR%20ALERT%20OR%20EMERGENCY%20OR%20DEBUG%29;timeRange=2022-08-10T14:54:03.318939Z%2F2022-08-10T14:54:03.318939Z--PT1M?referrer=search&project=foobar | View the logs>\n"
        "4. <https://officefornationalstatistics.atlassian.net/wiki/spaces/QSS/pages/50326799/Troubleshooting+Playbook+-+BTS+Totalmobile | View the BTS/Totalmobile Troubleshooting Playbook>"
    )


@pytest.mark.parametrize(
    "nisra_application",
    [
        "nisra-case-mover",
        "nisra-case-mover-trigger",
    ],
)
def test_create_footnote_returns_nisra_instructions_from_nisra_application_with_view_the_logs_line(
    processed_log_entry, nisra_application
):
    # arrange
    project_name = "foobar"
    processed_nisra_log_entry = dataclasses.replace(
        processed_log_entry, application=nisra_application
    )

    # act
    result = _create_footnote(processed_nisra_log_entry, project_name)

    # assert
    assert result == (
        "*Next Steps*\n"
        "1. Add some :eyes: to show you are investigating\n"
        "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=foobar | Check the system is online>\n"
        "3. <https://console.cloud.google.com/logs/query;query=severity%3D%28WARNING%20OR%20ERROR%20OR%20CRITICAL%20OR%20ALERT%20OR%20EMERGENCY%20OR%20DEBUG%29;timeRange=2022-08-10T14:54:03.318939Z%2F2022-08-10T14:54:03.318939Z--PT1M?referrer=search&project=foobar | View the logs>\n"
        "4. <https://officefornationalstatistics.atlassian.net/wiki/spaces/QSS/pages/50326981/Troubleshooting+Playbook+-+NISRA | View the NISRA Troubleshooting Playbook>"
    )


@pytest.mark.parametrize(
    "nisra_application",
    [
        "nisra-case-mover",
        "nisra-case-mover-trigger",
    ],
)
def test_create_footnote_returns_nisra_instructions_from_nisra_application_without_view_the_logs_line(
    processed_log_entry, nisra_application
):
    # arrange
    project_name = "foobar"
    processed_nisra_log_entry = dataclasses.replace(
        processed_log_entry, application=nisra_application, timestamp=None
    )

    # act
    result = _create_footnote(processed_nisra_log_entry, project_name)

    # assert
    assert result == (
        "*Next Steps*\n"
        "1. Add some :eyes: to show you are investigating\n"
        "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=foobar | Check the system is online>\n"
        "3. Determine the cause of the error\n"
        "4. <https://officefornationalstatistics.atlassian.net/wiki/spaces/QSS/pages/50326981/Troubleshooting+Playbook+-+NISRA | View the NISRA Troubleshooting Playbook>"
    )


def test_create_footnote_returns_nisra_instructions_from_cloud_scheduler_job_with_view_the_logs_line(
    processed_log_entry,
):
    # arrange
    project_name = "foobar"
    processed_data_delivery_log_entry = dataclasses.replace(
        processed_log_entry,
        log_query={
            "@type": "type.googleapis.com/google.cloud.scheduler.logging.AttemptFinished",
            "jobName": "projects/foobar/locations/europe-west2/jobs/nisra-trigger-lms",
            "pubsubTopic": "projects/ons-blaise-v2-prod/topics/ons-blaise-v2-prod-nisra-trigger",
            "status": "DEADLINE_EXCEEDED",
            "targetType": "PUB_SUB",
        },
    )

    # act
    result = _create_footnote(processed_data_delivery_log_entry, project_name)

    # assert
    assert result == (
        "*Next Steps*\n"
        "1. Add some :eyes: to show you are investigating\n"
        "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=foobar | Check the system is online>\n"
        "3. <https://console.cloud.google.com/logs/query;query=@type:%22type.googleapis.com/google.cloud.scheduler.logging.AttemptFinished%22%20jobName:%22projects/foobar/locations/europe-west2/jobs/nisra-trigger-lms%22%20pubsubTopic:%22projects/ons-blaise-v2-prod/topics/ons-blaise-v2-prod-nisra-trigger%22%20status:%22DEADLINE_EXCEEDED%22%20targetType:%22PUB_SUB%22%20severity%3D%28WARNING%20OR%20ERROR%20OR%20CRITICAL%20OR%20ALERT%20OR%20EMERGENCY%20OR%20DEBUG%29;timeRange=2022-08-10T14:54:03.318939Z%2F2022-08-10T14:54:03.318939Z--PT1M?referrer=search&project=foobar | View the logs>\n"
        "4. <https://officefornationalstatistics.atlassian.net/wiki/spaces/QSS/pages/50326981/Troubleshooting+Playbook+-+NISRA | View the NISRA Troubleshooting Playbook>"
    )


def test_create_footnote_returns_nisra_instructions_from_cloud_scheduler_job_without_view_the_logs_line(
    processed_log_entry,
):
    # arrange
    project_name = "foobar"
    processed_data_delivery_log_entry = dataclasses.replace(
        processed_log_entry,
        log_query={
            "@type": "type.googleapis.com/google.cloud.scheduler.logging.AttemptFinished",
            "jobName": "projects/foobar/locations/europe-west2/jobs/nisra-trigger-lms",
            "pubsubTopic": "projects/ons-blaise-v2-prod/topics/ons-blaise-v2-prod-nisra-trigger",
            "status": "DEADLINE_EXCEEDED",
            "targetType": "PUB_SUB",
        },
        timestamp=None,
    )

    # act
    result = _create_footnote(processed_data_delivery_log_entry, project_name)

    # assert
    assert result == (
        "*Next Steps*\n"
        "1. Add some :eyes: to show you are investigating\n"
        "2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=foobar | Check the system is online>\n"
        "3. Determine the cause of the error\n"
        "4. <https://officefornationalstatistics.atlassian.net/wiki/spaces/QSS/pages/50326981/Troubleshooting+Playbook+-+NISRA | View the NISRA Troubleshooting Playbook>"
    )
