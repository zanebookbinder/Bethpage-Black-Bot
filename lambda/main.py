from bethpage_black_bot import BethpageBlackBot
from api_gateway_handler import ApiGatewayHandler
from lambda_helpers.one_time_link_handler import OneTimeLinkHandler


def lambda_handler(event, context):
    # If the event came from API Gateway (HTTP API)
    if "routeKey" in event:
        handler = ApiGatewayHandler()
        response = handler.handle(event)
        return response

    # Otherwise, this is a scheduled or direct invocation
    bot = BethpageBlackBot()
    bot.notify_if_new_tee_times()

    one_time_link_handler = OneTimeLinkHandler()
    one_time_link_handler.remove_old_one_time_links()

    success_message = {"message": "Tee time check completed."}
    return ApiGatewayHandler().get_api_response(success_message, 200)