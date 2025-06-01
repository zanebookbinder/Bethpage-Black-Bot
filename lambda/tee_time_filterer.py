from astral.sun import sun
from astral import LocationInfo
from datetime import datetime, timedelta
from date_handler import DateHandler
import holidays
from decimal import Decimal
from dynamo_db_connection import DynamoDBConnection

class TeeTimeFilterer():

	def __init__(self):
		self.db_table = DynamoDBConnection()

		try:
			# CONFIG FROM DATABASE
			self.load_config_from_database()
			self.output_current_config()

			# LOCATION AND HOILDAY CONFIG
			self.bethpaige_info = LocationInfo("Farmingdale", "USA", "America/New_York", 40.7326, -73.4457)
			self.holiday_dates = [date.strftime("%m/%d/%Y") for date in holidays.UnitedStates(years=datetime.now().year)]
			self.date_handler = DateHandler()
		except Exception as e:
			print("ERROR WITH CONFIGURED VARIABLES")
			raise e
		
	def filter_tee_times(self, tee_times_to_consider):
		print('Tee times before filtering:', tee_times_to_consider)
		filtered_tee_times = []

		for tee_time in tee_times_to_consider: 
			# {Date: "Tuesday, May 27th", Time: "4:30pm", Players: "2", Holes: "18"}
			day_of_week, date_obj = self.parse_date_string(tee_time['Date'])

			# is ok day (weekend, holiday, etc.)
			is_playable_day = self.is_playable_day(day_of_week, date_obj)

			# is acceptable time (after min time and before sunset)
			tee_time_of_day = datetime.strptime(tee_time['Time'], "%I:%M%p").time()
			is_acceptable_time = self.is_far_enough_before_sunset(date_obj, tee_time_of_day) \
				and self.is_after_earliest_acceptable_time(tee_time_of_day)
			
			# is minimum number of players
			hits_min_players = int(tee_time['Players']) >= self.min_players

			# then yes, this tee time is ok
			if is_playable_day and is_acceptable_time and hits_min_players:
				filtered_tee_times.append(tee_time)

		print('Tee times after filtering:', filtered_tee_times)
		return filtered_tee_times

	def is_after_earliest_acceptable_time(self, time_of_day):
		earliest_playable_time_as_dt = datetime.strptime(self.earliest_playable_time, "%I:%M%p").time()
		return time_of_day > earliest_playable_time_as_dt

	def is_far_enough_before_sunset(self, date_obj, time_of_day):
		sunset_time = sun(self.bethpaige_info.observer, date=date_obj, tzinfo=self.bethpaige_info.timezone)['sunset']
		before_sunset_dt = sunset_time - timedelta(minutes=self.minimum_minutes_before_sunset)

		return time_of_day < before_sunset_dt.time()
	
	def parse_date_string(self, date_str):
		parts = date_str.split()
		day_of_week = parts[0]
		month = parts[1]
		day = self.date_handler.strip_ordinal_suffix(parts[2])
		
		year = datetime.now().year
		
		# Parse to datetime object
		date_obj = datetime.strptime(f"{month} {day} {year}", "%B %d %Y").date()
		return day_of_week, date_obj
	
	def get_day_of_week_from_str(self, date_str):
		return date_str.split()[0]
	
	def is_playable_day(self, day_of_week, date_obj):
		is_playable_day_of_week = day_of_week in self.playable_days_of_week
		
		formatted = f"{date_obj.month}/{date_obj.day}/{date_obj.year}"
		is_extra_day_to_notify = formatted in self.extra_playable_days

		is_us_holiday = formatted in self.holiday_dates \
			if self.include_holidays \
			else False

		return is_playable_day_of_week or is_extra_day_to_notify or is_us_holiday
	
	def load_config_from_database(self):
		config_data = self.db_table.get_config()

		if not config_data:
			# Fallback defaults if no config found
			self.playable_days_of_week = ["Saturday", "Sunday"]
			self.earliest_playable_time = "8:00am"
			self.extra_playable_days = ["6/19/2025", "7/3/2025", "7/4/2025", "8/29/2025", "9/1/2025"]
			self.include_holidays = True
			self.minimum_minutes_before_sunset = 240
			self.min_players = 2
			return

		# Grab the first (and presumably only) config item

		def convert_decimal(value):
			# Convert DynamoDB Decimal to int if possible
			if isinstance(value, Decimal):
				if value % 1 == 0:
					return int(value)
				else:
					return float(value)
			return value

		self.playable_days_of_week = config_data.get("playable_days_of_week", ["Saturday", "Sunday"])
		self.earliest_playable_time = config_data.get("earliest_playable_time", "8:00am")
		self.extra_playable_days = config_data.get("extra_playable_days", ["6/19/2025", "7/3/2025", "7/4/2025", "8/29/2025", "9/1/2025"])
		self.include_holidays = config_data.get("include_holidays", True)
		self.minimum_minutes_before_sunset = convert_decimal(config_data.get("minimum_minutes_before_sunset", 240))
		self.min_players = convert_decimal(config_data.get("min_players", 2))

	def output_current_config(self):
		print(
				"CONFIG LOADED:\n"
				f"  Playable Days of Week: {self.playable_days_of_week}\n"
				f"  Earliest Playable Time: {self.earliest_playable_time}\n"
				f"  Extra Playable Days: {self.extra_playable_days}\n"
				f"  Include Holidays: {self.include_holidays}\n"
				f"  Minimum Minutes Before Sunset: {self.minimum_minutes_before_sunset}\n"
				f"  Minimum Players: {self.min_players}"
			)

# t = TeeTimeFilterer()
# d = [{'Date': 'Saturday May 31st', 'Time': '3:50pm', 'Players': 2, 'Holes': 18}]

# t.filter_tee_times(d)