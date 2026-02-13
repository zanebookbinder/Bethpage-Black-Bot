import json
from decimal import Decimal
from unittest.mock import patch, MagicMock


def make_handler():
    """Create ApiGatewayHandler with mocked EmailSender."""
    with patch("api_gateway_handler.EmailSender"):
        from api_gateway_handler import ApiGatewayHandler
        return ApiGatewayHandler()


def make_event(method, path, body=None, origin="http://localhost:3000"):
    event = {
        "routeKey": f"{method} {path}",
        "headers": {"origin": origin},
    }
    if body is not None:
        event["body"] = json.dumps(body)
    return event


class TestFormatApiResponse:
    def test_dict_body(self):
        h = make_handler()
        resp = h.format_api_response({"key": "value"}, 200)
        assert resp["statusCode"] == 200
        assert json.loads(resp["body"]) == {"key": "value"}
        assert resp["headers"]["Content-Type"] == "application/json"

    def test_string_body(self):
        h = make_handler()
        resp = h.format_api_response("raw string", 200)
        assert resp["body"] == "raw string"

    def test_status_code(self):
        h = make_handler()
        resp = h.format_api_response({}, 404)
        assert resp["statusCode"] == 404


class TestDecimalDefault:
    def test_whole_decimal(self):
        h = make_handler()
        assert h.decimal_default(Decimal(5)) == 5

    def test_fractional_decimal(self):
        h = make_handler()
        assert h.decimal_default(Decimal("3.14")) == 3.14

    def test_unsupported_type_raises(self):
        h = make_handler()
        import pytest
        with pytest.raises(TypeError):
            h.decimal_default("not a decimal")


class TestOriginValidation:
    def test_invalid_origin_returns_403(self):
        h = make_handler()
        event = make_event("GET", "/getRecentTimes", origin="https://evil.com")
        resp = h.handle(event)
        assert resp["statusCode"] == 403

    def test_valid_localhost_origin(self):
        h = make_handler()
        event = make_event("GET", "/getRecentTimes", origin="http://localhost:3000")
        with patch("api_gateway_handler.DynamoDBConnection") as mock_ddc:
            mock_ddc.return_value.get_latest_tee_times_all.return_value = []
            resp = h.handle(event)
        assert resp["statusCode"] == 200

    def test_valid_prod_origin(self):
        h = make_handler()
        event = make_event("GET", "/getRecentTimes", origin="https://www.bethpage-black-bot.com")
        with patch("api_gateway_handler.DynamoDBConnection") as mock_ddc:
            mock_ddc.return_value.get_latest_tee_times_all.return_value = []
            resp = h.handle(event)
        assert resp["statusCode"] == 200


class TestRoutes:
    def test_get_recent_times(self):
        h = make_handler()
        event = make_event("GET", "/getRecentTimes")
        with patch("api_gateway_handler.DynamoDBConnection") as mock_ddc:
            mock_ddc.return_value.get_latest_tee_times_all.return_value = [{"Time": "8am"}]
            resp = h.handle(event)
        body = json.loads(resp["body"])
        assert body["result"] == [{"Time": "8am"}]

    def test_register(self):
        h = make_handler()
        event = make_event("POST", "/register", body={"email": "a@b.com"})
        with patch("api_gateway_handler.DynamoDBConnection") as mock_ddc, \
             patch("api_gateway_handler.OneTimeLinkHandler") as mock_otlh:
            mock_ddc.return_value.add_email_to_all_emails_list.return_value = (True, "")
            resp = h.handle(event)
        body = json.loads(resp["body"])
        assert body["success"] is True

    def test_register_duplicate(self):
        h = make_handler()
        event = make_event("POST", "/register", body={"email": "a@b.com"})
        with patch("api_gateway_handler.DynamoDBConnection") as mock_ddc:
            mock_ddc.return_value.add_email_to_all_emails_list.return_value = (False, "Email is already in list")
            resp = h.handle(event)
        body = json.loads(resp["body"])
        assert body["success"] is False

    def test_get_user_config_found(self):
        h = make_handler()
        event = make_event("POST", "/getUserConfig", body={"email": "a@b.com"})
        with patch("api_gateway_handler.DynamoDBConnection") as mock_ddc:
            mock_ddc.return_value.get_user_config.return_value = {"id": "a@b.com", "min_players": 2}
            resp = h.handle(event)
        body = json.loads(resp["body"])
        assert body["success"] is True

    def test_get_user_config_not_found(self):
        h = make_handler()
        event = make_event("POST", "/getUserConfig", body={"email": "a@b.com"})
        with patch("api_gateway_handler.DynamoDBConnection") as mock_ddc:
            mock_ddc.return_value.get_user_config.return_value = None
            resp = h.handle(event)
        body = json.loads(resp["body"])
        assert body["success"] is False

    def test_update_user_config(self):
        h = make_handler()
        event = make_event("POST", "/updateUserConfig", body={"email": "a@b.com", "min_players": 3})
        with patch("api_gateway_handler.DynamoDBConnection") as mock_ddc:
            resp = h.handle(event)
        assert resp["statusCode"] == 200

    def test_create_one_time_link(self):
        h = make_handler()
        event = make_event("POST", "/createOneTimeLink", body={"email": "a@b.com"})
        with patch("api_gateway_handler.DynamoDBConnection") as mock_ddc, \
             patch("api_gateway_handler.OneTimeLinkHandler") as mock_otlh:
            mock_ddc.return_value.get_user_config.return_value = {"id": "a@b.com"}
            resp = h.handle(event)
        body = json.loads(resp["body"])
        assert body["success"] is True

    def test_create_one_time_link_user_not_found(self):
        h = make_handler()
        event = make_event("POST", "/createOneTimeLink", body={"email": "unknown@b.com"})
        with patch("api_gateway_handler.DynamoDBConnection") as mock_ddc:
            mock_ddc.return_value.get_user_config.return_value = None
            resp = h.handle(event)
        body = json.loads(resp["body"])
        assert body["success"] is False

    def test_validate_one_time_link_valid(self):
        h = make_handler()
        event = make_event("POST", "/validateOneTimeLink", body={"guid": "abc-123"})
        with patch("api_gateway_handler.OneTimeLinkHandler") as mock_otlh:
            mock_otlh.return_value.validate_one_time_link_and_get_email.return_value = (True, "a@b.com")
            resp = h.handle(event)
        body = json.loads(resp["body"])
        assert body["email"] == "a@b.com"

    def test_validate_one_time_link_invalid(self):
        h = make_handler()
        event = make_event("POST", "/validateOneTimeLink", body={"guid": "bad"})
        with patch("api_gateway_handler.OneTimeLinkHandler") as mock_otlh:
            mock_otlh.return_value.validate_one_time_link_and_get_email.return_value = (False, "Expired")
            resp = h.handle(event)
        body = json.loads(resp["body"])
        assert body["errorMessage"] == "Expired"

    def test_unknown_route(self):
        h = make_handler()
        event = make_event("DELETE", "/nonexistent")
        resp = h.handle(event)
        assert resp["statusCode"] == 404
