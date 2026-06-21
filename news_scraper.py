"""
News scraper for SafeSteps.

Pulls crime-related articles from Mumbai news RSS feeds, classifies
them by incident type using keyword matching, extracts the likely
locality mentioned in the headline, geocodes it via Nominatim
(OpenStreetMap's free geocoder), and inserts them as Incident rows
with source=news_scraper and status=verified.

This is intentionally simple — keyword matching rather than NLP/ML
classification. It's good enough to seed historical data for the
heatmap and the eventual crime prediction model. Accuracy can be
improved later without changing the pipeline shape.
"""

import re
import logging
import feedparser
import urllib.request
from datetime import datetime, timezone
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

from models import Incident, IncidentType, IncidentStatus, IncidentSource

logger = logging.getLogger(__name__)

# Many news sites reject requests with the default Python/feedparser
# user-agent string, returning a 403. Spoofing a normal browser
# user-agent avoids this without doing anything deceptive — we're
# reading the same public RSS feed a browser would.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch_feed(url: str):
    """
    Fetches and parses an RSS feed with a browser user-agent header,
    since many sites 403 the default feedparser/urllib agent string.
    """
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as response:
        raw = response.read()
    return feedparser.parse(raw)


# ─────────────────────────────────────────────
# RSS feed sources
#
# Direct city-section feed IDs on TOI/Mid-Day change without notice
# and are prone to silently redirecting to the wrong city or 404ing.
# Google News RSS search feeds are far more stable since they're
# query-based rather than tied to an internal category ID, so we
# use one as the primary reliable source and keep the direct feeds
# as a secondary attempt.
# ─────────────────────────────────────────────

RSS_FEEDS = {
    "Google News - Mumbai Crime": (
        "https://news.google.com/rss/search?"
        "q=mumbai+crime+OR+police+OR+arrested&hl=en-IN&gl=IN&ceid=IN:en"
    ),
}


# ─────────────────────────────────────────────
# Keyword classification
# Each incident type maps to keywords we look
# for in the headline + summary. First match wins.
# Order matters — more specific terms first.
# ─────────────────────────────────────────────

TYPE_KEYWORDS = {
    IncidentType.assault:    ["assault", "attacked", "stabbed", "beaten", "murder", "killed", "shot", "thrashed"],
    IncidentType.robbery:    ["robbed", "robbery", "looted", "snatched", "dacoity", "extortion"],
    IncidentType.theft:      ["theft", "stolen", "burglary", "pickpocket", "duped", "duping", "fraud", "cheated", "swindled"],
    IncidentType.harassment: ["harassment", "molested", "stalking", "eve-teasing", "abused"],
    IncidentType.vandalism:  ["vandalism", "vandalised", "defaced", "arson"],
}

# Words that must appear somewhere for the article to be crime-relevant at all.
# Filters out unrelated Mumbai news (traffic, weather, politics, etc.)
CRIME_SIGNAL_WORDS = [
    "police", "fir", "arrested", "accused", "victim", "crime",
    "held", "booked", "probe", "custody", "court", "case filed",
    *[kw for kws in TYPE_KEYWORDS.values() for kw in kws]
]

# Known Mumbai localities — used to extract location from headline text.
# Not exhaustive, but covers the areas your project already references.
MUMBAI_AREAS = [
    "Kurla", "BKC", "Bandra Kurla Complex", "Bandra", "Andheri", "Dadar",
    "Tilak Nagar", "Chembur", "Worli", "Colaba", "Fort", "Churchgate",
    "Vile Parle", "Santacruz", "Khar", "Juhu", "Goregaon", "Malad",
    "Kandivali", "Borivali", "Mulund", "Bhandup", "Ghatkopar", "Vikhroli",
    "Powai", "Sion", "Matunga", "Mahim", "Lower Parel", "Parel",
    "Byculla", "Mazgaon", "Wadala", "Antop Hill", "Govandi", "Mankhurd",
    "Thane", "Navi Mumbai", "Vashi", "Panvel", "Kalyan", "Dombivli",
]


def classify_incident_type(text: str) -> IncidentType | None:
    """
    Returns the first matching IncidentType based on keyword presence,
    or None if no crime keywords match at all (article is irrelevant).
    """
    text_lower = text.lower()

    for incident_type, keywords in TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return incident_type

    return None


