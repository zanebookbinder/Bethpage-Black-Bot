import boto3
from collections import defaultdict


class EmailSender:

    def __init__(self, email):
        self.email = email

    def send_email(self, new_times):
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
        ses = boto3.client("ses", region_name="us-east-1")
        ses.send_email(
            Source=self.email,
            Destination={"ToAddresses": [self.email]},
            Message={
                "Subject": {"Data": "New Bethpage Tee Times Found"},
                "Body": {"Html": {"Data": body_html}},
            },
        )

    def send_error_email(self, error_as_str):
        ses = boto3.client("ses", region_name="us-east-1")
        ses.send_email(
            Source=self.email,
            Destination={"ToAddresses": [self.email]},
            Message={
                "Subject": {"Data": "[ERROR] Bethpage Black Bot"},
                "Body": {"Text": {"Data": error_as_str}},
            },
        )