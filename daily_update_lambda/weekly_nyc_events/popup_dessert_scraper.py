import json
import logging
import html as html_module

from weekly_nyc_events.donyc_popups_scraper import DonycPopupsScraper
from weekly_nyc_events.nycforfree_scraper import NycForFreeScraper
from daily_update_helpers.bedrock_extractor import BedrockExtractor

logger = logging.getLogger(__name__)


class PopupDessertScraper:
    """Combines NYC pop-up / dessert event sources into one section.

    Each source is fetched separately as structured JSON (DoNYC pop-ups +
    nycforfree free events), then a single Claude (Bedrock) pass merges them,
    removes duplicates that appear in both feeds, filters to on-theme events
    (pop-up shops, markets, food & dessert specials), and writes short blurbs.
    """

    title = "Pop-Ups & Dessert Specials"
    MAX_DISPLAYED = 12

    # Sources are fetched independently, then combined by the LLM.
    SOURCES = [DonycPopupsScraper, NycForFreeScraper]

    def __init__(self):
        self.extractor = BedrockExtractor()

    def scrape_and_return_html(self):
        logger.info("Starting Pop-Ups & Dessert Specials aggregation")
        by_source = {}
        for source_cls in self.SOURCES:
            try:
                by_source[source_cls.source] = source_cls().fetch_events()
            except Exception as e:
                logger.error("Source %s failed: %s", source_cls.__name__, str(e), exc_info=True)
                by_source[source_cls.source] = []

        if not any(by_source.values()):
            logger.info("No pop-up / dessert events from any source")
            return ""

        events = self._combine(by_source)
        if not events:
            logger.info("No pop-up / dessert events after combining")
            return ""

        logger.info("Combined into %d pop-up / dessert events", len(events))
        return self._build_html(events)

    def _combine(self, by_source):
        """Use Claude to merge, dedupe, filter to theme, and shorten blurbs."""
        prompt = (
            "You are combining NYC event listings from two sources into a single "
            '"Pop-Ups & Dessert Specials" digest.\n\n'
            "Below is JSON with events from each source. Do the following:\n"
            "1. MERGE both lists into one.\n"
            "2. REMOVE duplicates — the same event can appear in both sources or on "
            "multiple dates; keep ONE entry, preferring the one with the most complete "
            "info and a working link.\n"
            "3. KEEP ONLY on-theme events: pop-ups, pop-up shops, markets, brand "
            "activations, and food/dessert specials or promos. DROP generic concerts, "
            "theater, film screenings, sports, and routine fitness/yoga classes.\n"
            "4. For each kept event return an object with EXACTLY these keys:\n"
            '   - "title": clean event name.\n'
            '   - "description": ONE short original sentence (max 20 words), your own '
            "words — do not copy long source text.\n"
            '   - "datetime": keep the given date/time string unchanged (may be empty).\n'
            '   - "location": keep the given location (use "NYC" if empty).\n'
            '   - "link": keep the given link unchanged.\n\n'
            f"Return at most {self.MAX_DISPLAYED} events as a JSON array, soonest first. "
            "Output JSON only, no prose.\n\n"
            f"Sources:\n{json.dumps(by_source, ensure_ascii=False)}"
        )

        events = self.extractor.extract_json(prompt, max_tokens=3000)
        if not isinstance(events, list):
            return []

        cleaned = []
        for e in events:
            if not isinstance(e, dict):
                continue
            title = (e.get("title") or "").strip()
            link = (e.get("link") or "").strip()
            if title and link:
                cleaned.append(
                    {
                        "title": title,
                        "description": (e.get("description") or "").strip(),
                        "datetime": (e.get("datetime") or "").strip(),
                        "location": (e.get("location") or "NYC").strip() or "NYC",
                        "link": link,
                    }
                )
        return cleaned[: self.MAX_DISPLAYED]

    def _build_html(self, events):
        items = ""
        for e in events:
            title = html_module.escape(e["title"])
            url = html_module.escape(e["link"])
            desc = html_module.escape(e["description"])
            desc_html = f" — {desc}" if desc else ""

            meta_bits = []
            if e["datetime"]:
                meta_bits.append(f"📅 {html_module.escape(e['datetime'])}")
            if e["location"]:
                meta_bits.append(f"📍 {html_module.escape(e['location'])}")
            meta_html = ""
            if meta_bits:
                meta_html = (
                    '<br><span style="color: #666; font-size: 0.9em;">'
                    + " · ".join(meta_bits)
                    + "</span>"
                )

            items += (
                '<li style="margin-bottom: 8px;">'
                f'<a href="{url}" target="_blank"><strong>{title}</strong></a>{desc_html}'
                f"{meta_html}</li>"
            )

        return f"""
        <h3 style="margin-bottom: 4px;">🛍️ {html_module.escape(self.title)}</h3>
        <ul style="margin-top: 4px; padding-left: 20px;">
            {items}
        </ul>
        """


# s = PopupDessertScraper()
# print(s.scrape_and_return_html())
