import zoneinfo
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from lib.utilities.weekly_maintenance_window import \
    is_in_friday_maintenance_window

# Test constants
UK_TZ = zoneinfo.ZoneInfo("Europe/London")
FRIDAY_DATE = datetime(2025, 7, 25, 0, 0, 0, tzinfo=UK_TZ)

# Maintenance window times in UK timezone (Friday 01:25-01:35 UK time)
MAINTENANCE_START_UK = FRIDAY_DATE.replace(hour=1, minute=25, second=0, microsecond=0)
MAINTENANCE_END_UK = FRIDAY_DATE.replace(hour=1, minute=35, second=0, microsecond=0)
MAINTENANCE_MIDDLE_UK = FRIDAY_DATE.replace(hour=1, minute=30, second=0, microsecond=0)


@pytest.fixture
def maintenance_friday() -> datetime:
    return MAINTENANCE_MIDDLE_UK


@pytest.fixture
def non_maintenance_tuesday() -> datetime:
    return datetime(2025, 7, 22, 1, 30, 0, tzinfo=UK_TZ)


def create_datetime_with_offset(base_time: datetime, **kwargs: Any) -> datetime:
    return base_time.replace(**kwargs)


@pytest.mark.parametrize("invalid_input", ["not a datetime", None, 123, [], {}])
def test_returns_false_for_non_datetime_input(invalid_input: Any) -> None:
    assert is_in_friday_maintenance_window(invalid_input) is False


@pytest.mark.parametrize(
    "test_time,expected",
    [
        (MAINTENANCE_START_UK, True),
        (MAINTENANCE_END_UK, True),
        (MAINTENANCE_MIDDLE_UK, True),
        (create_datetime_with_offset(MAINTENANCE_START_UK, minute=27), True),
        (create_datetime_with_offset(MAINTENANCE_START_UK, minute=33), True),
    ],
)
def test_friday_maintenance_window_times(test_time: datetime, expected: bool) -> None:
    assert is_in_friday_maintenance_window(test_time) is expected


@pytest.mark.parametrize(
    "test_time,expected",
    [
        (MAINTENANCE_START_UK.replace(minute=24), False),  # Before window (01:24 UK)
        (
            MAINTENANCE_START_UK.replace(hour=0, minute=30),
            False,
        ),  # Before window (00:30 UK)
        (MAINTENANCE_END_UK.replace(minute=36), False),  # After window (01:36 UK)
        (MAINTENANCE_END_UK.replace(hour=3), False),  # After window (03:35 UK)
    ],
)
def test_friday_outside_maintenance_window(test_time: datetime, expected: bool) -> None:
    assert is_in_friday_maintenance_window(test_time) is expected


@pytest.mark.parametrize("target_weekday", [0, 1, 2, 3, 5, 6])  # Non-Friday weekdays
def test_non_friday_during_maintenance_hours(target_weekday: int) -> None:
    days_difference = target_weekday - 4
    non_friday = MAINTENANCE_MIDDLE_UK + timedelta(days=days_difference)
    assert is_in_friday_maintenance_window(non_friday) is False


@pytest.mark.parametrize(
    "test_time,expected,description",
    [
        (
            datetime(2025, 7, 25, 0, 30, 0, tzinfo=timezone.utc),
            True,
            "Friday 00:30 UTC = Friday 01:30 BST UK (within maintenance window)",
        ),
        (
            datetime(2025, 7, 25, 1, 30, 0, tzinfo=timezone(timedelta(hours=1))),
            True,
            "Friday 01:30+1 = Friday 00:30 UTC = Friday 01:30 BST UK (within maintenance window)",
        ),
        (
            datetime(2025, 7, 25, 1, 30, 0, tzinfo=timezone.utc),
            False,
            "Friday 01:30 UTC = Friday 02:30 BST UK (outside maintenance window)",
        ),
        (
            datetime(2025, 7, 25, 2, 30, 0, tzinfo=timezone(timedelta(hours=-1))),
            False,
            "Friday 02:30-1 = Friday 03:30 UTC = Friday 04:30 BST UK (outside maintenance window)",
        ),
        (
            datetime(2025, 7, 25, 0, 30, 0),
            True,
            "Naive datetime treated as UTC: 00:30 UTC = 01:30 BST UK (within maintenance window)",
        ),
        (
            datetime(2025, 7, 25, 2, 30, 0),
            False,
            "Naive datetime treated as UTC: 02:30 UTC = 03:30 BST UK (outside maintenance window)",
        ),
    ],
)
def test_timezone_conversions(
    test_time: datetime, expected: bool, description: str
) -> None:
    assert is_in_friday_maintenance_window(test_time) is expected


@pytest.mark.parametrize(
    "test_time,expected",
    [
        (MAINTENANCE_START_UK, True),
        (
            MAINTENANCE_START_UK.replace(minute=24, second=59, microsecond=999999),
            False,
        ),
        (
            MAINTENANCE_END_UK.replace(minute=35, second=0, microsecond=1),
            False,
        ),
    ],
)
def test_edge_cases_with_microseconds(test_time: datetime, expected: bool) -> None:
    assert is_in_friday_maintenance_window(test_time) is expected


@pytest.mark.parametrize(
    "month,day,expected_weekday",
    [
        (1, 4, 5),  # Saturday, Jan 4, 2025
        (2, 6, 3),  # Thursday, Feb 6, 2025
        (3, 15, 5),  # Saturday, Mar 15, 2025
        (12, 25, 3),  # Thursday, Dec 25, 2025
    ],
)
def test_different_non_friday_dates(
    month: int, day: int, expected_weekday: int
) -> None:
    non_friday_date = datetime(2025, month, day, 1, 30, 0, tzinfo=UK_TZ)  # UK timezone
    assert non_friday_date.weekday() == expected_weekday
    assert is_in_friday_maintenance_window(non_friday_date) is False


def test_fixtures_work_correctly(
    maintenance_friday: datetime, non_maintenance_tuesday: datetime
) -> None:
    assert is_in_friday_maintenance_window(maintenance_friday) is True
    assert is_in_friday_maintenance_window(non_maintenance_tuesday) is False
