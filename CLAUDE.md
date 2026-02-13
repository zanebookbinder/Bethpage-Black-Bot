# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Two AWS Lambda functions that scrape websites and send email notifications:

1. **Bethpage Black Bot** (`lambda/`): Scrapes Bethpage Black golf course for tee times every 5 minutes via EventBridge. Filters per-user preferences, diffs against DynamoDB state, and emails new matches via SES. Also serves a REST API (API Gateway) for user registration, config management, and one-time auth links.

2. **Daily Update Lambda** (`daily_update_lambda/`): Aggregates data from multiple scrapers (late night show tickets from 1iota, New York Cares volunteering, Central Park public/private volunteering) and sends a combined daily email.

## Architecture

Both lambdas follow the same pattern: entry point → orchestrator bot → helpers (web scraper, DB connection, email sender, secret handler).

**Bethpage Lambda entry point:** `lambda/main.py:lambda_handler` — routes to `ApiGatewayHandler` (if `routeKey` in event) or `BethpageBlackBot` (scheduled invocation).

**Daily Update entry point:** `daily_update_lambda/daily_update_lambda.py:lambda_handler` — runs all 4 bots sequentially, combines HTML, sends one email.

**Key pattern:** Web scrapers use Selenium with headless Chrome. The shared Chrome setup for daily_update_lambda is in `daily_update_helpers/chrome_helper.py`. The Bethpage lambda has its own Chrome setup inline in `lambda/lambda_helpers/web_scraper.py`.

**External dependencies:** AWS (DynamoDB, SES, Secrets Manager via boto3), Selenium/Chrome, astral (sunset calculations), holidays, requests, BeautifulSoup.

## Lambda Directory Layouts

```
lambda/
  main.py                          # Lambda handler, routes API vs scheduled
  bethpage_black_bot.py            # Orchestrates scrape → filter → diff → notify
  api_gateway_handler.py           # REST API routing and response formatting
  lambda_helpers/
    tee_time_filterer.py           # Core filtering logic (day, time, sunset, players, holes)
    bethpage_black_config.py       # User config object with DynamoDB Decimal handling
    date_handler.py                # Ordinal suffix and day-number-to-date conversion
    dynamo_db_connection.py        # All DynamoDB operations for tee times + user configs
    one_time_link_handler.py       # GUID-based auth link generation and validation
    web_scraper.py                 # Selenium scraper for Bethpage tee time site
    email_sender.py                # SES email formatting and sending
    secret_handler.py              # AWS Secrets Manager access

daily_update_lambda/
  daily_update_lambda.py           # Lambda handler, runs all bots
  late_night_show_bot.py           # 1iota late night show ticket scraper
  new_york_cares_bot.py            # NY Cares volunteering scraper
  central_park_public_volunteering_bot.py   # Central Park community days (requests/BS4)
  central_park_private_volunteering_bot.py  # MyImpactPage scraper (Selenium, login required)
  daily_update_helpers/
    chrome_helper.py               # Shared headless Chrome driver factory
    daily_update_constants.py      # URLs, table names, scraping limits
    daily_updates_dynamo_db_connection.py  # DynamoDB for daily update state
    daily_updates_email_service.py # Combined email sender
    daily_updates_secret_handler.py # Secrets Manager for daily update credentials
    late_night_web_scraper.py      # Selenium scraper + WaitlistEntry data class
    new_york_cares_web_scraper.py  # Selenium scraper + travel time enrichment
    myimpactpage_web_scraper.py    # Selenium scraper for Better Impact
    travel_time_calculation_service.py  # Google Maps Distance Matrix API wrapper
```

## Running Tests

No test framework is currently configured. When adding tests, use `pytest`:

```bash
# Install test dependencies
pip install pytest

# Run all tests
pytest

# Run a single test file
pytest tests/test_date_handler.py

# Run a specific test
pytest tests/test_date_handler.py::TestDateHandler::test_get_day_suffix
```

## Key Conventions

- DynamoDB Decimal values are converted to Python int/float via `BethpageBlackBotConfig.convert_decimal()` and `ApiGatewayHandler.decimal_default()`.
- Tee time dicts use keys: `Date`, `Time`, `Players`, `Holes` (capitalized).
- User configs are stored in DynamoDB with the user's email as the `id` key.
- `TeeTimeFilterer` connects to DynamoDB in its `__init__` — tests must mock `DynamoDBConnection`.
- All secret/AWS access happens through dedicated handler classes (`SecretHandler`, `DailyUpdateSecretHandler`) — mock these at the class level in tests.
- The React frontend lives in `bethpage-black-bot-react/` (separate from the Python lambdas).
