from unittest.mock import patch, MagicMock


class TestDailyUpdateLambdaHandler:
    @patch("daily_update_lambda.DailyUpdateEmailService")
    @patch("daily_update_lambda.CentralParkPrivateVolunteeringBot")
    @patch("daily_update_lambda.CentralParkPublicVolunteeringBot")
    @patch("daily_update_lambda.NewYorkCaresBot")
    @patch("daily_update_lambda.LateNightShowBot")
    def test_calls_all_bots_and_sends_email(
        self, mock_ln, mock_nyc, mock_cp_pub, mock_cp_priv, mock_email
    ):
        from daily_update_lambda import lambda_handler

        mock_ln.return_value.scrape_data_and_return_email_html.return_value = "<html>ln</html>"
        mock_nyc.return_value.scrape_data_and_return_email_html.return_value = "<html>nyc</html>"
        mock_cp_pub.return_value.scrape_data_and_return_email_html.return_value = "<html>cp_pub</html>"
        mock_cp_priv.return_value.scrape_data_and_return_email_html.return_value = "<html>cp_priv</html>"

        result = lambda_handler({}, None)

        mock_ln.return_value.scrape_data_and_return_email_html.assert_called_once()
        mock_nyc.return_value.scrape_data_and_return_email_html.assert_called_once()
        mock_cp_pub.return_value.scrape_data_and_return_email_html.assert_called_once()
        mock_cp_priv.return_value.scrape_data_and_return_email_html.assert_called_once()
        mock_email.return_value.send_combined_email.assert_called_once()
        assert "message" in result

    @patch("daily_update_lambda.DailyUpdateEmailService")
    @patch("daily_update_lambda.CentralParkPrivateVolunteeringBot")
    @patch("daily_update_lambda.CentralParkPublicVolunteeringBot")
    @patch("daily_update_lambda.NewYorkCaresBot")
    @patch("daily_update_lambda.LateNightShowBot")
    def test_passes_html_pieces_to_email(
        self, mock_ln, mock_nyc, mock_cp_pub, mock_cp_priv, mock_email
    ):
        from daily_update_lambda import lambda_handler

        mock_ln.return_value.scrape_data_and_return_email_html.return_value = "A"
        mock_nyc.return_value.scrape_data_and_return_email_html.return_value = "B"
        mock_cp_pub.return_value.scrape_data_and_return_email_html.return_value = "C"
        mock_cp_priv.return_value.scrape_data_and_return_email_html.return_value = "D"

        lambda_handler({}, None)

        call_args = mock_email.return_value.send_combined_email.call_args
        pieces = call_args[0][0]
        assert pieces == ["A", "B", "C", "D"]
