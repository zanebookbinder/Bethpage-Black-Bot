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

## Deploying (Bethpage Black Bot only)

This section covers **only** the Bethpage Black Bot (the React frontend + the `lambda/` backend). The Daily Update Bot has a **separate** deploy process (`daily_update_lambda/deploy_daily_updates_lambda.sh`) — do not use the steps below for it.

Prereqs for any deploy: AWS CLI configured for account `511803112403`, region `us-east-1`. Backend deploys also need Docker running.

### Frontend (React site — `bethpage-black-bot-react/`)

Production is **AWS Amplify Hosting**, app `Bethpage-Black-Bot` (appId `d1rm63vo2b73hl`), branch `main` (stage PRODUCTION, **auto-build ON**), connected to the GitHub repo and serving the custom domain **bethpage-black-bot.com**.

**Deploying = pushing to `main`.** Amplify auto-builds and deploys on every push; there is no manual build/upload step.

```bash
cd bethpage-black-bot-react
CI=true npm test            # optional but recommended: confirm tests pass
CI=true npm run build       # optional but recommended: catch compile errors before pushing

# from repo root, commit the frontend changes and push
git add bethpage-black-bot-react/src/...
git commit -m "..."
git push origin main        # <-- triggers the Amplify production build
```

Monitor the build:

```bash
# list recent builds for the prod branch
aws amplify list-jobs --app-id d1rm63vo2b73hl --branch-name main --max-items 5 \
  --query "jobSummaries[].{jobId:jobId,status:status,commit:commitId,msg:commitMessage}" --output table

# poll a specific job until it reads SUCCEED / FAILED / CANCELLED
aws amplify get-job --app-id d1rm63vo2b73hl --branch-name main --job-id <N> \
  --query "job.summary.status" --output text
```

Console: `https://console.aws.amazon.com/amplify/home?region=us-east-1#/d1rm63vo2b73hl/main`

> Note: `bethpage-black-bot-react/deploy_react_site.sh` is a legacy manual zip-deploy that targets a **different** Amplify app (`bethpage-black-bot-frontend`, appId `d3r6y6jr1uq1dp`) with **no custom domain**. It does **not** deploy production — use `git push origin main` instead.

### Backend (scraper + REST API Lambda — `lambda/`)

One container-image Lambda named **`bethpage-black-bot`** (us-east-1, role `bethpaige-black-bot-role-np1ssf1j`), triggered by EventBridge rule `bethpage-black-bot-schedule` (every 3 min, Mar–Nov) and also fronted by API Gateway for the REST API.

**Deploy = run the script** (builds the linux/amd64 image, pushes to ECR, updates the Lambda code, and idempotently re-applies the EventBridge schedule/permission):

```bash
cd lambda
./deploy.sh
```

Monitor the rollout:

```bash
aws lambda get-function-configuration --function-name bethpage-black-bot \
  --query "{LastUpdateStatus:LastUpdateStatus,LastModified:LastModified,Image:Code.ImageUri}" --output table
# LastUpdateStatus should be "Successful"

aws logs tail /aws/lambda/bethpage-black-bot --follow   # live logs
```

**Infra scripts — run only when that infrastructure changes, not on every deploy:**
- `lambda/deploy_api_gateway.sh` — (re)creates the `bethpage-black-bot-api` API Gateway (stage `prod`) and its routes/integration to the Lambda. Run when API routes change.
- `lambda/deploy_dynamo_db.sh` — creates the DynamoDB tables (`bethpage-black-bot-config`, `bethpage-black-bot-one-time-links`) if missing.

## Deploying the Daily Update Bot

Separate from the Bethpage Black Bot above. The Daily Update Bot is one container-image Lambda named **`daily-update-bot`** (us-east-1, role `bethpaige-black-bot-role-np1ssf1j` — note the legacy misspelling, shared with the Bethpage Lambda), triggered by EventBridge rule `daily-update-bot-schedule` (`cron(0 0 * * ? *)` — midnight UTC / 7pm EST daily). It sends one combined email; some bots use Bedrock (`us.anthropic.claude-haiku-4-5-20251001-v1:0`) for HTML extraction, so the role needs `bedrock:InvokeModel`.

Prereqs: AWS CLI configured for account `511803112403`, region `us-east-1`, and **Docker running**.

**Deploy = run the script** (builds the linux/amd64 image, pushes to ECR repo `daily-update-docker-image`, updates the Lambda code, and idempotently re-applies the EventBridge schedule/permission):

```bash
cd daily_update_lambda
./deploy_daily_updates_lambda.sh
```

Monitor the rollout:

```bash
aws lambda get-function-configuration --function-name daily-update-bot \
  --query "{LastUpdateStatus:LastUpdateStatus,LastModified:LastModified,Image:Code.ImageUri}" --output table
# LastUpdateStatus should be "Successful"

aws logs tail /aws/lambda/daily-update-bot --follow   # live logs
```

> Do **not** test by invoking the function — it sends a real daily email. Rely on the deploy output, `LastUpdateStatus: Successful`, and a matching `CodeSha256` instead. The Dockerfile uses `COPY . ./`, so new modules/sub-scrapers are packaged automatically.

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
