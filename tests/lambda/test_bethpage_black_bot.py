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
    @patch("bethpage_black_bot.EmailSender")
    @patch("bethpage_black_bot.SecretHandler")
    def test_sends_emails(self, mock_secret, mock_email_cls):
        from bethpage_black_bot import BethpageBlackBot

        mock_secret.get_bethpage_username_and_password.return_value = ("user", "pass")
        bot = BethpageBlackBot()

        with patch.object(bot, "get_new_tee_times", return_value={"a@b.com": [{"Time": "8am"}]}):
            bot.notify_if_new_tee_times()

        mock_email_cls.return_value.send_email.assert_called_once()

    @patch("bethpage_black_bot.EmailSender")
    @patch("bethpage_black_bot.SecretHandler")
    def test_sends_error_email_on_exception(self, mock_secret, mock_email_cls):
        from bethpage_black_bot import BethpageBlackBot
        import pytest

        mock_secret.get_bethpage_username_and_password.return_value = ("user", "pass")
        bot = BethpageBlackBot()

        with patch.object(bot, "get_new_tee_times", side_effect=RuntimeError("boom")):
            with pytest.raises(RuntimeError):
                bot.notify_if_new_tee_times()

        mock_email_cls.return_value.send_error_email.assert_called_once()
