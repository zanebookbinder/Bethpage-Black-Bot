from unittest.mock import patch
from central_park_public_volunteering_bot import CentralParkPublicVolunteeringBot


class TestGenerateEmailHtml:
    def setup_method(self):
        self.bot = CentralParkPublicVolunteeringBot()

    def test_with_events(self):
        events = [
            {"date": "March 14", "time": "9:00 AM"},
            {"date": "March 21", "time": "10:00 AM"},
        ]
        html = self.bot._generate_email_html(events)
        assert "March 14" in html
        assert "March 21" in html
        assert "9:00 AM" in html
        assert "<table" in html
        assert "Sign Up" in html

    def test_empty_events(self):
        html = self.bot._generate_email_html([])
        assert "No available" in html

    def test_no_events_html(self):
        html = self.bot._generate_no_events_html()
        assert "No upcoming" in html

    def test_error_html(self):
        html = self.bot._generate_error_html()
        assert "Unable to retrieve" in html
