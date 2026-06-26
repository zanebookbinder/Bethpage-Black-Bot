import re
import json
import logging
import html as html_module

import requests
from bs4 import BeautifulSoup

from daily_update_helpers.daily_update_constants import (
    TIME_OUT_NYC_BASE_URL,
    TIME_OUT_NYC_WEEKEND_URL,
)
from daily_update_helpers.bedrock_extractor import BedrockExtractor

logger = logging.getLogger(__name__)


class TimeoutWeekendScraper:
    """Scrapes Time Out's "things to do in NYC this weekend" roundup.

    Time Out keeps a stable URL that refreshes weekly, so we hit the same page
    each run with no date math. Their class names are obfuscated and change
    often, so rather than hand-tuning selectors we loosely gather candidate
    cards and let Claude (via Bedrock) pick the real events and write concise
    blurbs.

    Copyright note: Time Out's writeups are copyrighted editorial. We only show
    the event title, a short *original* one-line blurb, and a link back to their
    page so the click lands on them.
    """

    title = "Time Out — This Weekend in NYC"

    # Bound how many candidates we hand the model and how many we display.
    MAX_CANDIDATES = 30
    MAX_DISPLAYED = 12

    def __init__(self):
        self.url = TIME_OUT_NYC_WEEKEND_URL
        self.session = requests.Session()
        self.extractor = BedrockExtractor()

    def scrape_and_return_html(self):
        logger.info("Starting Time Out weekend scrape")
        try:
            response = self.session.get(
                self.url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            candidates = self._gather_candidates(soup)
            if not candidates:
                logger.info("No Time Out candidates found")
                return ""

            events = self._extract_events(candidates, self._page_heading(soup))
            if not events:
                logger.info("No Time Out events extracted")
                return ""

            logger.info("Extracted %d Time Out events", len(events))
            return self._build_html(events, self._page_heading(soup))
        except Exception as e:
            logger.error("Error scraping Time Out weekend: %s", str(e), exc_info=True)
            return ""

    def _page_heading(self, soup):
        """The roundup's own headline, e.g. '...this weekend: June 19-21'."""
        if soup.title:
            return soup.title.get_text(strip=True)
        h1 = soup.find("h1")
        return h1.get_text(strip=True) if h1 else ""

    def _gather_candidates(self, soup):
        """Loosely collect (title, url, snippet) cards, keeping the richest per title."""
        best = {}
        for card in soup.select("article, [class*='card'], [class*='tile'], li"):
            heading = card.find(["h2", "h3"])
            link = card.find("a", href=True)
            if not (heading and link):
                continue

            raw_title = heading.get_text(strip=True)
            title = re.sub(r"^\s*\d+\.\s*", "", raw_title).strip()
            if len(title) <= 3:
                continue

            snippet = card.get_text(" ", strip=True).replace(raw_title, "", 1).strip()
            snippet = re.sub(r"\s+", " ", snippet)[:300]
            url = self._absolute_url(link["href"])

            if title not in best or len(snippet) > len(best[title]["snippet"]):
                best[title] = {"title": title, "url": url, "snippet": snippet}

        return list(best.values())[: self.MAX_CANDIDATES]

    def _extract_events(self, candidates, heading):
        """Use Claude to filter candidates to real events with original blurbs."""
        prompt = (
            "You are cleaning up scraped data from Time Out's "
            f'"{heading or "things to do in NYC this weekend"}" page.\n\n'
            "Below is a JSON list of candidate cards (title, url, snippet) scraped "
            "from the page. Return ONLY the entries that are real things to do this "
            "weekend in NYC. Drop navigation, generic venue/landing pages, ads, and "
            "duplicates.\n\n"
            "For each kept entry return an object with:\n"
            '  - "title": the clean event name (no leading numbers).\n'
            '  - "blurb": ONE short, original sentence (max 18 words) describing it '
            "IN YOUR OWN WORDS. Do NOT copy Time Out's wording.\n"
            '  - "url": the url unchanged.\n\n'
            f"Return at most {self.MAX_DISPLAYED} entries as a JSON array, preserving "
            "the original order. Output JSON only, no prose.\n\n"
            f"Candidates:\n{json.dumps(candidates, ensure_ascii=False)}"
        )

        events = self.extractor.extract_json(prompt, max_tokens=2048)
        if not isinstance(events, list):
            return []

        cleaned = []
        for e in events:
            if not isinstance(e, dict):
                continue
            title = (e.get("title") or "").strip()
            url = self._absolute_url((e.get("url") or "").strip())
            blurb = (e.get("blurb") or "").strip()
            if title and url:
                cleaned.append({"title": title, "url": url, "blurb": blurb})
        return cleaned[: self.MAX_DISPLAYED]

    @staticmethod
    def _absolute_url(href):
        if not href:
            return ""
        if href.startswith("http"):
            return href
        return TIME_OUT_NYC_BASE_URL + href

    def _build_html(self, events, heading):
        items = ""
        for e in events:
            title = html_module.escape(e["title"])
            url = html_module.escape(e["url"])
            blurb = html_module.escape(e["blurb"])
            blurb_html = f' — {blurb}' if blurb else ""
            items += (
                '<li style="margin-bottom: 6px;">'
                f'<a href="{url}" target="_blank"><strong>{title}</strong></a>{blurb_html}'
                "</li>"
            )

        subtitle = ""
        if heading:
            subtitle = f'<p style="margin: 0 0 6px; color: #666;">{html_module.escape(heading)}</p>'

        return f"""
        <h3 style="margin-bottom: 4px;">🗓️ {html_module.escape(self.title)}</h3>
        {subtitle}
        <ul style="margin-top: 4px; padding-left: 20px;">
            {items}
        </ul>
        <p style="margin-top: 4px;">
            <a href="{html_module.escape(self.url)}" target="_blank">See the full list on Time Out</a>
        </p>
        """


# s = TimeoutWeekendScraper()
# print(s.scrape_and_return_html())
