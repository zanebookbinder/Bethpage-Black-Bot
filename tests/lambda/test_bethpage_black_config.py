from decimal import Decimal
from lambda_helpers.bethpage_black_config import BethpageBlackBotConfig


class TestDefaults:
    def test_default_values(self):
        config = BethpageBlackBotConfig()
        assert config.earliest_playable_time == "8:00am"
        assert config.extra_playable_days == []
        assert config.include_holidays is True
        assert config.minimum_minutes_before_sunset == 240
        assert config.min_players == 2
        assert config.playable_days_of_week == ["Saturday", "Sunday"]
        assert config.notifications_enabled is True


class TestFromDict:
    def test_custom_values(self):
        config = BethpageBlackBotConfig({
            "earliest_playable_time": "7:00am",
            "extra_playable_days": ["6/20/2026"],
            "include_holidays": False,
            "minimum_minutes_before_sunset": Decimal(180),
            "min_players": Decimal(3),
            "playable_days_of_week": ["Friday", "Saturday"],
            "notifications_enabled": False,
        })
        assert config.earliest_playable_time == "7:00am"
        assert config.extra_playable_days == ["6/20/2026"]
        assert config.include_holidays is False
        assert config.minimum_minutes_before_sunset == 180
        assert config.min_players == 3
        assert config.playable_days_of_week == ["Friday", "Saturday"]
        assert config.notifications_enabled is False

    def test_partial_config_uses_defaults(self):
        config = BethpageBlackBotConfig({"min_players": 4})
        assert config.min_players == 4
        assert config.earliest_playable_time == "8:00am"


class TestConvertDecimal:
    def setup_method(self):
        self.config = BethpageBlackBotConfig()

    def test_whole_decimal(self):
        assert self.config.convert_decimal(Decimal(5)) == 5
        assert isinstance(self.config.convert_decimal(Decimal(5)), int)

    def test_fractional_decimal(self):
        assert self.config.convert_decimal(Decimal("5.5")) == 5.5
        assert isinstance(self.config.convert_decimal(Decimal("5.5")), float)

    def test_plain_int(self):
        assert self.config.convert_decimal(3) == 3

    def test_plain_float(self):
        assert self.config.convert_decimal(3.5) == 3.5


class TestConfigToDynamoDbItem:
    def test_default_item(self):
        config = BethpageBlackBotConfig()
        item = config.config_to_dynamodb_item("user@test.com")
        assert item["id"] == "user@test.com"
        assert item["earliest_playable_time"] == "8:00am"
        assert item["min_players"] == 2
        assert item["notifications_enabled"] is True

    def test_default_id(self):
        config = BethpageBlackBotConfig()
        item = config.config_to_dynamodb_item()
        assert item["id"] == "config"
