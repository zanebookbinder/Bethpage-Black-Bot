from lambda_late_night.late_night_show_helpers.late_night_show_bot import LateNightShowBot

def lambda_handler(event, context):
    late_night_show_bot = LateNightShowBot()
    late_night_show_bot.notify_if_new_waitlist_opportunities()
    return {"message": "Late night show waitlist check completed."}