def is_crime_relevant(text: str) -> bool:
    """Quick filter — does this article even mention crime-adjacent terms?"""
    text_lower = text.lower()
    return any(word in text_lower for word in CRIME_SIGNAL_WORDS)


def extract_area(text: str) -> str | None:
    """
    Looks for a known Mumbai locality name in the article text.
    Returns the first match, or None if no known area is mentioned.

    Many crime articles (especially fraud/cybercrime) don't name a
    specific locality at all — just "Mumbai Police" generically.
    Callers should treat None as "use city-level fallback", not as
    "discard the article" — see FALLBACK_AREA below.
    """
    for area in MUMBAI_AREAS:
        # word boundary match so "Sion" doesn't match inside "Mission"
        if re.search(rf"\b{re.escape(area)}\b", text, re.IGNORECASE):
            return area
    return None


# Used when an article is clearly Mumbai crime news but names no
# specific locality. Better to place it at a city-center reference
# point than to silently drop real data.
FALLBACK_AREA = "Mumbai"


# ─────────────────────────────────────────────
# Geocoding
#
# Nominatim's usage policy caps requests at 1/second per client.
# Sending requests back-to-back (as a tight loop over articles
# would) triggers 429 Too Many Requests almost immediately.
#
# geopy's RateLimiter wraps the geocode call and automatically
# waits between requests to stay under that limit. We also cache
# results in-memory per scrape run, since "Mumbai" and other
# common areas repeat across many articles in the same batch —
# no reason to re-geocode the same string twice.
# ─────────────────────────────────────────────

from geopy.extra.rate_limiter import RateLimiter

_geolocator = Nominatim(user_agent="safesteps-mumbai-crime-map")
_rate_limited_geocode = RateLimiter(_geolocator.geocode, min_delay_seconds=1.1)

_geocode_cache: dict[str, tuple[float, float] | None] = {
    # Pre-seeded coordinates for all MUMBAI_AREAS.
    # Eliminates Nominatim API calls for known localities — faster,
    # no rate-limit issues, and these coordinates don't change.
    "Kurla":               (19.0726, 72.8794),
    "BKC":                 (19.0590, 72.8640),
    "Bandra Kurla Complex":(19.0590, 72.8640),
    "Bandra":              (19.0544, 72.8401),
    "Andheri":             (19.1197, 72.8464),
    "Dadar":               (19.0184, 72.8440),
    "Tilak Nagar":         (19.0429, 72.8895),
    "Chembur":             (19.0522, 72.8967),
    "Worli":               (19.0176, 72.8152),
    "Colaba":              (18.9067, 72.8147),
    "Fort":                (18.9338, 72.8355),
    "Churchgate":          (18.9322, 72.8264),
    "Vile Parle":          (19.0991, 72.8432),
    "Santacruz":           (19.0833, 72.8382),
    "Khar":                (19.0726, 72.8365),
    "Juhu":                (19.1075, 72.8263),
    "Goregaon":            (19.1551, 72.8493),
    "Malad":               (19.1874, 72.8484),
    "Kandivali":           (19.2042, 72.8527),
    "Borivali":            (19.2285, 72.8569),
    "Mulund":              (19.1726, 72.9561),
    "Bhandup":             (19.1480, 72.9370),
    "Ghatkopar":           (19.0866, 72.9081),
    "Vikhroli":            (19.1098, 72.9275),
    "Powai":               (19.1176, 72.9060),
    "Sion":                (19.0404, 72.8621),
    "Matunga":             (19.0275, 72.8558),
    "Mahim":               (19.0423, 72.8407),
    "Lower Parel":         (18.9941, 72.8310),
    "Parel":               (19.0011, 72.8401),
    "Byculla":             (18.9788, 72.8329),
    "Mazgaon":             (18.9683, 72.8440),
    "Wadala":              (19.0179, 72.8685),
    "Antop Hill":          (19.0320, 72.8700),
    "Govandi":             (19.0464, 72.9104),
    "Mankhurd":            (19.0493, 72.9290),
    "Thane":               (19.2183, 72.9781),
    "Navi Mumbai":         (19.0330, 73.0297),
    "Vashi":               (19.0771, 72.9986),
    "Panvel":              (18.9894, 73.1175),
    "Kalyan":              (19.2437, 73.1355),
    "Dombivli":            (19.2183, 73.0867),
    "Mumbai":              (19.0760, 72.8777),   # city-level fallback
}


