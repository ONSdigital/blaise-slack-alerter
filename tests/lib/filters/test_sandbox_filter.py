import pytest
import datetime

from lib.log_processor import ProcessedLogEntry
from lib.filters.sandbox_filter import sandbox_filter, is_sandbox_environment


@pytest.fixture()
def processed_log_entry() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="This is an example message",
        data={
            "logName": "projects/ons-blaise-v2-dev-jw09/logs/%40google-cloud%2Fprofiler",
            "resource": {
                "type": "gae_app_example",
                "labels": {
                    "version_id": "20231129t144628_example",
                    "module_id": "dqs-ui-example",
                    "zone": "europe-west2-1-example",
                },
            },
            "timestamp": "2023-11-29T15:34:54.591Z",
        },
        severity="DEBUG",
        platform="gae_app_example",
        application="dqs-ui-example",
        log_name="projects/ons-blaise-v2-dev-jw09/logs/stdout",
        timestamp=datetime.datetime(2023, 11, 29, 15, 34, 54, 591),
        log_query={
            "resource.type": "gae_app_example",
            "resource.labels.module_id": "dqs-ui-example",
        },
        most_important_values=[
            "status",
            "host",
            "method",
            "resource",
            "ip",
            "latency",
            "responseSize",
            "httpVersion",
        ],
    )


def test_log_is_skipped_for_sandbox_environment(
    processed_log_entry: ProcessedLogEntry,
):
    # act
    log_is_skipped = sandbox_filter(processed_log_entry)

    # assert
    assert log_is_skipped is True


def test_is_sandbox_environment_returns_true_for_sandbox_environment():
    # arrange
    log_name_example = "projects/ons-blaise-v2-dev-jw09/logs/stdout"

    # act
    result = is_sandbox_environment(log_name_example)

    # assert
    assert result is True


@pytest.mark.parametrize(
    "formal_log_name_example",
    [
        "projects/ons-blaise-v2-dev/logs/stdout",
        "projects/ons-blaise-v2-dev-training/logs/stdout",
        "projects/ons-blaise-v2-preprod/logs/stdout",
        "projects/ons-blaise-v2-prod/logs/stdout",
    ],
)
def test_is_sandbox_environment_returns_false_for_formal_environment(
    formal_log_name_example,
):
    # act
    result = is_sandbox_environment(formal_log_name_example)

    # assert
    assert result is False
