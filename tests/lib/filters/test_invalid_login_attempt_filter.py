import pytest
import datetime
import dataclasses

from lib.log_processor import ProcessedLogEntry
from lib.filters.invalid_login_attempt_filter import invalid_login_attempt_filter


@pytest.fixture()
def processed_log_entry_invalid_login_attempt_error_Slack() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="alert: ERROR: [AuditLog] Required \"container.clusters.list\" permission(s) for \"projects/ons-blaise-v2-prod\".'}}, {'type': 'section', 'fields': [{'type': 'mrkdwn', 'text': '*Platform:*\\ngke_cluster'}, {'type': 'mrkdwn', 'text': '*Application:*\\n[unknown]'}, {'type': 'mrkdwn', 'text': '*Log Time:*\\n2024-05-02 09:55:17'}, {'type': 'mrkdwn', 'text': '*Project:*\\nons-blaise-v2-prod'}]}, {'type': 'divider'}, {'type': 'section', 'text': {'type': 'plain_text', 'text': 'serviceName: container.googleapis.com\\nmethodName: google.container.v1.ClusterManager.ListClusters'}}, {'type': 'divider'}, {'type': 'section', 'text': {'type': 'mrkdwn', 'text': '*Next Steps*\\n1. Add some :eyes: to show you are investigating\\n2. <https://console.cloud.google.com/monitoring/uptime?referrer=search&project=ons-blaise-v2-prod | Check the system is online>\\n3. <https://console.cloud.google.com/logs/query;query=protoPayload.@type:%22type.googleapis.com/google.cloud.audit.AuditLog%22%20severity%3D%28WARNING%20OR%20ERROR%20OR%20CRITICAL%20OR%20ALERT%20OR%20EMERGENCY%20OR%20DEBUG%29;timeRange=2024-05-02T08:55:17.641927Z%2F2024-05-02T08:55:17.641927Z--PT1M?referrer=search&project=ons-blaise-v2-prod | View the logs>\\n4. Follow the <https://confluence.ons.gov.uk/pages/viewpage.action?pageId=98502389 | Managing Prod Alerts> process'}}]})",
        data=dict(description="dummy"),
        severity="ERROR",
        platform="cloud_run_revision",
        application="slack-alerts",
        log_name="/logs/cloudfunctions",
        timestamp=datetime.datetime(2024, 5, 20, 10, 23, 56, 32425),
        log_query={
            "resource.type": "cloud_run_revision",
            "resource.labels.instance_id": "00f46b928521d49fcdbf455e4592829a1631850562c1b37283d70572deaca72b851130f7fbca367bbb5a75b386efa9832f3d974f1a5a463b2fb9af0fb2a9c2fb4e57",
        },
    )


@pytest.fixture()
def processed_log_entry_invalid_login_attempt_error_GCP() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message='Required "container.clusters.list" permission(s) for "projects/ons-blaise-v2-prod".',
        data=dict(description="dummy"),
        severity="ERROR",
        platform="cloud_run_revision",
        application="unknown",
        log_name="/logs/cloudfunctions",
        timestamp=datetime.datetime(2024, 4, 18, 6, 22, 54, 24321),
        log_query={
            "resource.type": "cloud_run_revision",
            "resource.labels.instance_id": "234023940239340394",
        },
    )


def test_log_is_not_skipped_when_its_first_run_invalid_login_attempt_error_Slack(
    processed_log_entry_invalid_login_attempt_error_Slack: ProcessedLogEntry,
):
    log_is_skipped = invalid_login_attempt_filter(
        processed_log_entry_invalid_login_attempt_error_Slack
    )
    assert log_is_skipped is True


def test_log_is_skipped_when_its_from_cloud_run_revision_when_invalid_login_attempt_error_GCP(
    processed_log_entry_invalid_login_attempt_error_GCP: ProcessedLogEntry,
):
    log_is_skipped = invalid_login_attempt_filter(
        processed_log_entry_invalid_login_attempt_error_GCP
    )
    assert log_is_skipped is True


def test_log_message_is_not_a_string_when_invalid_login_attempt_error_Slack(
    processed_log_entry_invalid_login_attempt_error_Slack: ProcessedLogEntry,
):
    processed_log_entry_invalid_login_attempt_error_Slack = dataclasses.replace(
        processed_log_entry_invalid_login_attempt_error_Slack, message=1234
    )
    log_is_skipped = invalid_login_attempt_filter(
        processed_log_entry_invalid_login_attempt_error_Slack
    )

    assert log_is_skipped is False


def test_log_message_is_not_a_string_when_invalid_login_attempt_error_GCP(
    processed_log_entry_invalid_login_attempt_error_GCP: ProcessedLogEntry,
):
    processed_log_entry_invalid_login_attempt_error_GCP = dataclasses.replace(
        processed_log_entry_invalid_login_attempt_error_GCP, message=1234
    )
    log_is_skipped = invalid_login_attempt_filter(
        processed_log_entry_invalid_login_attempt_error_GCP
    )

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_does_not_contain_invalid_login_attempt_error_Slack(
    processed_log_entry_invalid_login_attempt_error_Slack: ProcessedLogEntry,
):
    processed_log_entry_invalid_login_attempt_error_Slack = dataclasses.replace(
        processed_log_entry_invalid_login_attempt_error_Slack, message="foo"
    )
    log_is_skipped = invalid_login_attempt_filter(
        processed_log_entry_invalid_login_attempt_error_Slack
    )

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_does_not_contain_invalid_login_attempt_error_GCP(
    processed_log_entry_invalid_login_attempt_error_GCP: ProcessedLogEntry,
):
    processed_log_entry_invalid_login_attempt_error_GCP = dataclasses.replace(
        processed_log_entry_invalid_login_attempt_error_GCP, message="foo"
    )
    log_is_skipped = invalid_login_attempt_filter(
        processed_log_entry_invalid_login_attempt_error_GCP
    )

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_contains_severity_info_Slack(
    processed_log_entry_invalid_login_attempt_error_Slack: ProcessedLogEntry,
):
    processed_log_entry_invalid_login_attempt_error_Slack = dataclasses.replace(
        processed_log_entry_invalid_login_attempt_error_Slack, severity="INFO"
    )
    log_is_skipped = invalid_login_attempt_filter(
        processed_log_entry_invalid_login_attempt_error_Slack
    )

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_contains_severity_info_GCP(
    processed_log_entry_invalid_login_attempt_error_GCP: ProcessedLogEntry,
):
    processed_log_entry_invalid_login_attempt_error_GCP = dataclasses.replace(
        processed_log_entry_invalid_login_attempt_error_GCP, severity="INFO"
    )
    log_is_skipped = invalid_login_attempt_filter(
        processed_log_entry_invalid_login_attempt_error_GCP
    )

    assert log_is_skipped is False
