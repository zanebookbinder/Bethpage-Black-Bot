import requests
from .daily_updates_secret_handler import DailyUpdateSecretHandler


class TravelTimeCalculationService:
    def __init__(self):
        self.home_address, self.api_key = (
            DailyUpdateSecretHandler.get_daily_updates_secret_info()
        )

    def format_request_url(self, destination: str, mode: str) -> str:
        """Format the Google Maps Distance Matrix API request URL."""
        if mode not in ["driving", "walking", "bicycling", "transit"]:
            raise ValueError(
                "Invalid mode. Choose from 'driving', 'walking', 'bicycling', or 'transit'."
            )

        formatted_origin = self.home_address.replace(" ", "+")
        formatted_destination = destination.replace(" ", "+")
        return f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={formatted_origin}&destinations={formatted_destination}&mode={mode}&units=imperial&key={self.api_key}"

    def get_travel_time(self, destination: str, mode: str) -> int:
        """Get travel time in minutes from home address to destination."""
        url = self.format_request_url(destination, mode)
        response = requests.get(url)
        data = response.json()

        if data["status"] != "OK":
            raise Exception(f"Error from Google Maps API: {data['status']}")

        element = data["rows"][0]["elements"][0]
        if element["status"] != "OK":
            raise Exception(f"Error for element: {element['status']}")

        return element["duration"]["text"]
