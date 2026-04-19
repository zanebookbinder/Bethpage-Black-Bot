import logging
import boto3
from collections import defaultdict
from lambda_helpers.secret_handler import SecretHandler

logger = logging.getLogger(__name__)

WELCOME_EMAIL_TEXT = (
    "Welcome! You've signed up to receive notifications "
    "when new tee times are available on Bethpage Black. "
    "Please use the one-time link below to update your notification "
    "settings. If you did not sign up, please notify us at "
    "info@bethpage-black-bot.com."
)
WELCOME_EMAIL_SUBJECT = "Hello from the Bethpage Black Bot!"

ONE_TIME_LINK_EMAIL_TEXT = (
    "You've requested a one-time link to update your notification settings "
    "for the Bethpage Black Bot. If you did not request this link, please notify "
    "us at info@bethpage-black-bot.com. Thank you!"
)
ONE_TIME_LINK_EMAIL_SUBJECT = "One Time Link to Update Your Bethpage Black Bot Settings"

FRONTEND_URL = "https://www.bethpage-black-bot.com"


class EmailSender:

    def __init__(self):
        self.admin_email = SecretHandler.get_sender_email()
        self.one_time_link_email = SecretHandler.get_one_time_link_sender_email()
        self.admin_notify_email = SecretHandler.get_admin_notify_email()
        self.ses = boto3.client("ses", region_name="us-east-1")

    BOOKING_URL = "https://foreupsoftware.com/index.php/booking/19765/2431#/teetimes"

    def send_email(self, email, new_times, pause_guid=None):
        logger.info(
            "Sending tee time notification to %s with %d new times",
            email,
            len(new_times),
        )
        # Group times by date
        grouped = defaultdict(list)
        for time in new_times:
            grouped[time["Date"]].append(time)

        cell_style = "border: 1px solid #ddd; padding: 8px;"
        header_style = f"{cell_style} text-align: left;"

        # Build the HTML table
        html_lines = [
            "<html><body style=\"font-family: 'Roboto', Arial, sans-serif;\">",
            "<h2>New Bethpage Tee Times Found</h2>",
            "<table style='width: auto; border-collapse: collapse;'>",
            f"<thead><tr style='background-color: #f0f0f0;'>"
            f"<th style='{header_style}'>Date</th>"
            f"<th style='{header_style}'>Time</th>"
            f"<th style='{header_style}'>Players</th>"
            f"<th style='{header_style}'>Holes</th>"
            f"</tr></thead>",
            "<tbody>",
        ]

        for date, entries in grouped.items():
            for i, entry in enumerate(entries):
                row = "<tr>"
                if i == 0:
                    row += (
                        f"<td style='{cell_style}' rowspan='{len(entries)}'>{date}</td>"
                    )
                row += f"<td style='{cell_style}'>{entry['Time']}</td>"
                row += f"<td style='{cell_style}'>{entry['Players']}</td>"
                row += f"<td style='{cell_style}'>{entry['Holes']}</td>"
                row += "</tr>"
                html_lines.append(row)

        pause_footer = ""
        if pause_guid:
            pause_url = f"{FRONTEND_URL}/updateSettings/{pause_guid}"
            pause_footer = (
                f"<hr style='margin-top:2rem; border:none; border-top:1px solid #ddd;'/>"
                f"<p style='font-size:0.85em; color:#666;'>"
                f"<a href='{pause_url}'>Pause notifications</a>"
                f"To resume later, visit <a href='{FRONTEND_URL}'>{FRONTEND_URL}</a>, "
                f"</p>"
            )

        html_lines += [
            "</tbody></table>",
            f"<p><a href='{self.BOOKING_URL}' target='_blank'>Book on Bethpage</a></p>",
            pause_footer,
            "</body></html>",
        ]
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

    def send_user_update_to_admin_email(
        self, user_email, config_dict, is_new_account=True
    ):
        logger.info(
            "Sending admin notification for %s (new_account=%s)",
            user_email,
            is_new_account,
        )

        cell_style = "border: 1px solid #ddd; padding: 8px;"
        header_style = f"{cell_style} background-color: #f0f0f0; text-align: left;"

        field_labels = [
            ("email", "Email"),
            ("notifications_enabled", "Notifications Enabled"),
            ("in_state_golfer", "In-State Golfer"),
            ("playable_days_of_week", "Playable Days of Week"),
            ("earliest_playable_time", "Earliest Playable Time"),
            ("start_date", "Season Start Date"),
            ("end_date", "Season End Date"),
            ("include_holidays", "Include Holidays"),
            ("extra_playable_days", "Extra Playable Days"),
            ("minimum_minutes_before_sunset", "Minutes Before Sunset"),
            ("min_players", "Minimum Players"),
        ]

        rows = ""
        for key, label in field_labels:
            value = config_dict.get(key, "—")
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value) if value else "(none)"
            if key == "email":
                value = user_email
            rows += (
                f"<tr>"
                f"<td style='{cell_style}'><strong>{label}</strong></td>"
                f"<td style='{cell_style}'>{value}</td>"
                f"</tr>"
            )

        if is_new_account:
            subject = "[BBB] New Sign-Up"
            description = (
                "A new person has signed up for Bethpage Black Bot notifications."
            )
            config_note = (
                "The below values are their configuration settings (likely defaults):"
            )
        else:
            subject = "[BBB] Settings Updated"
            description = f"{user_email} has updated their Bethpage Black Bot notification settings."
            config_note = "The below values are their new configuration settings:"

        body_html = f"""
        <html><body style="font-family: Arial, sans-serif;">
        <p>{description}</p>
        <p>{config_note}</p>
        <table style="border-collapse: collapse; width: auto;">
            <thead>
                <tr>
                    <th style="{header_style}">Field</th>
                    <th style="{header_style}">Value</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        </body></html>
        """

        self.ses.send_email(
            Source=self.admin_email,
            Destination={"ToAddresses": [self.admin_notify_email]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Html": {"Data": body_html}},
            },
        )

    def send_error_email(self, error_as_str):
        logger.error("Sending error notification email")

        self.ses.send_email(
            Source=self.admin_email,
            Destination={"ToAddresses": [self.admin_email]},
            Message={
                "Subject": {"Data": "[ERROR] Bethpage Black Bot"},
                "Body": {"Text": {"Data": error_as_str}},
            },
        )

    def send_one_time_link_email(self, email, guid, welcome_email=False):
        logger.info(
            "Sending one-time link email to %s (welcome=%s)", email, welcome_email
        )

        email_subject = (
            WELCOME_EMAIL_SUBJECT if welcome_email else ONE_TIME_LINK_EMAIL_SUBJECT
        )
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
