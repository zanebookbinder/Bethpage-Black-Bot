from unittest.mock import patch, MagicMock


def make_sender():
    with patch("lambda_helpers.email_sender.SecretHandler") as mock_secret, \
         patch("lambda_helpers.email_sender.boto3") as mock_boto:
        mock_secret.get_sender_email.return_value = "admin@test.com"
        mock_secret.get_one_time_link_sender_email.return_value = "otl@test.com"
        mock_ses = MagicMock()
        mock_boto.client.return_value = mock_ses
        from lambda_helpers.email_sender import EmailSender
        sender = EmailSender()
        return sender, mock_ses


class TestSendEmail:
    def test_sends_html_with_table(self):
        sender, mock_ses = make_sender()
        times = [
            {"Date": "Saturday", "Time": "8:00am", "Players": "3", "Holes": "18"},
            {"Date": "Saturday", "Time": "9:00am", "Players": "2", "Holes": "18"},
        ]
        sender.send_email("user@test.com", times)
        mock_ses.send_email.assert_called_once()
        call_args = mock_ses.send_email.call_args
        html = call_args[1]["Message"]["Body"]["Html"]["Data"]
        assert "8:00am" in html
        assert "9:00am" in html
        assert "Saturday" in html

    def test_groups_by_date(self):
        sender, mock_ses = make_sender()
        times = [
            {"Date": "Saturday", "Time": "8:00am", "Players": "2", "Holes": "18"},
            {"Date": "Sunday", "Time": "10:00am", "Players": "3", "Holes": "18"},
        ]
        sender.send_email("user@test.com", times)
        call_kwargs = mock_ses.send_email.call_args
        html = call_kwargs[1]["Message"]["Body"]["Html"]["Data"]
        assert "rowspan" in html

    def test_has_styled_cells(self):
        sender, mock_ses = make_sender()
        times = [{"Date": "Saturday", "Time": "8:00am", "Players": "2", "Holes": "18"}]
        sender.send_email("user@test.com", times)
        html = mock_ses.send_email.call_args[1]["Message"]["Body"]["Html"]["Data"]
        assert "border: 1px solid #ddd" in html
        assert "padding: 8px" in html
        assert "background-color: #f0f0f0" in html

    def test_has_booking_link(self):
        sender, mock_ses = make_sender()
        times = [{"Date": "Saturday", "Time": "8:00am", "Players": "2", "Holes": "18"}]
        sender.send_email("user@test.com", times)
        html = mock_ses.send_email.call_args[1]["Message"]["Body"]["Html"]["Data"]
        assert "foreupsoftware.com" in html
        assert "Book on Bethpage" in html


class TestSendErrorEmail:
    def test_sends_plain_text(self):
        sender, mock_ses = make_sender()
        sender.send_error_email("Something went wrong")
        mock_ses.send_email.assert_called_once()
        call_kwargs = mock_ses.send_email.call_args
        text = call_kwargs[1]["Message"]["Body"]["Text"]["Data"]
        assert "Something went wrong" in text


class TestSendOneTimeLinkEmail:
    def test_welcome_email(self):
        sender, mock_ses = make_sender()
        sender.send_one_time_link_email("user@test.com", "guid-123", welcome_email=True)
        call_kwargs = mock_ses.send_email.call_args
        subject = call_kwargs[1]["Message"]["Subject"]["Data"]
        assert "Hello" in subject or "Welcome" in subject

    def test_regular_link_email(self):
        sender, mock_ses = make_sender()
        sender.send_one_time_link_email("user@test.com", "guid-123", welcome_email=False)
        call_kwargs = mock_ses.send_email.call_args
        subject = call_kwargs[1]["Message"]["Subject"]["Data"]
        assert "One Time Link" in subject

    def test_link_contains_guid(self):
        sender, mock_ses = make_sender()
        sender.send_one_time_link_email("user@test.com", "guid-123")
        call_kwargs = mock_ses.send_email.call_args
        html = call_kwargs[1]["Message"]["Body"]["Html"]["Data"]
        assert "guid-123" in html
