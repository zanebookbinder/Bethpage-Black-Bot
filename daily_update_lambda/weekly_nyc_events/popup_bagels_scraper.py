import logging
import html as html_module

import requests
from bs4 import BeautifulSoup

from daily_update_helpers.daily_update_constants import POPUP_BAGELS_URL

logger = logging.getLogger(__name__)


class PopupBagelsScraper:
    """Scrapes PopUp Bagels' homepage for the current rotating schmear flavors.

    The homepage renders a "Schmears of the Week" section whose items carry
    CSS-module class names (e.g. ``SpreadList_spreads_item_title__3fl_H``).
    The hashed suffix can change between site builds, so we match on the
    stable class-name prefix rather than the full class.
    """

    title = "PopUp Bagels — Weekly Schmears"

    # Only the rotating specials are interesting; the "Classic" schmears are
    # always available, so they're dropped. The site's "Limited"/"Upcoming"
    # categories map to this-week / next-week and sort in that order.
    CATEGORY_ORDER = {"Limited": 0, "Upcoming": 1}

    def __init__(self):
        self.url = POPUP_BAGELS_URL
        self.session = requests.Session()

    def scrape_and_return_html(self):
        logger.info("Starting PopUp Bagels schmear scrape")
        try:
            response = self.session.get(
                self.url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            schmears = self._parse_schmears(soup)
            if not schmears:
                logger.info("No PopUp Bagels schmears found")
                return ""

            logger.info("Found %d PopUp Bagels schmears", len(schmears))
            return self._build_html(schmears)
        except Exception as e:
            logger.error("Error scraping PopUp Bagels: %s", str(e), exc_info=True)
            return ""

    def _parse_schmears(self, soup):
        titles = [
            t
            for t in soup.find_all("h3")
            if self._class_has(t, "SpreadList_spreads_item_title")
        ]

        schmears = []
        for h3 in titles:
            name = h3.get_text(strip=True)
            category = self._find_category(h3)
            # Skip "Classic" (always-available) and anything uncategorized.
            if not name or category not in self.CATEGORY_ORDER:
                continue
            schmears.append(
                {
                    "name": name,
                    "category": category,
                    "base": self._find_base(h3),
                    "availability": self._availability_label(category, self._find_date(h3)),
                }
            )

        schmears.sort(key=lambda s: self.CATEGORY_ORDER.get(s["category"], 99))
        return schmears

    @staticmethod
    def _availability_label(category, date):
        """Map the site's category to a friendly when-it's-available label."""
        if category == "Limited":
            return "This Week"
        if category == "Upcoming":
            return f"Next Week ({date})" if date else "Next Week"
        return category

    def _find_category(self, title_tag):
        """Category label (Limited / Upcoming / Classic) that follows the title."""
        for el in title_tag.find_all_next():
            if el.name == "h3" and self._class_has(el, "SpreadList_spreads_item_title"):
                break  # reached the next item without finding a category
            if self._class_has(el, "SpreadList_spreads_item_category"):
                return el.get_text(strip=True)
        return ""

    def _find_base(self, title_tag):
        """Base ingredient badge (e.g. Cream Cheese / Butter) precedes the title."""
        badge = title_tag.find_previous("span")
        return badge.get_text(strip=True) if badge else ""

    def _find_date(self, title_tag):
        """Availability date (e.g. "June 25") that follows the title, if any."""
        for el in title_tag.find_all_next():
            if el.name == "h3" and self._class_has(el, "SpreadList_spreads_item_title"):
                break  # reached the next item without finding a date
            if self._class_has(el, "SpreadList_spreads_item_date"):
                return el.get_text(strip=True)
        return ""

    @staticmethod
    def _class_has(tag, prefix):
        return any(c.startswith(prefix) for c in (tag.get("class") or []))

    def _build_html(self, schmears):
        cell_style = "border: 1px solid #ddd; padding: 8px;"
        rows = ""
        for s in schmears:
            name = html_module.escape(s["name"])
            availability = html_module.escape(s["availability"]) or "—"
            base = html_module.escape(s["base"]) or "—"
            rows += (
                "<tr>"
                f'<td style="{cell_style}">{name}</td>'
                f'<td style="{cell_style}">{availability}</td>'
                f'<td style="{cell_style}">{base}</td>'
                "</tr>"
            )

        return f"""
        <h3 style="margin-bottom: 4px;">🥯 {html_module.escape(self.title)}</h3>
        <table style="width:100%; border-collapse: collapse;">
            <thead>
                <tr style="background-color: #f0f0f0;">
                    <th style="{cell_style} text-align: left;">Flavor</th>
                    <th style="{cell_style} text-align: left;">Availability</th>
                    <th style="{cell_style} text-align: left;">Base</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        <p style="margin-top: 4px;">
            <a href="{html_module.escape(self.url)}" target="_blank">popupbagels.com</a>
        </p>
        """


# s = PopupBagelsScraper()
# print(s.scrape_and_return_html())
