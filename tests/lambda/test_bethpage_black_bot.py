from unittest.mock import patch, MagicMock


class TestGetNewTeeTimes:
    @patch("bethpage_black_bot.TeeTimeFilterer")
    @patch("bethpage_black_bot.DynamoDBConnection")
    @patch("bethpage_black_bot.WebScraper")
    @patch("bethpage_black_bot.SecretHandler")
    def test_returns_new_times_map(self, mock_secret, mock_scraper_cls, mock_ddc_cls, mock_filterer_cls):
        from bethpage_black_bot import BethpageBlackBot

        mock_scraper = mock_scraper_cls.return_value
        mock_ddc = mock_ddc_cls.return_value
        mock_filterer = mock_filterer_cls.return_value

        all_times = [
            {"Date": "Sat", "Time": "8:00am", "Players": "3", "Holes": "18"},
            {"Date": "Sat", "Time": "9:00am", "Players": "2", "Holes": "18"},
        ]
        mock_scraper.get_tee_time_data.return_value = all_times
        mock_ddc.get_all_emails_list.return_value = ["a@b.com"]
        mock_ddc.get_latest_filtered_tee_times.return_value = {}

        mock_filterer.filter_tee_times_for_user.return_value = [all_times[0]]
        mock_filterer.remove_existing_tee_times.return_value = [all_times[0]]

        bot = BethpageBlackBot()
        bot.bethpage_email = "user"
        bot.bethpage_password = "pass"
        result = bot.get_new_tee_times()

        assert "a@b.com" in result
        assert len(result["a@b.com"]) == 1
        mock_ddc.publish_teetimes.assert_called_once()

    @patch("bethpage_black_bot.TeeTimeFilterer")
    @patch("bethpage_black_bot.DynamoDBConnection")
    @patch("bethpage_black_bot.WebScraper")
    @patch("bethpage_black_bot.SecretHandler")
    def test_empty_new_times_not_included(self, mock_secret, mock_scraper_cls, mock_ddc_cls, mock_filterer_cls):
        from bethpage_black_bot import BethpageBlackBot

        mock_scraper_cls.return_value.get_tee_time_data.return_value = []
        mock_ddc_cls.return_value.get_all_emails_list.return_value = ["a@b.com"]
        mock_ddc_cls.return_value.get_latest_filtered_tee_times.return_value = {}
        mock_filterer_cls.return_value.filter_tee_times_for_user.return_value = []
        mock_filterer_cls.return_value.remove_existing_tee_times.return_value = []

        bot = BethpageBlackBot()
        bot.bethpage_email = "user"
        bot.bethpage_password = "pass"
        result = bot.get_new_tee_times()
        assert result == {}


class TestNotifyIfNewTeeTimes:
    # EmailLog and OneTimeLinkHandler must be patched too: notify_if_new_tee_times
    # constructs both, and an unmocked one writes to the real DynamoDB tables.
    @patch("bethpage_black_bot.EmailLog")
    @patch("bethpage_black_bot.OneTimeLinkHandler")
    @patch("bethpage_black_bot.EmailSender")
    @patch("bethpage_black_bot.SecretHandler")
    def test_sends_emails(self, mock_secret, mock_email_cls, mock_otlh_cls, mock_log_cls):
        from bethpage_black_bot import BethpageBlackBot

        mock_secret.get_bethpage_username_and_password.return_value = ("user", "pass")
        bot = BethpageBlackBot()

        with patch.object(bot, "get_new_tee_times", return_value={"a@b.com": [{"Time": "8am"}]}):
            bot.notify_if_new_tee_times()

        mock_email_cls.return_value.send_email.assert_called_once()

    @patch("bethpage_black_bot.EmailLog")
    @patch("bethpage_black_bot.OneTimeLinkHandler")
    @patch("bethpage_black_bot.EmailSender")
    @patch("bethpage_black_bot.SecretHandler")
    def test_logs_each_email_sent(self, mock_secret, mock_email_cls, mock_otlh_cls, mock_log_cls):
        from bethpage_black_bot import BethpageBlackBot

        mock_secret.get_bethpage_username_and_password.return_value = ("user", "pass")
        bot = BethpageBlackBot()
        new_times = [{"Time": "8am"}]

        with patch.object(bot, "get_new_tee_times", return_value={"a@b.com": new_times}):
            bot.notify_if_new_tee_times()

        mock_log_cls.return_value.record_email_sent.assert_called_once()
        args = mock_log_cls.return_value.record_email_sent.call_args[0]
        assert args[1] == "a@b.com"
        assert args[2] == new_times

    @patch("bethpage_black_bot.EmailLog")
    @patch("bethpage_black_bot.OneTimeLinkHandler")
    @patch("bethpage_black_bot.EmailSender")
    @patch("bethpage_black_bot.SecretHandler")
    def test_logging_failure_does_not_stop_sending(
        self, mock_secret, mock_email_cls, mock_otlh_cls, mock_log_cls
    ):
        from bethpage_black_bot import BethpageBlackBot

        mock_secret.get_bethpage_username_and_password.return_value = ("user", "pass")
        mock_log_cls.return_value.record_email_sent.side_effect = RuntimeError("dynamo down")
        bot = BethpageBlackBot()

        with patch.object(bot, "get_new_tee_times", return_value={"a@b.com": [], "c@d.com": []}):
            bot.notify_if_new_tee_times()

        # Both users still got their email despite the log write blowing up.
        assert mock_email_cls.return_value.send_email.call_count == 2

    @patch("bethpage_black_bot.EmailLog")
    @patch("bethpage_black_bot.OneTimeLinkHandler")
    @patch("bethpage_black_bot.EmailSender")
    @patch("bethpage_black_bot.SecretHandler")
    def test_sends_error_email_on_exception(
        self, mock_secret, mock_email_cls, mock_otlh_cls, mock_log_cls
    ):
        from bethpage_black_bot import BethpageBlackBot
        import pytest

        mock_secret.get_bethpage_username_and_password.return_value = ("user", "pass")
        bot = BethpageBlackBot()

        with patch.object(bot, "get_new_tee_times", side_effect=RuntimeError("boom")):
            with pytest.raises(RuntimeError):
                bot.notify_if_new_tee_times()

        mock_email_cls.return_value.send_error_email.assert_called_once()
