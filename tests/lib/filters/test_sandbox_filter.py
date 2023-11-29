import pytest
import datetime

from lib.log_processor import ProcessedLogEntry
from lib.filters.sandbox_filter import sandbox_filter


@pytest.fixture()
def processed_log_entry() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="Foo",
        data={
            "resource": {
                "type": "gae_app",
                "labels": {
                    "module_id": "dqs-ui",
                    "zone": "europe-west2-1",
                    "project_id": "ons-blaise-v2-dev-jw09",
                    "version_id": "20231129t144628",
                },
            }
        },
        severity="ERROR",
        platform="Bar",
        application="Foobar",
        log_name="barfoo",
        timestamp=datetime.datetime(2023, 2, 25, 3, 46, 57, 99633),
        log_query={
            "foo": "bar",
        },
    )


def test_log_is_skipped_for_sandbox_environment(
    processed_log_entry: ProcessedLogEntry,
):
    # act
    log_is_skipped = sandbox_filter(processed_log_entry)

    # assert
    assert log_is_skipped is True
