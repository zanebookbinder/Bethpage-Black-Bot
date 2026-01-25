import boto3
from daily_update_helpers.daily_updates_secret_handler import DailyUpdateSecretHandler


class DailyUpdateEmailService:
    def __init__(self):
        self.admin_email = DailyUpdateSecretHandler.get_admin_email()
        self.daily_update_emails = DailyUpdateSecretHandler.get_daily_updates_emails()
        self.ses = boto3.client("ses", region_name="us-east-1")

    def send_combined_email(self, html_pieces, subject: str = "Zane's Daily Update"):
        print(f"Sending Daily Update email to {self.daily_update_emails}")

        if None in html_pieces:
            index = html_pieces.index(None)
            print("One of the HTML pieces is None, replacing with empty string. Index:", index)
            html_pieces = [piece if piece is not None else "" for piece in html_pieces]

        body_html = (
            "<html><body style=\"font-family: 'Roboto', Arial, sans-serif;\">"
            + "<hr>".join(html_pieces)
            + "</body></html>"
        )

        self.ses.send_email(
            Source=self.admin_email,
            Destination={"ToAddresses": self.daily_update_emails},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Html": {"Data": body_html}},
            },
        )

        print("Email sent successfully.")

    def send_error_email(self, error_as_str):
        print(f"Sending error email to {self.admin_email}")

        self.ses.send_email(
            Source=self.admin_email,
            Destination={"ToAddresses": [self.admin_email]},
            Message={
                "Subject": {"Data": "[ERROR] Daily Update Bot Error"},
                "Body": {"Text": {"Data": error_as_str}},
            },
        )
