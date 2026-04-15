import logging
import html as html_module

from daily_update_helpers.nyc_tennis_web_scraper import NycTennisWebScraper

logger = logging.getLogger(__name__)


class NycTennisBot:
    def scrape_data_and_return_email_html(self):
        logger.info("Starting NYC tennis reservation scrape")
        scraper = NycTennisWebScraper()
        try:
            reservations = scraper.scrape_weekend_reservations()
            if not reservations:
                logger.info("No available NYC tennis reservations found")
                return ""
            return self._build_html(reservations)
        except Exception as e:
            logger.error("Error scraping NYC tennis: %s", str(e), exc_info=True)
            return ""
        finally:
            scraper.quit()

    def _build_html(self, reservations):
        """
        Build an HTML table from reservations.
        reservations: list of (date_obj, date_label, {time: [urls]}) sorted by date.
        """
        cell_style = "border: 1px solid #ddd; padding: 8px;"
        table_rows = ""

        for _date_obj, date_label, time_slots in reservations:
            entries = list(time_slots.items())
            date_cell = html_module.escape(date_label)

            for i, (time_label, links) in enumerate(entries):
                links_html = " &nbsp; ".join(
                    f'<a href="{html_module.escape(link)}" target="_blank">Reserve {j}</a>'
                    for j, link in enumerate(links, 1)
                )
                row = "<tr>"
                if i == 0:
                    row += f'<td style="{cell_style}" rowspan="{len(entries)}">{date_cell}</td>'
                row += f'<td style="{cell_style}">{html_module.escape(time_label)}</td>'
                row += f'<td style="{cell_style}">{links_html}</td>'
                row += "</tr>"
                table_rows += row

        return f"""
        <h2>NYC Tennis Court Reservations (Weekends Only)</h2>
        <table style="width:100%; border-collapse: collapse;">
            <thead>
                <tr style="background-color: #f0f0f0;">
                    <th style="{cell_style} text-align: left;">Date</th>
                    <th style="{cell_style} text-align: left;">Time</th>
                    <th style="{cell_style} text-align: left;">Available Courts</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
        """


# logging.basicConfig(level=logging.INFO)
# bot = NycTennisBot()
# result = bot.scrape_data_and_return_email_html()
# print(result)
