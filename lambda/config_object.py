from typing import List

class BethpaigeBlackBotConfig:
    def __init__(
        self,
        earliest_playable_time: str = "8:00am",
        extra_playable_days: List[str] = ["6/19/2025", "7/3/2025", "7/4/2025", "8/29/2025", "9/1/2025"],
        include_holidays: bool = True,
        minimum_minutes_before_sunset: int = 240,
        min_players: int = 2,
        playable_days_of_week: List[str] = ["Saturday", "Sunday"]
    ):
        self.earliest_playable_time = earliest_playable_time
        self.extra_playable_days = extra_playable_days
        self.include_holidays = include_holidays
        self.minimum_minutes_before_sunset = minimum_minutes_before_sunset
        self.min_players = min_players
        self.playable_days_of_week = playable_days_of_week
        
    def config_to_dynamodb_item(self):
        return {
            "id": {"S": "config"},
            "data": {
                "M": {
                    "earliest_playable_time": {"S": self.earliest_playable_time},
                    "extra_playable_days": {"L": [{"S": d} for d in self.extra_playable_days]},
                    "include_holidays": {"BOOL": self.include_holidays},
                    "minimum_minutes_before_sunset": {"N": str(self.minimum_minutes_before_sunset)},
                    "min_players": {"N": str(self.min_players)},
                    "playable_days_of_week": {"L": [{"S": d} for d in self.playable_days_of_week]},
                }
            }
        }