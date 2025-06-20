
class BethpageBlackBotConfig:
    def __init__(self, config=None):
        self.earliest_playable_time = "8:00am",
        self.extra_playable_days = ["6/19/2025", "7/4/2025", "9/1/2025"],
        self.include_holidays = True,
        self.minimum_minutes_before_sunset = 240,
        self.min_players = 2,
        self.playable_days_of_week = ["Saturday", "Sunday"]

        if config:
            self.earliest_playable_time = config.get('earliest_playable_time') or self.earliest_playable_time
            self.extra_playable_days = config.get('extra_playable_days') or self.extra_playable_days
            self.earliest_playable_time = config.get('earliest_playable_time') or self.earliest_playable_time
            self.include_holidays = config.get('include_holidays') or self.include_holidays
            self.minimum_minutes_before_sunset = config.get('minimum_minutes_before_sunset') or self.minimum_minutes_before_sunset
            self.playable_days_of_week = config.get('playable_days_of_week') or self.playable_days_of_week

    def config_to_dynamodb_item(self, id="config"):
        return {
            "id": id,
            "earliest_playable_time": self.earliest_playable_time,
            "extra_playable_days": self.extra_playable_days,
            "include_holidays": self.include_holidays,
            "minimum_minutes_before_sunset": self.minimum_minutes_before_sunset,
            "min_players": self.min_players,
            "playable_days_of_week": self.playable_days_of_week,
        }

    def config_to_dynamodb_item_low_level(self, id="config"):
        return {
            "id": {"S": id},
            "earliest_playable_time": {"S": self.earliest_playable_time},
            "extra_playable_days": {"L": [{"S": d} for d in self.extra_playable_days]},
            "include_holidays": {"BOOL": self.include_holidays},
            "minimum_minutes_before_sunset": {"N": str(self.minimum_minutes_before_sunset)},
            "min_players": {"N": str(self.min_players)},
            "playable_days_of_week": {"L": [{"S": d} for d in self.playable_days_of_week]},
        }