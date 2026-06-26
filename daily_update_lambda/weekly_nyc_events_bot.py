import logging

from weekly_nyc_events.popup_bagels_scraper import PopupBagelsScraper
from weekly_nyc_events.timeout_weekend_scraper import TimeoutWeekendScraper
from weekly_nyc_events.popup_dessert_scraper import PopupDessertScraper

logger = logging.getLogger(__name__)


class WeeklyNycEventsBot:
    """Aggregates weekly NYC event sub-scrapers into one collapsible email section.

    Add new sources by appending their scraper class to ``SCRAPERS``. Each
    scraper must expose a ``title`` attribute and a ``scrape_and_return_html()``
    method returning an HTML snippet (or "" when there is nothing to show).
    """

    SCRAPERS = [TimeoutWeekendScraper, PopupDessertScraper, PopupBagelsScraper]

    def scrape_data_and_return_email_html(self):
        logger.info("Starting Weekly NYC Events aggregation")
        sections = []
        for scraper_cls in self.SCRAPERS:
            name = scraper_cls.__name__
            try:
                html = scraper_cls().scrape_and_return_html()
            except Exception as e:
                logger.error("Sub-scraper %s failed: %s", name, str(e), exc_info=True)
                html = ""
            if html and html.strip():
                sections.append(html)
            else:
                logger.info("Sub-scraper %s produced no content", name)

        if not sections:
            logger.info("No Weekly NYC Events content to show")
            return ""

        return self._wrap_collapsible(sections)

    def _wrap_collapsible(self, sections):
        """Wrap the sections in a <details> element so the block is collapsible.

        <details>/<summary> is supported by Apple Mail and several other
        clients. Clients that strip it (e.g. Gmail) simply render the inner
        content expanded, which degrades gracefully.
        """
        inner = '<hr style="border:none;border-top:1px solid #eee;">'.join(sections)
        return f"""
        <details open style="margin-top: 8px;">
            <summary style="font-size: 1.5em; font-weight: bold; cursor: pointer;">
                🗽 Weekly NYC Events
            </summary>
            <div style="margin-top: 8px;">
                {inner}
            </div>
        </details>
        """


# bot = WeeklyNycEventsBot()
# print(bot.scrape_data_and_return_email_html())
