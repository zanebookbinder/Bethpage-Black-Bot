import logging
from late_night_show_bot import LateNightShowBot
from new_york_cares_bot import NewYorkCaresBot
from central_park_public_volunteering_bot import CentralParkPublicVolunteeringBot
from central_park_private_volunteering_bot import CentralParkPrivateVolunteeringBot
from nyc_tennis_bot import NycTennisBot
from health_data_bot import HealthDataBot
from daily_update_helpers.daily_updates_email_service import DailyUpdateEmailService

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _run_bot(name, bot_fn):
    try:
        return bot_fn()
    except Exception as e:
        logger.error("Bot %s failed: %s", name, str(e), exc_info=True)
        return f"<p><strong>{name} failed to load.</strong></p>"


def lambda_handler(event, context):
    logger.info("Starting daily update process")
    late_night_bot = LateNightShowBot()
    late_night_html = _run_bot("LateNightShowBot", late_night_bot.scrape_data_and_return_email_html)

    nyc_bot = NewYorkCaresBot()
    nyc_html = _run_bot("NewYorkCaresBot", nyc_bot.scrape_data_and_return_email_html)

    cp_public_bot = CentralParkPublicVolunteeringBot()
    cp_public_html = _run_bot("CentralParkPublicVolunteeringBot", cp_public_bot.scrape_data_and_return_email_html)

    cp_private_bot = CentralParkPrivateVolunteeringBot()
    cp_private_html = _run_bot("CentralParkPrivateVolunteeringBot", cp_private_bot.scrape_data_and_return_email_html)

    tennis_bot = NycTennisBot()
    tennis_html = _run_bot("NycTennisBot", tennis_bot.scrape_data_and_return_email_html)

    health_bot = HealthDataBot()
    health_html = _run_bot("HealthDataBot", health_bot.scrape_data_and_return_email_html)

    # 7) combine and send
    email_service = DailyUpdateEmailService()
    email_service.send_combined_email(
        [tennis_html, late_night_html, nyc_html, cp_public_html, cp_private_html, health_html],
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

# health_bot = HealthDataBot()
# health_html = health_bot.scrape_data_and_return_email_html()
# print(health_html)