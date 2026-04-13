import json
import os
import logging
from handlers import health_data_handler

logger = logging.getLogger()
logger.setLevel(logging.INFO)

API_KEY = os.environ.get("DATA_INPUT_API_KEY", "")


def lambda_handler(event, context):
    # Auth check
    headers = event.get("headers") or {}
    provided_key = headers.get("x-api-key") or headers.get("X-Api-Key")
    if not provided_key or provided_key != API_KEY:
        logger.warning("Unauthorized request — bad or missing API key")
        return {"statusCode": 401, "body": json.dumps({"error": "Unauthorized"})}

    # Parse body
    try:
        body = json.loads(event.get("body") or "{}")
    except Exception:
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid JSON body"})}

    # Route by path
    route_key = event.get("routeKey", "")
    logger.info("Received request: %s", route_key)

    if "POST /health-data" in route_key:
        status_code, response_body = health_data_handler.handle(body)
    else:
        status_code, response_body = 404, {"error": f"Unknown route: {route_key}"}

    return {"statusCode": status_code, "body": json.dumps(response_body)}
