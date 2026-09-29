"""Constants for daily update lambda."""

# AWS
REGION_NAME = "us-east-1"
DAILY_UPDATES_SECRET_NAME = "daily-updates-secret"
BETHPAGE_SECRET_NAME = "bethpage-secret"

# Bedrock (used for durable LLM-based HTML extraction)
BEDROCK_REGION = "us-east-1"
BEDROCK_MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

# Central Park Public Volunteering
CENTRAL_PARK_PUBLIC_URL = (
    "https://www.centralparknyc.org/volunteer/community-volunteer-days"
)

# Central Park Private / MyImpactPage
MYIMPACTPAGE_BASE_URL = "https://app.betterimpact.com"
MYIMPACTPAGE_LOGIN_URL = f"{MYIMPACTPAGE_BASE_URL}/Login/Login"
MYIMPACTPAGE_OPPORTUNITIES_URL = (
    f"{MYIMPACTPAGE_BASE_URL}/Volunteer/Schedule/Opportunities"
)
MYIMPACTPAGE_BAD_OPPORTUNITY_NAMES = ("Volunteer Development", "Volunteer Training")
MYIMPACTPAGE_NAVBAR_MARKERS = ("Back to Activity List", "Log Out", "Help")

# Late Night Shows (1iota)
IOTIA_BASE_URL = "https://1iota.com/"
# The Late Show with Stephen Colbert ended its run (May 2026) and no longer has
# tapings on 1iota (show/536 returns no ticket calendar), which caused
# "Error finding calendar dates" timeouts. Removed from the scrape list.
IOTIA_SETH_MEYERS_URL = "https://1iota.com/show/461/late-night-with-seth-meyers"
IOTIA_DAILY_SHOW_URL = "https://1iota.com/show/1248/the-daily-show"
IOTIA_FALLON_URL = "https://1iota.com/show/353/the-tonight-show-starring-jimmy-fallon"
IOTIA_URL_TO_SHOW_NAME = {
    IOTIA_SETH_MEYERS_URL: "Late Night with Seth Meyers",
    IOTIA_DAILY_SHOW_URL: "The Daily Show",
    IOTIA_FALLON_URL: "The Tonight Show Starring Jimmy Fallon",
}

# Last Week Tonight with John Oliver (free studio audience tickets)
LAST_WEEK_TONIGHT_URL = "https://www.lastweektickets.com/"

# New York Cares
NEW_YORK_CARES_BASE_URL = "https://www.newyorkcares.org/volunteers?boroughs%5B%5D=Manhattan&days%5B%5D=Saturday&days%5B%5D=Sunday"

# Weekly NYC Events
POPUP_BAGELS_URL = "https://www.popupbagels.com"
TIME_OUT_NYC_BASE_URL = "https://www.timeout.com"
TIME_OUT_NYC_WEEKEND_URL = (
    "https://www.timeout.com/newyork/things-to-do/things-to-do-in-nyc-this-weekend"
)

# Pop-ups & dessert specials (JSON sources)
DONYC_BASE_URL = "https://donyc.com"
DONYC_POPUPS_URL = "https://donyc.com/pop-ups-nyc"
NYC_FOR_FREE_BASE_URL = "https://www.nycforfree.co"
NYC_FOR_FREE_EVENTS_URL = "https://www.nycforfree.co/events"

# How far ahead to surface pop-up / free events (days from today).
POPUP_EVENT_LOOKAHEAD_DAYS = 21

# Scraping limits
MAX_MYIMPACTPAGE_SHIFTS = 30
