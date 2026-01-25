from late_night_show_bot import LateNightShowBot
from new_york_cares_bot import NewYorkCaresBot
from central_park_volunteering_bot import CentralParkVolunteeringBot
from daily_update_helpers.daily_updates_email_service import DailyUpdateEmailService


def lambda_handler(event, context):
    # 1) get email response for late night shows
    late_night_bot = LateNightShowBot()
    late_night_html = late_night_bot.scrape_data_and_return_email_html()

    # 2) get email response for new york cares
    nyc_bot = NewYorkCaresBot()
    nyc_html = nyc_bot.scrape_data_and_return_email_html()

    # 3) get central park volunteering
    cp_bot = CentralParkVolunteeringBot()
    cp_html = cp_bot.scrape_data_and_return_email_html()

    # 4) combine and send
    email_service = DailyUpdateEmailService()
    email_service.send_combined_email(
        [late_night_html, nyc_html, cp_html], subject="Zane's Daily Update"
    )

    return {"message": "Zane's Daily Update sent."}


# lambda_handler({}, None)  # For local testing only


# nyc_bot = NewYorkCaresBot()
# nyc_html = nyc_bot.scrape_data_and_return_email_html()
# print(nyc_html)

# cp_bot = CentralParkVolunteeringBot()
# cp_html = cp_bot.scrape_data_and_return_email_html()
# print(cp_html)