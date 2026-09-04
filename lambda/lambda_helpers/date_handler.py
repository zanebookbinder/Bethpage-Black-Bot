from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re

# The course, the users and every time we display are all Eastern. The lambda
# itself runs in UTC, so anything user-facing has to be stamped explicitly.
EASTERN = ZoneInfo("America/New_York")


def now_eastern():
	return datetime.now(EASTERN)


class DateHandler():

	def get_day_suffix(self, day):
		if 11 <= day <= 13:
			return 'th'
		last_digit = day % 10
		return {1: 'st', 2: 'nd', 3: 'rd'}.get(last_digit, 'th')
	
	def strip_ordinal_suffix(self, s):
		return re.sub(r'(st|nd|rd|th)', '', s)
	
	def get_date_from_day_number(self, day_number):
		today = datetime.today()

		for i in range(9):
			candidate = today + timedelta(days=i)
			if day_number.isdigit() and candidate.day == int(day_number):
				suffix = self.get_day_suffix(candidate.day)
				return candidate.strftime(f"%A %B {candidate.day}{suffix}")
		
		return None  # If not found in the next 7 days