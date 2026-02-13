import logging
from late_night_show_bot import LateNightShowBot
from new_york_cares_bot import NewYorkCaresBot
from central_park_public_volunteering_bot import CentralParkPublicVolunteeringBot
from central_park_private_volunteering_bot import CentralParkPrivateVolunteeringBot
from daily_update_helpers.daily_updates_email_service import DailyUpdateEmailService

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info("Starting daily update process")
    # 1) get email response for late night shows
    late_night_bot = LateNightShowBot()
    late_night_html = late_night_bot.scrape_data_and_return_email_html()

    # 2) get email response for new york cares
    nyc_bot = NewYorkCaresBot()
    nyc_html = nyc_bot.scrape_data_and_return_email_html()

    # 3) get central park public volunteering
    cp_public_bot = CentralParkPublicVolunteeringBot()
    cp_public_html = cp_public_bot.scrape_data_and_return_email_html()

    # 4) get central park private volunteering (MyImpactPage)
    cp_private_bot = CentralParkPrivateVolunteeringBot()
    cp_private_html = cp_private_bot.scrape_data_and_return_email_html()

    # 5) combine and send
    email_service = DailyUpdateEmailService()
    email_service.send_combined_email(
        [late_night_html, nyc_html, cp_public_html, cp_private_html],
        subject="Zane's Daily Update",
    )

    logger.info("Daily update process completed successfully")
    return {"message": "Zane's Daily Update sent."}


# lambda_handler({}, None)  # For local testing only


# nyc_bot = NewYorkCaresBot()
# nyc_html = nyc_bot.scrape_data_and_return_email_html()
# print(nyc_html)

# cp_bot = CentralParkPublicVolunteeringBot()
# cp_html = cp_bot.scrape_data_and_return_email_html()
# print(cp_html)
