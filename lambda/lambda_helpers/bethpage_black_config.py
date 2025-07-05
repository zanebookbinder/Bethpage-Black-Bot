from decimal import Decimal

class BethpageBlackBotConfig:
    def __init__(self, config=None):
        self.earliest_playable_time = "8:00am"
        self.extra_playable_days = ["6/19/2025", "7/4/2025", "9/1/2025"]
        self.include_holidays = True
        self.minimum_minutes_before_sunset = 240
        self.min_players = 2
        self.playable_days_of_week = ["Saturday", "Sunday"]
        self.notifications_enabled = True

        if config:
            self.earliest_playable_time = str(config.get('earliest_playable_time', self.earliest_playable_time))
            self.extra_playable_days = list(config.get('extra_playable_days', self.extra_playable_days))
            self.earliest_playable_time = config.get('earliest_playable_time', self.earliest_playable_time)
            self.include_holidays = bool(config.get('include_holidays', self.include_holidays))
            self.minimum_minutes_before_sunset = self.convert_decimal(config.get('minimum_minutes_before_sunset', self.minimum_minutes_before_sunset))
            self.min_players = self.convert_decimal(config.get("min_players", self.min_players))
            self.playable_days_of_week = list(config.get('playable_days_of_week', self.playable_days_of_week))
            self.notifications_enabled = bool(config.get('notifications_enabled', self.notifications_enabled))

    def config_to_dynamodb_item(self, id="config"):
        return {
            "id": id,
            "earliest_playable_time": self.earliest_playable_time,
            "extra_playable_days": self.extra_playable_days,
            "include_holidays": self.include_holidays,
            "minimum_minutes_before_sunset": self.minimum_minutes_before_sunset,
            "min_players": self.min_players,
            "playable_days_of_week": self.playable_days_of_week,
            "notifications_enabled": self.notifications_enabled
        }
    
    def convert_decimal(self, value):
        # Convert DynamoDB Decimal to int if possible
        if isinstance(value, Decimal):
            if value % 1 == 0:
                return int(value)
            else:
                return float(value)
        return value