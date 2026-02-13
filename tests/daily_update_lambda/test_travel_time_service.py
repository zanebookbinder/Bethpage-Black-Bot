from unittest.mock import patch, MagicMock
import pytest


def make_service():
    with patch("daily_update_helpers.travel_time_calculation_service.DailyUpdateSecretHandler") as mock_secret:
        mock_secret.get_daily_updates_secret_info.return_value = ("123 Main St", "fake-api-key")
        from daily_update_helpers.travel_time_calculation_service import TravelTimeCalculationService
        return TravelTimeCalculationService()


class TestFormatRequestUrl:
    def test_valid_mode(self):
        svc = make_service()
        url = svc.format_request_url("456 Oak Ave", "transit")
        assert "origins=123+Main+St" in url
        assert "destinations=456+Oak+Ave" in url
        assert "mode=transit" in url
        assert "key=fake-api-key" in url

    def test_invalid_mode(self):
        svc = make_service()
        with pytest.raises(ValueError):
            svc.format_request_url("456 Oak Ave", "teleport")

    def test_all_valid_modes(self):
        svc = make_service()
        for mode in ["driving", "walking", "bicycling", "transit"]:
            url = svc.format_request_url("dest", mode)
            assert f"mode={mode}" in url


class TestGetTravelTime:
    @patch("daily_update_helpers.travel_time_calculation_service.requests")
    def test_returns_duration_text(self, mock_requests):
        svc = make_service()
        mock_requests.get.return_value.json.return_value = {
            "status": "OK",
            "rows": [{"elements": [{"status": "OK", "duration": {"text": "25 mins"}}]}],
        }
        result = svc.get_travel_time("456 Oak Ave", "transit")
        assert result == "25 mins"

    @patch("daily_update_helpers.travel_time_calculation_service.requests")
    def test_api_error(self, mock_requests):
        svc = make_service()
        mock_requests.get.return_value.json.return_value = {"status": "REQUEST_DENIED"}
        with pytest.raises(Exception, match="REQUEST_DENIED"):
            svc.get_travel_time("dest", "driving")

    @patch("daily_update_helpers.travel_time_calculation_service.requests")
    def test_element_error(self, mock_requests):
        svc = make_service()
        mock_requests.get.return_value.json.return_value = {
            "status": "OK",
            "rows": [{"elements": [{"status": "NOT_FOUND"}]}],
        }
        with pytest.raises(Exception, match="NOT_FOUND"):
            svc.get_travel_time("dest", "driving")
