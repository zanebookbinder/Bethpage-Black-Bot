import logging
from astral.sun import sun
from astral import LocationInfo
from datetime import datetime, timedelta
from lambda_helpers.date_handler import DateHandler
import holidays
from lambda_helpers.dynamo_db_connection import DynamoDBConnection
from lambda_helpers.bethpage_black_config import BethpageBlackBotConfig

logger = logging.getLogger(__name__)


class TeeTimeFilterer:

    def __init__(self, db_connection=None):
        try:
            self.db_table = db_connection if db_connection else DynamoDBConnection()

            self.bethpage_info = LocationInfo(
                "Farmingdale", "USA", "America/New_York", 40.7326, -73.4457
            )
            us_holidays = holidays.UnitedStates(years=datetime.now().year)
            self.holiday_dates = {
                f"{date.month}/{date.day}/{date.year}"
                for date, name in us_holidays.items()
                if "Veterans Day" not in name
            }
            self.date_handler = DateHandler()
        except Exception as e:
            logger.error("Error initializing TeeTimeFilterer: %s", str(e), exc_info=True)
            raise e

    def filter_tee_times_for_user(self, tee_times_to_consider, user_email):
        logger.debug("Filtering %d tee times for user: %s", len(tee_times_to_consider), user_email)
        user_config = self.get_user_config_as_object(user_email)

        if not user_config.notifications_enabled:
            logger.debug("User %s has notifications disabled", user_email)
            return []

        filtered_tee_times = []

        for tee_time in tee_times_to_consider:
            day_of_week, date_obj = self.parse_date_string(tee_time["Date"])

            is_playable_day = self.is_playable_day(user_config, day_of_week, date_obj)

            tee_time_of_day = datetime.strptime(tee_time["Time"], "%I:%M%p").time()
            is_acceptable_time = self.is_far_enough_before_sunset(
                user_config, date_obj, tee_time_of_day
            ) and self.is_after_earliest_acceptable_time(user_config, tee_time_of_day)

            hits_min_players = int(tee_time["Players"]) >= user_config.min_players

            has_18_holes = tee_time["Holes"] == 18 or tee_time["Holes"] == "18"

            if (
                is_playable_day
                and is_acceptable_time
                and hits_min_players
                and has_18_holes
            ):
                filtered_tee_times.append(tee_time)

        logger.debug("Filtered to %d tee times for user %s", len(filtered_tee_times), user_email)
        return filtered_tee_times

    def is_after_earliest_acceptable_time(self, user_config, time_of_day):
        earliest_playable_time_as_dt = datetime.strptime(
            user_config.earliest_playable_time, "%I:%M%p"
        ).time()
        return time_of_day > earliest_playable_time_as_dt

    def is_far_enough_before_sunset(self, user_config, date_obj, time_of_day):
        sunset_time = sun(
            self.bethpage_info.observer,
            date=date_obj,
            tzinfo=self.bethpage_info.timezone,
        )["sunset"]
        before_sunset_dt = sunset_time - timedelta(
            minutes=user_config.minimum_minutes_before_sunset
        )

        return time_of_day < before_sunset_dt.time()

    def parse_date_string(self, date_str):
        parts = date_str.split()
        day_of_week = parts[0]
        month = parts[1]
        day = self.date_handler.strip_ordinal_suffix(parts[2])

        year = datetime.now().year

        # Parse to datetime object
        date_obj = datetime.strptime(f"{month} {day} {year}", "%B %d %Y").date()
        return day_of_week, date_obj

    def get_day_of_week_from_str(self, date_str):
        return date_str.split()[0]

    def is_playable_day(self, user_config, day_of_week, date_obj):
        is_playable_day_of_week = day_of_week in user_config.playable_days_of_week

        formatted = f"{date_obj.month}/{date_obj.day}/{date_obj.year}"
        is_extra_day_to_notify = formatted in user_config.extra_playable_days

        is_us_holiday = (
            formatted in self.holiday_dates if user_config.include_holidays else False
        )

        return is_playable_day_of_week or is_extra_day_to_notify or is_us_holiday

    def get_user_config_as_object(self, user_email):
        config_data = self.db_table.get_user_config(user_email)
        return BethpageBlackBotConfig(config_data)

    def remove_existing_tee_times(self, times_from_site, existing_times):
        if existing_times:
            existing_times_set = set(
                tuple(sorted(item.items())) for item in existing_times
            )

            new_times = [
                item
                for item in times_from_site
                if tuple(sorted(item.items())) not in existing_times_set
            ]
        else:
            logger.debug("No existing times in database, all times are new")
            new_times = times_from_site

        logger.debug("Found %d new times after diff", len(new_times))
        return new_times


# t = TeeTimeFilterer()
# d = [{"Date": "Saturday November 22nd", "Time": "12:40pm", "Players": 2, "Holes": '9'}]
# t.filter_tee_times_for_user(d, "zane.bookbinder@gmail.com")
