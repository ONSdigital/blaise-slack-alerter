import pytest
import datetime
import dataclasses

from lib.log_processor import ProcessedLogEntry


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
