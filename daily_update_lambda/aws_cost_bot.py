import logging
from datetime import datetime, timedelta, timezone, date

import boto3

logger = logging.getLogger(__name__)

# A single service costing more than this (month-to-date) is called out at the
# top of the email instead of tucked near the bottom.
HIGH_CHARGE_THRESHOLD = 10.0

# Services below this month-to-date cost are omitted from the breakdown table to
# keep it readable (rounding/near-zero line items).
MIN_DISPLAYED_COST = 0.01


class AwsCostBot:
    """Reports month-to-date AWS spend broken down by service plus a projected
    month-end total, using the Cost Explorer API.

    After ``scrape_data_and_return_email_html`` runs, ``has_high_charge_item`` is
    True when any single service has exceeded ``HIGH_CHARGE_THRESHOLD`` this
    month; the orchestrator uses that flag to decide placement in the email.
    """

    def __init__(self):
        # Cost Explorer is a global service fronted by the us-east-1 endpoint.
        self.ce = boto3.client("ce", region_name="us-east-1")
        self.has_high_charge_item = False

    def scrape_data_and_return_email_html(self):
        try:
            now = datetime.now(timezone.utc)
            month_start = now.replace(day=1).date()
            today = now.date()
            tomorrow = today + timedelta(days=1)
            next_month_start = self._first_of_next_month(today)

            services = self._get_month_to_date_by_service(
                month_start, min(tomorrow, next_month_start)
            )
            if not services:
                logger.info("No AWS cost data returned for the current month")
                return ""

            total_mtd = sum(cost for _, cost in services)
            self.has_high_charge_item = any(
                cost > HIGH_CHARGE_THRESHOLD for _, cost in services
            )

            projected = self._project_month_total(
                total_mtd, tomorrow, next_month_start, month_start, today
            )

            return self._build_html(services, total_mtd, projected, month_start)
        except Exception as e:
            logger.error("Error building AWS cost report: %s", str(e), exc_info=True)
            return ""

    # --- Cost Explorer calls ------------------------------------------------

    def _get_month_to_date_by_service(self, start: date, end: date):
        """Return a list of (service_name, cost) sorted by cost descending."""
        response = self.ce.get_cost_and_usage(
            TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )

        services = []
        for result in response.get("ResultsByTime", []):
            for group in result.get("Groups", []):
                name = group["Keys"][0]
                amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
                if amount >= MIN_DISPLAYED_COST:
                    services.append((name, amount))

        services.sort(key=lambda item: item[1], reverse=True)
        return services

    def _project_month_total(self, total_mtd, forecast_start, next_month_start,
                             month_start, today):
        """Projected month-end total = month-to-date + forecast of the remainder.

        Prefers Cost Explorer's forecast; falls back to a linear extrapolation if
        the forecast API is unavailable (e.g. too little history)."""
        if forecast_start >= next_month_start:
            # Last day of the month — nothing left to forecast.
            return total_mtd

        try:
            response = self.ce.get_cost_forecast(
                TimePeriod={
                    "Start": forecast_start.isoformat(),
                    "End": next_month_start.isoformat(),
                },
                Metric="UNBLENDED_COST",
                Granularity="MONTHLY",
            )
            remaining = float(response["Total"]["Amount"])
            return total_mtd + remaining
        except Exception as e:
            logger.warning(
                "Cost forecast unavailable (%s); using linear projection", str(e)
            )
            days_elapsed = (today - month_start).days + 1
            days_in_month = (next_month_start - month_start).days
            if days_elapsed <= 0:
                return total_mtd
            return total_mtd / days_elapsed * days_in_month

    @staticmethod
    def _first_of_next_month(d: date) -> date:
        if d.month == 12:
            return date(d.year + 1, 1, 1)
        return date(d.year, d.month + 1, 1)

    # --- HTML ---------------------------------------------------------------

    def _build_html(self, services, total_mtd, projected, month_start):
        month_label = month_start.strftime("%B %Y")

        rows = ""
        for name, cost in services:
            highlight = cost > HIGH_CHARGE_THRESHOLD
            name_cell = name
            cost_style = "padding: 6px 12px; text-align: right;"
            if highlight:
                name_cell = f"⚠️ <strong>{name}</strong>"
                cost_style += " color: #b00020; font-weight: bold;"
            rows += (
                "<tr>"
                f"<td style='padding: 6px 12px;'>{name_cell}</td>"
                f"<td style='{cost_style}'>${cost:,.2f}</td>"
                "</tr>"
            )

        return f"""
        <h2>AWS Charges — {month_label} (Month to Date)</h2>
        <table style="border-collapse: collapse;">
            <tr>
                <th style="padding: 6px 12px; text-align: left; border-bottom: 1px solid #ccc;">Service</th>
                <th style="padding: 6px 12px; text-align: right; border-bottom: 1px solid #ccc;">Cost</th>
            </tr>
            {rows}
            <tr>
                <td style="padding: 6px 12px; border-top: 2px solid #ccc;"><strong>Total (so far)</strong></td>
                <td style="padding: 6px 12px; text-align: right; border-top: 2px solid #ccc;"><strong>${total_mtd:,.2f}</strong></td>
            </tr>
            <tr>
                <td style="padding: 6px 12px;">Projected month total</td>
                <td style="padding: 6px 12px; text-align: right;">${projected:,.2f}</td>
            </tr>
        </table>
        """
