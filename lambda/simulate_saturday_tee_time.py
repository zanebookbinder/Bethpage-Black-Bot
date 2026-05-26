"""
Simulate a tee time on this Saturday to trigger a real email to zane.bookbinder@gmail.com.
Mocks only the web scraper and DB state; uses live user config and live SES.
Run from the lambda/ directory: python simulate_saturday_tee_time.py
"""

import logging
from unittest.mock import patch, MagicMock

logging.basicConfig(level=logging.INFO)

SATURDAY = "Saturday May 30th"

SIMULATED_TEE_TIMES = [
    {"Date": SATURDAY, "Time": "8:00AM",  "Players": 4, "Holes": 18},
    {"Date": SATURDAY, "Time": "9:30AM",  "Players": 4, "Holes": 18},
    {"Date": SATURDAY, "Time": "11:00AM", "Players": 4, "Holes": 18},
]


def run():
    with patch("bethpage_black_bot.WebScraper") as mock_scraper_cls, \
         patch("bethpage_black_bot.DynamoDBConnection") as mock_ddc_cls, \
         patch("bethpage_black_bot.TeeTimeFilterer", wraps=None) as mock_filterer_cls:

        # Scraper returns our fake Saturday times
        mock_scraper_cls.return_value.get_tee_time_data.return_value = SIMULATED_TEE_TIMES

        # Wrap a real DynamoDBConnection but override the state methods so the
        # times look "new" and we don't pollute the DB.
        from lambda_helpers.dynamo_db_connection import DynamoDBConnection as RealDDB
        real_ddb = RealDDB()
        real_ddb.get_available_times_by_day = lambda: {}           # nothing seen yet
        real_ddb.update_available_times_by_day = lambda x: None    # don't write
        real_ddb.publish_teetimes = lambda x: None                 # don't write
        mock_ddc_cls.return_value = real_ddb

        # Use the real TeeTimeFilterer with the live DB so user prefs apply
        from lambda_helpers.tee_time_filterer import TeeTimeFilterer as RealFilterer
        mock_filterer_cls.return_value = RealFilterer(db_connection=real_ddb)

        from bethpage_black_bot import BethpageBlackBot
        bot = BethpageBlackBot()
        bot.notify_if_new_tee_times()
        print("Done — check your inbox.")


if __name__ == "__main__":
    run()
