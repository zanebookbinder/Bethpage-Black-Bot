from bethpaige_black_bot import BethpageBlackBot
from api_gateway_handler import ApiGatewayHandler

def lambda_handler(event, context):
    # If the event came from API Gateway (HTTP API)
    print(event)
    if "routeKey" in event:
        handler = ApiGatewayHandler()
        response = handler.handle(event)
        return response

    # Otherwise, this is a scheduled or direct invocation
    bot = BethpageBlackBot()
    bot.notify_if_new_tee_times()

    success_message = {"message": "Tee time check completed."}
    return ApiGatewayHandler.get_api_response(success_message)