"""
One-off debug script — run this locally to see exactly what
articles are coming through the feeds and why they pass/fail
each filter stage. Delete once the scraper is tuned correctly.

Run with: python debug_scraper.py
"""

from news_scraper import (
    RSS_FEEDS, fetch_feed, is_crime_relevant,
    classify_incident_type, extract_area
)

for source_name, feed_url in RSS_FEEDS.items():
    print(f"\n{'='*60}")
    print(f"SOURCE: {source_name}")
    print('='*60)

    try:
        feed = fetch_feed(feed_url)
    except Exception as e:
        print(f"FAILED TO FETCH: {e}")
        continue

    print(f"Entries found: {len(feed.entries)}\n")

    for entry in feed.entries:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        full_text = f"{title} {summary}"

        relevant = is_crime_relevant(full_text)
        itype    = classify_incident_type(full_text) if relevant else None
        area     = extract_area(full_text) if relevant else None

        marker = "✓" if (relevant and itype and area) else ("~" if relevant else " ")
        print(f"[{marker}] {title}")
        if relevant:
            print(f"      type={itype}, area={area}")