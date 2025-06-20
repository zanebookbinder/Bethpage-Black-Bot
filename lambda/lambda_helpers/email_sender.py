import boto3
from collections import defaultdict

WELCOME_EMAIL_TEXT = \
    "You've registered your email to receive notifications " \
    "when new tee times are available for Bethpage Black. " \
    "If you'd like to update your configuration, please visit " \
    "the website. Thanks for joining!"

class EmailSender:

    def __init__(self, admin_email, email=None):
        self.admin_email = admin_email
        self.email = email
        self.ses = boto3.client("ses", region_name="us-east-1")

    def send_email(self, new_times, email=None):
        email = self.email if not email else email

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

    def send_error_email(self, error_as_str, email=None):
        email = self.email if not email else email

        self.ses.send_email(
            Source=self.admin_email,
            Destination={"ToAddresses": [self.email]},
            Message={
                "Subject": {"Data": "[ERROR] Bethpage Black Bot"},
                "Body": {"Text": {"Data": error_as_str}},
            },
        )

    def add_email_identity(self, email_to_verify=None):
        email_to_verify = email_to_verify if email_to_verify else self.email
        try:
            response = self.ses.verify_email_identity(
                EmailAddress=email_to_verify
            )
            return f"Verification email sent to {email_to_verify} with response {response}"
        
        except Exception as e:
            return f"Error: {str(e)}"
        
    def send_welcome_email(self, email=None):
        email = self.email if not email else email

        self.ses.send_email(
            Source=self.admin_email,
            Destination={"ToAddresses": [email]},
            Message={
                "Subject": {"Data": "Hello from the Bethpage Black Bot!"},
                "Body": {"Text": {"Data": WELCOME_EMAIL_TEXT}},
            },
        )