def geocode_area(area: str) -> tuple[float, float] | None:
    """
    Converts an area name to (lat, lng) using Nominatim, respecting
    the 1 req/sec rate limit and caching results within a run so
    repeated areas (very common — "Mumbai" appears constantly)
    don't trigger redundant network calls.
    """
    if area in _geocode_cache:
        return _geocode_cache[area]

    result = None
    try:
        query = f"{area}, Mumbai, Maharashtra, India"
        location = _rate_limited_geocode(query, timeout=10)
        if location:
            result = (location.latitude, location.longitude)
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        logger.warning(f"[Scraper] Geocoding failed for '{area}': {e}")

    _geocode_cache[area] = result
    return result


# ─────────────────────────────────────────────
# Main scrape function
# Called by the Celery task — takes a DB session
# (sync session, since Celery workers are sync)
# ─────────────────────────────────────────────

def scrape_and_store(db_session, seen_urls: set[str]) -> dict:
    """
    Fetches all configured RSS feeds, filters for crime-relevant
    articles, classifies + geocodes them, and inserts new Incident
    rows. Returns a summary dict of what happened.

    `seen_urls` should be the set of article URLs already stored as
    source_url on existing Incident rows (loaded by the caller), so
    we skip articles we've already inserted in a previous run.
    """
    summary = {
        "feeds_checked":  0,
        "articles_seen":  0,
        "crime_relevant": 0,
        "geocoded":       0,
        "inserted":       0,
        "skipped_duplicate": 0,
        "skipped_no_area":   0,
        "skipped_no_type":   0,
    }

    for source_name, feed_url in RSS_FEEDS.items():
        summary["feeds_checked"] += 1
        logger.info(f"[Scraper] Fetching {source_name}")

        try:
            feed = fetch_feed(feed_url)
        except Exception as e:
            logger.error(f"[Scraper] Failed to fetch {source_name}: {e}")
            continue

        for entry in feed.entries:
            summary["articles_seen"] += 1

            title   = entry.get("title", "")
            summary_text = entry.get("summary", "")
            link    = entry.get("link", "")
            full_text = f"{title} {summary_text}"

            # skip if not crime-relevant at all
            if not is_crime_relevant(full_text):
                continue
            summary["crime_relevant"] += 1

            # dedup check — has this exact article URL been stored before?
            if link in seen_urls:
                summary["skipped_duplicate"] += 1
                continue

            # classify incident type
            incident_type = classify_incident_type(full_text)
            if not incident_type:
                summary["skipped_no_type"] += 1
                continue

            # extract area — fall back to city-level if no specific
            # locality is named, rather than discarding real crime data
            area = extract_area(full_text)
            is_fallback = False
            if not area:
                area = FALLBACK_AREA
                is_fallback = True

            # geocode
            coords = geocode_area(area)
            if not coords:
                continue
            lat, lng = coords

            # When using the city-level fallback, add a small random offset
            # (~2-3 km radius) so incidents scatter across Mumbai on the
            # heatmap instead of stacking at one single point.
            if is_fallback:
                import random
                lat += random.uniform(-0.025, 0.025)
                lng += random.uniform(-0.025, 0.025)

            summary["geocoded"] += 1

            # parse publish date — fall back to now if missing
            occurred_at = datetime.now(timezone.utc)
            if entry.get("published_parsed"):
                occurred_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

            # insert incident — auto-verified since it's from a published source
            incident = Incident(
                reported_by=None,                       # no human reporter
                source=IncidentSource.news_scraper,
                source_url=link,
                incident_type=incident_type,
                description=title,
                area=area,
                city="Mumbai",
                state="Maharashtra",
                latitude=lat,
                longitude=lng,
                occurred_at=occurred_at,
                status=IncidentStatus.verified,          # auto-verified, see note below
                is_anonymous=False,
            )
            db_session.add(incident)
            seen_urls.add(link)
            summary["inserted"] += 1

    db_session.commit()
    logger.info(f"[Scraper] Run complete: {summary}")
    return summary