import pytest
import datetime

from lib.log_processor import ProcessedLogEntry
from lib.filters.sandbox_filter import sandbox_filter


@pytest.fixture()
def processed_log_entry() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message='Successfully collected profile HEAP.',
        data={
            'logName': 'projects/ons-blaise-v2-dev-jw09/logs/%40google-cloud%2Fprofiler',
            'resource': {
                'type': 'gae_app',
                'labels': {
                    'version_id': '20231129t144628',
                    'module_id': 'dqs-ui',
                    'zone': 'europe-west2-1'
                }
            },
            'timestamp': '2023-11-29T15:34:54.591Z'
        },
        severity='DEBUG',
        platform='gae_app',
        application='dqs-ui',
        log_name='projects/ons-blaise-v2-dev-jw09/logs/stdout',
        timestamp=datetime.datetime(2023, 11, 29, 15, 34, 54, 591),
        log_query={
            'resource.type': 'gae_app',
            'resource.labels.module_id': 'dqs-ui'
        },
        most_important_values=['status', 'host', 'method', 'resource', 'ip', 'latency', 'responseSize', 'httpVersion'])


def test_log_is_skipped_for_sandbox_environment(
    processed_log_entry: ProcessedLogEntry,
):
    # act
    log_is_skipped = sandbox_filter(processed_log_entry)

    # assert
    assert log_is_skipped is True
