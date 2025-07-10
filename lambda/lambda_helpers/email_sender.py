import boto3
from collections import defaultdict
from lambda_helpers.secret_handler import SecretHandler

WELCOME_EMAIL_TEXT = \
    "Welcome! You've signed up to receive notifications " \
    "when new tee times are available on Bethpage Black. " \
    "Please use the one-time link below to update your notification " \
    "settings. If you did not sign up, please notify us at " \
    "info@bethpage-black-bot.com."
WELCOME_EMAIL_SUBJECT = "Hello from the Bethpage Black Bot!"

ONE_TIME_LINK_EMAIL_TEXT = \
    "You've requested a one-time link to update your notification settings " \
    "for the Bethpage Black Bot. If you did not request this link, please notify " \
    "us at info@bethpage-black-bot.com. Thank you!"
ONE_TIME_LINK_EMAIL_SUBJECT = "One Time Link to Update Your Bethpage Black Bot Settings"

FRONTEND_URL = 'https://www.bethpage-black-bot.com'

class EmailSender:

    def __init__(self):
        self.admin_email = SecretHandler.get_sender_email()
        self.one_time_link_email = SecretHandler.get_one_time_link_sender_email()
        self.ses = boto3.client("ses", region_name="us-east-1")

    def send_email(self, email, new_times):
        # Group times by date
        grouped = defaultdict(list)
        for time in new_times:
            grouped[time["Date"]].append(time)

        # Build the HTML table
        html_lines = [
            "<html><body>",
            "<h2>New Bethpage Tee Times Found</h2>",
            "<table border='1' cellpadding='5' cellspacing='0' style='border-collapse: collapse;'>",
            "<thead><tr><th>Date</th><th>Time</th><th>Players</th><th>Holes</th></tr></thead>",
            "<tbody>",
        ]

        for date, entries in grouped.items():
            for i, entry in enumerate(entries):
                row = "<tr>"
                if i == 0:
                    row += f"<td rowspan='{len(entries)}'>{date}</td>"
                row += f"<td>{entry['Time']}</td><td>{entry['Players']}</td><td>{entry['Holes']}</td>"
                row += "</tr>"
                html_lines.append(row)

        html_lines += ["</tbody></table></body></html>"]
        body_html = "".join(html_lines)

        # Send email with HTML body
        self.ses.send_email(
            Source=self.admin_email,
            Destination={"ToAddresses": [email]},
            Message={
                "Subject": {"Data": "New Bethpage Tee Times Found"},
                "Body": {"Html": {"Data": body_html}},
            },
        )

    def send_error_email(self, error_as_str):
        self.ses.send_email(
            Source=self.admin_email,
            Destination={"ToAddresses": [self.admin_email]},
            Message={
                "Subject": {"Data": "[ERROR] Bethpage Black Bot"},
                "Body": {"Text": {"Data": error_as_str}},
            },
        )

    def send_one_time_link_email(self, email, guid, welcome_email=False):
        email_subject = WELCOME_EMAIL_SUBJECT if welcome_email else ONE_TIME_LINK_EMAIL_SUBJECT
        link = f"{FRONTEND_URL}/updateSettings/{guid}"
        message = WELCOME_EMAIL_TEXT if welcome_email else ONE_TIME_LINK_EMAIL_TEXT 

        body_html = f"""
        <html>
        <head></head>
        <body>
        <p>{message}</p>
        <p>Use the link below to access your one-time login:</p>
        <p><a href="{link}">{link}</a></p>
        </body>
        </html>
        """

        self.ses.send_email(
            Source=self.one_time_link_email,
            Destination={"ToAddresses": [email]},
            Message={
                "Subject": {"Data": email_subject},
                "Body": {"Html": {"Data": body_html}, "Text": {"Data": message}},
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

# es = EmailSender()
# es.send_one_time_link_email("zane.bookbinder@gmail.com", "4535325fffhello")