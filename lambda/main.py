import logging
from bethpage_black_bot import BethpageBlackBot
from api_gateway_handler import ApiGatewayHandler
from lambda_helpers.one_time_link_handler import OneTimeLinkHandler

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

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

    success_message = {"message": "Tee time check completed."}
    return ApiGatewayHandler().format_api_response(success_message, 200)

# lambda_handler({}, None)  # For local testing only
