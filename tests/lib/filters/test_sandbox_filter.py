import pytest
import datetime
import dataclasses

from lib.log_processor.processed_log_entry import ProcessedLogEntry
from lib.filters.sandbox_filter import sandbox_filter


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


@pytest.mark.parametrize(
    "sandbox_log_name_example",
    [
        "projects/ons-blaise-v2-dev-jw09/logs/stdout",
        "projects/ons-blaise-v2-dev-sj02/logs/stdout",
        "projects/ons-blaise-v2-dev-cma/logs/stdout",
        "projects/ons-blaise-v2-dev-foo/logs/stdout",
        "projects/ons-blaise-v2-dev-bar/logs/stdout",
    ],
)
def test_log_is_skipped_for_sandbox_environment(
    processed_log_entry: ProcessedLogEntry, sandbox_log_name_example: str
) -> None:
    # arrange
    processed_sandbox_environment_log_entry = dataclasses.replace(
        processed_log_entry, log_name=sandbox_log_name_example
    )
    # act
    log_is_skipped = sandbox_filter(processed_sandbox_environment_log_entry)

    # assert
    assert log_is_skipped is True


@pytest.mark.parametrize(
    "formal_log_name_example",
    [
        "projects/ons-blaise-v2-dev/logs/stdout",
        "projects/ons-blaise-v2-dev-training/logs/stdout",
        "projects/ons-blaise-v2-preprod/logs/stdout",
        "projects/ons-blaise-v2-prod/logs/stdout",
    ],
)
def test_log_is_not_skipped_for_formal_environment(
    processed_log_entry: ProcessedLogEntry, formal_log_name_example: str
) -> None:
    # arrange
    processed_formal_environment_log_entry = dataclasses.replace(
        processed_log_entry, log_name=formal_log_name_example
    )

    # act
    log_is_skipped = sandbox_filter(processed_formal_environment_log_entry)

    # assert
    assert log_is_skipped is False
