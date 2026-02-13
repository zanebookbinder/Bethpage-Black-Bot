from unittest.mock import patch, MagicMock


class TestLambdaHandler:
    @patch("main.OneTimeLinkHandler")
    @patch("main.BethpageBlackBot")
    @patch("main.ApiGatewayHandler")
    def test_scheduled_event(self, mock_api_cls, mock_bot_cls, mock_otlh_cls):
        from main import lambda_handler

        mock_api_cls.return_value.format_api_response.return_value = {"statusCode": 200, "body": "ok"}
        result = lambda_handler({}, None)
        mock_bot_cls.return_value.notify_if_new_tee_times.assert_called_once()
        mock_otlh_cls.return_value.remove_old_one_time_links.assert_called_once()
        assert result["statusCode"] == 200

    @patch("main.ApiGatewayHandler")
    def test_api_event(self, mock_api_cls):
        from main import lambda_handler

        mock_api_cls.return_value.handle.return_value = {"statusCode": 200, "body": "ok"}
        event = {"routeKey": "GET /test"}
        result = lambda_handler(event, None)
        mock_api_cls.return_value.handle.assert_called_once_with(event)
        assert result["statusCode"] == 200
