"""Sub-scrapers for the Weekly NYC Events section of the daily update email.

Each sub-scraper exposes:
  - ``title``: a short human-readable name for the event source.
  - ``scrape_and_return_html()``: returns an HTML snippet for that source,
    or an empty string if there is nothing to show / scraping failed.

The ``WeeklyNycEventsBot`` orchestrator discovers these, runs each one
defensively, and combines them into a single collapsible email section.
"""
