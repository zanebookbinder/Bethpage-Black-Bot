from unittest.mock import patch


class TestCentralParkPrivateBot:
    def make_bot(self):
        from central_park_private_volunteering_bot import CentralParkPrivateVolunteeringBot
        return CentralParkPrivateVolunteeringBot()

    def test_generate_email_html_empty(self):
        bot = self.make_bot()
        html = bot._generate_email_html([])
        assert "No opportunities" in html or "No weekend" in html

    def test_generate_email_html_with_weekend_opps(self):
        bot = self.make_bot()
        opps = [
            {
                "name": "Tree Planting",
                "date": "Saturday, March 14, 2026",
                "start_time": "9:00 AM",
                "end_time": "12:00 PM",
                "open_slots": "5",
                "url": "https://example.com/signup",
            }
        ]
        html = bot._generate_email_html(opps)
        assert "Tree Planting" in html
        assert "9:00 AM" in html
        assert "Sign Up" in html
        assert "<table" in html

    def test_generate_email_html_filters_weekdays(self):
        bot = self.make_bot()
        opps = [
            {
                "name": "Weekday Event",
                "date": "Wednesday, March 18, 2026",
                "start_time": "9:00 AM",
                "end_time": "12:00 PM",
                "open_slots": "5",
                "url": "https://example.com",
            }
        ]
        html = bot._generate_email_html(opps)
        assert "No weekend" in html or "No opportunities" in html

    def test_generate_error_html(self):
        bot = self.make_bot()
        html = bot._generate_error_html()
        assert "Unable to retrieve" in html

    def test_sorted_by_date(self):
        bot = self.make_bot()
        opps = [
            {
                "name": "Later",
                "date": "Sunday, March 22, 2026",
                "start_time": "9:00 AM",
                "end_time": "12:00 PM",
                "open_slots": "3",
                "url": "https://example.com",
            },
            {
                "name": "Earlier",
                "date": "Saturday, March 14, 2026",
                "start_time": "10:00 AM",
                "end_time": "1:00 PM",
                "open_slots": "5",
                "url": "https://example.com",
            },
        ]
        html = bot._generate_email_html(opps)
        assert html.index("Earlier") < html.index("Later")
