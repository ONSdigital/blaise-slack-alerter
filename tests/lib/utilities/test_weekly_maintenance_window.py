import pytest
from datetime import datetime, timezone, timedelta

from lib.utilities.weekly_maintenance_window import is_in_weekly_maintenance_window


class TestIsInWeeklyMaintenanceWindow:
    def test_returns_false_for_non_datetime_input(self):
        assert is_in_weekly_maintenance_window("not a datetime") is False
        assert is_in_weekly_maintenance_window(None) is False
        assert is_in_weekly_maintenance_window(123) is False
        assert is_in_weekly_maintenance_window([]) is False

    def test_returns_true_for_friday_maintenance_window_start(self):
        friday_start = datetime(2025, 7, 25, 1, 0, 0, tzinfo=timezone.utc)
        assert is_in_weekly_maintenance_window(friday_start) is True

    def test_returns_true_for_friday_maintenance_window_end(self):
        friday_end = datetime(2025, 7, 25, 2, 0, 0, tzinfo=timezone.utc)
        assert is_in_weekly_maintenance_window(friday_end) is True

    def test_returns_true_for_friday_during_maintenance_window(self):
        friday_middle = datetime(2025, 7, 25, 1, 30, 0, tzinfo=timezone.utc)
        assert is_in_weekly_maintenance_window(friday_middle) is True

        friday_quarter = datetime(2025, 7, 25, 1, 15, 0, tzinfo=timezone.utc)
        assert is_in_weekly_maintenance_window(friday_quarter) is True

        friday_three_quarter = datetime(2025, 7, 25, 1, 45, 0, tzinfo=timezone.utc)
        assert is_in_weekly_maintenance_window(friday_three_quarter) is True

    def test_returns_false_for_friday_before_maintenance_window(self):
        friday_before = datetime(2025, 7, 25, 0, 59, 0, tzinfo=timezone.utc)
        assert is_in_weekly_maintenance_window(friday_before) is False

        friday_early = datetime(2025, 7, 25, 0, 30, 0, tzinfo=timezone.utc)
        assert is_in_weekly_maintenance_window(friday_early) is False

    def test_returns_false_for_friday_after_maintenance_window(self):
        friday_after = datetime(2025, 7, 25, 2, 1, 0, tzinfo=timezone.utc)
        assert is_in_weekly_maintenance_window(friday_after) is False

        friday_late = datetime(2025, 7, 25, 3, 0, 0, tzinfo=timezone.utc)
        assert is_in_weekly_maintenance_window(friday_late) is False

    def test_returns_false_for_non_friday_during_maintenance_hours(self):
        monday = datetime(2025, 7, 21, 1, 30, 0, tzinfo=timezone.utc)
        assert is_in_weekly_maintenance_window(monday) is False

        tuesday = datetime(2025, 7, 22, 1, 30, 0, tzinfo=timezone.utc)
        assert is_in_weekly_maintenance_window(tuesday) is False

        wednesday = datetime(2025, 7, 23, 1, 30, 0, tzinfo=timezone.utc)
        assert is_in_weekly_maintenance_window(wednesday) is False

        thursday = datetime(2025, 7, 24, 1, 30, 0, tzinfo=timezone.utc)
        assert is_in_weekly_maintenance_window(thursday) is False

        saturday = datetime(2025, 7, 26, 1, 30, 0, tzinfo=timezone.utc)
        assert is_in_weekly_maintenance_window(saturday) is False

        sunday = datetime(2025, 7, 27, 1, 30, 0, tzinfo=timezone.utc)
        assert is_in_weekly_maintenance_window(sunday) is False

    def test_works_with_different_timezones(self):
        # Friday 01:30 UTC - should be in maintenance window
        utc_time = datetime(2025, 7, 25, 1, 30, 0, tzinfo=timezone.utc)
        assert is_in_weekly_maintenance_window(utc_time) is True
        
        # 02:30 with +1 hour offset (like London BST) = 01:30 UTC
        london_offset = datetime(2025, 7, 25, 2, 30, 0, tzinfo=timezone(timedelta(hours=1)))
        assert is_in_weekly_maintenance_window(london_offset) is True
        
        # 21:30 previous day with -4 hour offset (like New York EDT) = 01:30 UTC Friday
        ny_offset = datetime(2025, 7, 24, 21, 30, 0, tzinfo=timezone(timedelta(hours=-4)))
        assert is_in_weekly_maintenance_window(ny_offset) is True
        
        # 06:30 with +5 hour offset = 01:30 UTC
        india_offset = datetime(2025, 7, 25, 6, 30, 0, tzinfo=timezone(timedelta(hours=5)))
        assert is_in_weekly_maintenance_window(india_offset) is True
        
        # 01:30 with -2 hour offset = 03:30 UTC (outside window)
        outside_window = datetime(2025, 7, 25, 1, 30, 0, tzinfo=timezone(timedelta(hours=-2)))
        assert is_in_weekly_maintenance_window(outside_window) is False

    def test_naive_datetime_treated_as_utc(self):
        naive_friday = datetime(2025, 7, 25, 1, 30, 0)
        assert is_in_weekly_maintenance_window(naive_friday) is True

        naive_friday_early = datetime(2025, 7, 25, 0, 30, 0)
        assert is_in_weekly_maintenance_window(naive_friday_early) is False

    def test_edge_cases_with_microseconds(self):
        friday_exact_start = datetime(2025, 7, 25, 1, 0, 0, 0, tzinfo=timezone.utc)
        assert is_in_weekly_maintenance_window(friday_exact_start) is True

        friday_exact_end = datetime(2025, 7, 25, 2, 0, 0, 0, tzinfo=timezone.utc)
        assert is_in_weekly_maintenance_window(friday_exact_end) is True

        friday_just_before = datetime(2025, 7, 25, 0, 59, 59, 999999, tzinfo=timezone.utc)
        assert is_in_weekly_maintenance_window(friday_just_before) is False

        friday_just_after = datetime(2025, 7, 25, 2, 0, 0, 1, tzinfo=timezone.utc)
        assert is_in_weekly_maintenance_window(friday_just_after) is False

    def test_different_friday_dates(self):
        friday_dates = [
            datetime(2025, 1, 3, 1, 30, 0, tzinfo=timezone.utc),   # Friday, Jan 3, 2025
            datetime(2025, 2, 7, 1, 30, 0, tzinfo=timezone.utc),   # Friday, Feb 7, 2025
            datetime(2025, 3, 14, 1, 30, 0, tzinfo=timezone.utc),  # Friday, Mar 14, 2025
            datetime(2025, 12, 26, 1, 30, 0, tzinfo=timezone.utc), # Friday, Dec 26, 2025
        ]

        for friday_date in friday_dates:
            assert friday_date.weekday() == 4, f"Date {friday_date} should be a Friday"
            assert is_in_weekly_maintenance_window(friday_date) is True

    def test_different_non_friday_dates(self):
        non_friday_dates = [
            datetime(2025, 1, 4, 1, 30, 0, tzinfo=timezone.utc),   # Saturday, Jan 4, 2025
            datetime(2025, 2, 6, 1, 30, 0, tzinfo=timezone.utc),   # Thursday, Feb 6, 2025
            datetime(2025, 3, 15, 1, 30, 0, tzinfo=timezone.utc),  # Saturday, Mar 15, 2025
            datetime(2025, 12, 25, 1, 30, 0, tzinfo=timezone.utc), # Thursday, Dec 25, 2025
        ]

        for non_friday_date in non_friday_dates:
            assert non_friday_date.weekday() != 4, f"Date {non_friday_date} should not be a Friday"
            assert is_in_weekly_maintenance_window(non_friday_date) is False

    def test_timezone_conversion_changes_weekday(self):
        # Thursday 23:30 with -2 hour offset = Friday 01:30 UTC (should be True)
        thursday_becomes_friday = datetime(2025, 7, 24, 23, 30, 0, tzinfo=timezone(timedelta(hours=-2)))
        assert is_in_weekly_maintenance_window(thursday_becomes_friday) is True
        
        # Friday 02:30 with +2 hour offset = Friday 00:30 UTC (should be False - outside window)
        friday_stays_friday_but_outside = datetime(2025, 7, 25, 2, 30, 0, tzinfo=timezone(timedelta(hours=2)))
        assert is_in_weekly_maintenance_window(friday_stays_friday_but_outside) is False
        
        # Saturday 01:30 with +1 hour offset = Friday 00:30 UTC (should be False - outside window)
        saturday_becomes_friday_outside = datetime(2025, 7, 26, 1, 30, 0, tzinfo=timezone(timedelta(hours=1)))
        assert is_in_weekly_maintenance_window(saturday_becomes_friday_outside) is False
