from datetime import datetime, date, time
from unittest.mock import patch, MagicMock
from lambda_helpers.bethpage_black_config import BethpageBlackBotConfig


def make_filterer():
    """Create a TeeTimeFilterer with mocked DynamoDB."""
    with patch("lambda_helpers.tee_time_filterer.DynamoDBConnection"):
        from lambda_helpers.tee_time_filterer import TeeTimeFilterer
        return TeeTimeFilterer()


class TestParseDateString:
    def test_basic(self):
        f = make_filterer()
        day_of_week, date_obj = f.parse_date_string("Saturday May 27th")
        assert day_of_week == "Saturday"
        assert date_obj.month == 5
        assert date_obj.day == 27

    def test_no_suffix(self):
        f = make_filterer()
        day_of_week, date_obj = f.parse_date_string("Monday June 1")
        assert day_of_week == "Monday"
        assert date_obj.month == 6
        assert date_obj.day == 1


class TestIsPlayableDay:
    def setup_method(self):
        self.f = make_filterer()

    def test_matching_day_of_week(self):
        config = BethpageBlackBotConfig({"playable_days_of_week": ["Saturday"]})
        assert self.f.is_playable_day(config, "Saturday", date(2026, 3, 14)) is True

    def test_non_matching_day_of_week(self):
        config = BethpageBlackBotConfig({"playable_days_of_week": ["Saturday"]})
        assert self.f.is_playable_day(config, "Monday", date(2026, 3, 16)) is False

    def test_extra_playable_day(self):
        config = BethpageBlackBotConfig({
            "playable_days_of_week": [],
            "extra_playable_days": ["3/16/2026"],
        })
        assert self.f.is_playable_day(config, "Monday", date(2026, 3, 16)) is True

    def test_holiday(self):
        config = BethpageBlackBotConfig({
            "playable_days_of_week": [],
            "include_holidays": True,
        })
        # July 4 is a real US holiday — now matched correctly after the format fix
        assert self.f.is_playable_day(config, "Saturday", date(2026, 7, 4)) is True

    def test_holiday_disabled(self):
        config = BethpageBlackBotConfig({
            "playable_days_of_week": [],
            "include_holidays": False,
        })
        assert self.f.is_playable_day(config, "Saturday", date(2026, 7, 4)) is False


class TestIsAfterEarliestAcceptableTime:
    def setup_method(self):
        self.f = make_filterer()

    def test_after(self):
        config = BethpageBlackBotConfig({"earliest_playable_time": "8:00am"})
        assert self.f.is_after_earliest_acceptable_time(config, time(9, 0)) is True

    def test_before(self):
        config = BethpageBlackBotConfig({"earliest_playable_time": "8:00am"})
        assert self.f.is_after_earliest_acceptable_time(config, time(7, 0)) is False

    def test_equal_returns_false(self):
        config = BethpageBlackBotConfig({"earliest_playable_time": "8:00am"})
        assert self.f.is_after_earliest_acceptable_time(config, time(8, 0)) is False


class TestIsFarEnoughBeforeSunset:
    def setup_method(self):
        self.f = make_filterer()

    def test_well_before_sunset(self):
        config = BethpageBlackBotConfig({"minimum_minutes_before_sunset": 240})
        # Early morning is definitely before sunset - 4 hours
        assert self.f.is_far_enough_before_sunset(config, date(2026, 6, 21), time(8, 0)) is True

    def test_too_close_to_sunset(self):
        config = BethpageBlackBotConfig({"minimum_minutes_before_sunset": 240})
        # Late evening is too close to sunset
        assert self.f.is_far_enough_before_sunset(config, date(2026, 6, 21), time(20, 0)) is False


class TestRemoveExistingTeeTimes:
    def setup_method(self):
        self.f = make_filterer()

    def test_removes_duplicates(self):
        existing = [{"Date": "Sat", "Time": "8:00am", "Players": "2", "Holes": "18"}]
        current = [
            {"Date": "Sat", "Time": "8:00am", "Players": "2", "Holes": "18"},
            {"Date": "Sat", "Time": "9:00am", "Players": "3", "Holes": "18"},
        ]
        result = self.f.remove_existing_tee_times(current, existing)
        assert len(result) == 1
        assert result[0]["Time"] == "9:00am"

    def test_empty_existing(self):
        current = [{"Date": "Sat", "Time": "8:00am", "Players": "2", "Holes": "18"}]
        result = self.f.remove_existing_tee_times(current, [])
        assert result == current

    def test_none_existing(self):
        current = [{"Date": "Sat", "Time": "8:00am", "Players": "2", "Holes": "18"}]
        result = self.f.remove_existing_tee_times(current, None)
        assert result == current

    def test_all_overlap(self):
        items = [{"Date": "Sat", "Time": "8:00am", "Players": "2", "Holes": "18"}]
        result = self.f.remove_existing_tee_times(items, items)
        assert result == []


class TestFilterTeeTimesForUser:
    def test_filters_by_all_criteria(self):
        f = make_filterer()
        config = BethpageBlackBotConfig({
            "playable_days_of_week": ["Saturday"],
            "earliest_playable_time": "7:00am",
            "minimum_minutes_before_sunset": 60,
            "min_players": 2,
            "notifications_enabled": True,
        })

        f.db_table = MagicMock()
        f.db_table.get_user_config.return_value = config.config_to_dynamodb_item("user@test.com")

        tee_times = [
            # Good: Saturday, 9am, 3 players, 18 holes
            {"Date": "Saturday June 20th", "Time": "9:00am", "Players": "3", "Holes": "18"},
            # Bad: 9 holes
            {"Date": "Saturday June 20th", "Time": "9:00am", "Players": "3", "Holes": "9"},
            # Bad: 1 player
            {"Date": "Saturday June 20th", "Time": "9:00am", "Players": "1", "Holes": "18"},
        ]

        result = f.filter_tee_times_for_user(tee_times, "user@test.com")
        assert len(result) == 1
        assert result[0]["Players"] == "3"
        assert result[0]["Holes"] == "18"

    def test_notifications_disabled_returns_empty(self):
        f = make_filterer()
        config = BethpageBlackBotConfig({"notifications_enabled": False})

        f.db_table = MagicMock()
        f.db_table.get_user_config.return_value = config.config_to_dynamodb_item("user@test.com")

        tee_times = [{"Date": "Saturday June 20th", "Time": "9:00am", "Players": "3", "Holes": "18"}]
        result = f.filter_tee_times_for_user(tee_times, "user@test.com")
        assert result == []
