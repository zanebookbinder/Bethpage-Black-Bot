"""Constants for daily update lambda."""

# AWS
REGION_NAME = "us-east-1"
DAILY_UPDATES_SECRET_NAME = "daily-updates-secret"
BETHPAGE_SECRET_NAME = "bethpage-secret"

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
IOTIA_COLBERT_URL = "https://1iota.com/show/536/the-late-show-with-stephen-colbert"
IOTIA_SETH_MEYERS_URL = "https://1iota.com/show/461/late-night-with-seth-meyers"
IOTIA_DAILY_SHOW_URL = "https://1iota.com/show/1248/the-daily-show"
IOTIA_FALLON_URL = "https://1iota.com/show/353/the-tonight-show-starring-jimmy-fallon"
IOTIA_URL_TO_SHOW_NAME = {
    IOTIA_COLBERT_URL: "The Late Show with Stephen Colbert",
    IOTIA_SETH_MEYERS_URL: "Late Night with Seth Meyers",
    IOTIA_DAILY_SHOW_URL: "The Daily Show",
    IOTIA_FALLON_URL: "The Tonight Show Starring Jimmy Fallon",
}

# New York Cares
NEW_YORK_CARES_BASE_URL = "https://www.newyorkcares.org/volunteers?boroughs%5B%5D=Manhattan&days%5B%5D=Saturday&days%5B%5D=Sunday"

# Scraping limits
MAX_MYIMPACTPAGE_SHIFTS = 30
