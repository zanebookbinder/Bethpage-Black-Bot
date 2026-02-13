from unittest.mock import patch, MagicMock


def make_service():
    with patch("daily_update_helpers.daily_updates_email_service.DailyUpdateSecretHandler") as mock_secret, \
         patch("daily_update_helpers.daily_updates_email_service.boto3") as mock_boto:
        mock_secret.get_admin_email.return_value = "admin@test.com"
        mock_secret.get_daily_updates_emails.return_value = ["user1@test.com", "user2@test.com"]
        mock_ses = MagicMock()
        mock_boto.client.return_value = mock_ses
        from daily_update_helpers.daily_updates_email_service import DailyUpdateEmailService
        svc = DailyUpdateEmailService()
        return svc, mock_ses


class TestSendCombinedEmail:
    def test_joins_pieces_with_hr(self):
        svc, mock_ses = make_service()
        svc.send_combined_email(["<p>Part 1</p>", "<p>Part 2</p>"])
        call_kwargs = mock_ses.send_email.call_args[1]
        html = call_kwargs["Message"]["Body"]["Html"]["Data"]
        assert "<hr>" in html
        assert "Part 1" in html
        assert "Part 2" in html

    def test_filters_none_pieces(self):
        svc, mock_ses = make_service()
        svc.send_combined_email([None, "<p>Only</p>", None])
        call_kwargs = mock_ses.send_email.call_args[1]
        html = call_kwargs["Message"]["Body"]["Html"]["Data"]
        assert "Only" in html
        assert "<hr>" not in html  # only one piece after filtering

    def test_custom_subject(self):
        svc, mock_ses = make_service()
        svc.send_combined_email(["<p>A</p>"], subject="Custom Subject")
        call_kwargs = mock_ses.send_email.call_args[1]
        assert call_kwargs["Message"]["Subject"]["Data"] == "Custom Subject"

    def test_sends_to_all_recipients(self):
        svc, mock_ses = make_service()
        svc.send_combined_email(["<p>A</p>"])
        call_kwargs = mock_ses.send_email.call_args[1]
        assert call_kwargs["Destination"]["ToAddresses"] == ["user1@test.com", "user2@test.com"]


class TestSendErrorEmail:
    def test_sends_to_admin(self):
        svc, mock_ses = make_service()
        svc.send_error_email("error details")
        call_kwargs = mock_ses.send_email.call_args[1]
        assert call_kwargs["Destination"]["ToAddresses"] == ["admin@test.com"]
        assert "error details" in call_kwargs["Message"]["Body"]["Text"]["Data"]
