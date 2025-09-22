import boto3
from late_night_show_waitlist_helpers.late_night_web_scraper import URL_TO_SHOW_NAME_DICT
from late_night_show_waitlist_helpers.late_night_secret_handler import LateNightSecretHandler

class LateNightEmailSender:

	def __init__(self):
		self.admin_email = LateNightSecretHandler.get_admin_email()
		self.ses = boto3.client("ses", region_name="us-east-1")

	def send_waitlist_email(self, new_waitlist_dict):
		print(f'Sending email to {self.admin_email}')
		# Build the HTML table
		html_lines = [
			"<html><body>",
			"<h2>New Late Night Show Waitlists Found</h2>",
			"<table border='1' cellpadding='5' cellspacing='0' style='border-collapse: collapse;'>",
			"<thead><tr><th>Show Name</th><th>Date</th><th>Time</th><th>Button Text Found</th></thead>",
			"<tbody>",
		]

		for show_name, entries in new_waitlist_dict.items():
			show_url = [key for key, value in URL_TO_SHOW_NAME_DICT.items() if value == show_name][0]

			for i, entry in enumerate(entries):
				row = "<tr>"
				if i == 0:
					row += f"<td rowspan='{len(entries)}'>{show_name}<br/>{show_url}</td>"
				row += f"<td>{entry.date}</td><td>{entry.show_time}</td><td>{entry.button_text}</td>"
				row += "</tr>"
				html_lines.append(row)

		html_lines += ["</tbody></table><h4>https://1iota.com/</h4></body></html>"]
		body_html = "".join(html_lines)

		# Send email with HTML body
		self.ses.send_email(
			Source=self.admin_email,
			Destination={"ToAddresses": [self.admin_email]},
			Message={
				"Subject": {"Data": "New Late Night Show Waitlists Found"},
				"Body": {"Html": {"Data": body_html}},
			},
		)

	def send_error_email(self, error_as_str):
		print(f'Sending error email to {self.admin_email}')

		self.ses.send_email(
			Source=self.admin_email,
			Destination={"ToAddresses": [self.admin_email]},
			Message={
				"Subject": {"Data": "[ERROR] Late Night Waitlist Scraper"},
				"Body": {"Text": {"Data": error_as_str}},
			},
		)
	
	# def add_email_identity(self, email_to_verify=None):
	#     email_to_verify = email_to_verify if email_to_verify else self.admin_email
	#     try:
	#         response = self.ses.verify_email_identity(
	#             EmailAddress=email_to_verify
	#         )
	#         return f"Verification email sent to {email_to_verify} with response {response}"
		
	#     except Exception as e:
	#         return f"Error: {str(e)}"
		
	# def send_welcome_email(self, email):
	#     self.send_one_time_link_email()
	#     self.ses.send_email(
	#         Source=self.admin_email,
	#         Destination={"ToAddresses": [email]},
	#         Message={
	#             "Subject": {"Data": "Hello from the Bethpage Black Bot!"},
	#             "Body": {"Text": {"Data": WELCOME_EMAIL_TEXT}},
	#         },
	#     )

# waitlists = {'Colbert': [
# 		WaitlistEntry('Sept 12', 'Colbert', 'Join Waitlist', '9pm'),
# 		WaitlistEntry('Sept 13', 'Colbert', 'fake button text2', 'fake show time2')
# 	],
# 	'Meyers': [WaitlistEntry('fake date', 'fake show name', 'fake button text', 'fake show time'),]
# }
# es = LateNightEmailSender()
# es.send_waitlist_email(waitlists)