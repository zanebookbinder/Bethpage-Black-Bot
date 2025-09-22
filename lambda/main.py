from bethpage_black_bot import BethpageBlackBot
from api_gateway_handler import ApiGatewayHandler
from lambda_helpers.one_time_link_handler import OneTimeLinkHandler
from late_night_show_bot import LateNightShowBot

def lambda_handler(event, context):
    # If the event came from API Gateway (HTTP API)
    if "routeKey" in event:
        handler = ApiGatewayHandler()
        response = handler.handle(event)
        return response

    # Otherwise, this is a scheduled or direct invocation
    bot = BethpageBlackBot()
    bot.notify_if_new_tee_times()

    # remove old one time links
    one_time_link_handler = OneTimeLinkHandler()
    one_time_link_handler.remove_old_one_time_links()

    # totally unrelated to Bethpage Black, I just separately wanted to get
    # late night show tickets in NYC :)
    late_night_show_bot = LateNightShowBot()
    late_night_show_bot.notify_if_new_waitlist_opportunities()

    success_message = {"message": "Tee time check completed."}
    return ApiGatewayHandler().format_api_response(success_message, 200)
