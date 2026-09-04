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
  send_weekly_email_report.py      # Manual runner for the weekly admin email report
  backfill_email_log.py            # One-off: rebuild email history from CloudWatch + snapshots
  lambda_helpers/
    tee_time_filterer.py           # Core filtering logic (day, time, sunset, players, holes)
    bethpage_black_config.py       # User config object with DynamoDB Decimal handling
    date_handler.py                # Ordinal suffix and day-number-to-date conversion
    dynamo_db_connection.py        # All DynamoDB operations for tee times + user configs
    one_time_link_handler.py       # GUID-based auth link generation and validation
    web_scraper.py                 # Selenium scraper for Bethpage tee time site
    email_sender.py                # SES email formatting and sending
    email_log.py                   # Records every notification email sent (for the weekly report)
    weekly_email_report.py         # Builds/sends the weekly "Bethpage Black Bot Email Report"
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
- `lambda/deploy_dynamo_db.sh` — creates the DynamoDB tables (`bethpage-black-bot-config`, `bethpage-black-bot-one-time-links`, `daily-updates-data`, `bethpage-black-bot-email-log`) if missing.

### Weekly admin email report

Every tee time notification is logged to the `bethpage-black-bot-email-log` table by `EmailLog` (one item per user per run, sharing a `run_id`). On the **first scheduled run after 7pm Eastern on a Sunday**, `WeeklyEmailReport.send_report_if_due()` emails the admin address a "Bethpage Black Bot Email Report": a total-emails count plus a table of Email Time / Tee Time Slot / Users Notified. A `weekly-report-sent#<sunday>` marker item in the same table stops later runs that evening from sending a duplicate.

**Timezone:** the lambda runs in UTC, so anything user-facing is stamped Eastern explicitly via `date_handler.EASTERN` / `now_eastern()`. Email-log `id`/`run_id`/`sent_at` are Eastern ISO strings (`2026-08-20T14:18:30-04:00`); `sent_at_epoch` is what the report actually sorts and filters on, so the repeated hour when EDT rolls back to EST can't misorder rows.

The report always covers the **trailing 7 days**, so it can be run and verified on any day:

```bash
cd lambda
python send_weekly_email_report.py --dry-run   # print the HTML
python send_weekly_email_report.py             # actually email it (does not consume the weekly marker)
```

`aws lambda invoke` with `{"action": "send_weekly_email_report"}` does the same thing in the deployed lambda.

**Backfilling history:** `lambda/backfill_email_log.py` reconstructs pre-logging emails by pulling the "Sending tee time notification to X with N new times" lines from CloudWatch Logs Insights and replaying the bot's diff against the `tee-times` snapshot table to recover which slots each user got. Records whose replayed count disagrees with the log line (usually a since-changed user config) are written with `approximate: True`.

```bash
cd lambda
python backfill_email_log.py --days 30 --dry-run   # shows a match rate, writes nothing
python backfill_email_log.py --days 30
```

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

`pytest` suites live in `tests/lambda/` and `tests/daily_update_lambda/`. There is no
`conftest.py` or `pytest.ini`, so **`PYTHONPATH` must point at the lambda directory** —
a bare `pytest` fails collection with `ModuleNotFoundError: No module named 'lambda_helpers'`.

```bash
# Bethpage lambda tests
PYTHONPATH="lambda" python -m pytest tests/lambda -q

# Daily update lambda tests
PYTHONPATH="daily_update_lambda" python -m pytest tests/daily_update_lambda -q

# A single test
PYTHONPATH="lambda" python -m pytest tests/lambda/test_date_handler.py::TestDateHandler::test_get_day_suffix
```

> As of 8/21/2026, `tests/lambda` has 7 pre-existing failures in
> `test_one_time_link_handler.py`, `test_api_gateway_handler.py` and
> `test_dynamo_db_connection.py` — stale expectations that predate
> `validate_one_time_link_and_get_email()` returning a 3-tuple. 96 pass.

## Key Conventions

- DynamoDB Decimal values are converted to Python int/float via `BethpageBlackBotConfig.convert_decimal()` and `ApiGatewayHandler.decimal_default()`.
- Tee time dicts use keys: `Date`, `Time`, `Players`, `Holes` (capitalized).
- User configs are stored in DynamoDB with the user's email as the `id` key.
- `TeeTimeFilterer` connects to DynamoDB in its `__init__` — tests must mock `DynamoDBConnection`.
- A user in the `all-emails` list with **no config row** is skipped with a warning, not notified. `get_user_config_as_object()` returns `None` for them; do not "fix" this by falling back to `BethpageBlackBotConfig()` defaults, which would silently notify them on the default Sat/Sun preferences. (`backfill_email_log.py` deliberately overrides this to replay history, when the bot did use defaults.)
- All secret/AWS access happens through dedicated handler classes (`SecretHandler`, `DailyUpdateSecretHandler`) — mock these at the class level in tests.
- The React frontend lives in `bethpage-black-bot-react/` (separate from the Python lambdas).
