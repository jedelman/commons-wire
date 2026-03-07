#!/usr/bin/env python3
"""
fetch.py — Pull RSS feeds, deduplicate, write raw items to raw/YYYY-MM-DD.json
"""

import json
import os
import sys
import hashlib
import datetime
from pathlib import Path

import feedparser
import yaml

ROOT = Path(__file__).parent.parent
CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text())
FEEDS = yaml.safe_load((ROOT / "feeds.yaml").read_text())["feeds"]

RAW_DIR = ROOT / CONFIG["output"]["raw_dir"]
RAW_DIR.mkdir(exist_ok=True)

LOOKBACK = datetime.timedelta(days=CONFIG["pipeline"]["lookback_days"])
CUTOFF = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) - LOOKBACK


def item_id(entry):
    """Stable ID for deduplication — prefer entry id, fall back to url hash."""
    raw = getattr(entry, "id", None) or getattr(entry, "link", "") or entry.get("title", "")
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def parse_date(entry):
    """Return a UTC datetime or None."""
    for field in ("published_parsed", "updated_parsed"):
        t = getattr(entry, field, None)
        if t:
            try:
                return datetime.datetime(*t[:6])
            except Exception:
                pass
    return None


def fetch_feed(feed_config):
    """Fetch one feed, return list of item dicts."""
    url = feed_config["url"]
    weight = feed_config.get("weight", 1)
    category = feed_config.get("category", "uncategorized")
    name = feed_config["name"]

    try:
        parsed = feedparser.parse(url, agent="commons-wire/1.0 (+https://github.com/jedelman/commons-wire)")
    except Exception as e:
        print(f"  ERROR fetching {name}: {e}", file=sys.stderr)
        return []

    items = []
    for entry in parsed.entries:
        pub = parse_date(entry)
        if pub and pub < CUTOFF:
            continue  # too old

        # Extract best available summary
        summary = ""
        if hasattr(entry, "summary"):
            summary = entry.summary
        elif hasattr(entry, "content"):
            summary = entry.content[0].get("value", "")
        # Strip HTML tags crudely (avoid dependency on bs4 for a simple field)
        import re
        summary = re.sub(r"<[^>]+>", " ", summary).strip()
        summary = re.sub(r"\s+", " ", summary)[:800]

        items.append({
            "id": item_id(entry),
            "source": name,
            "category": category,
            "weight": weight,
            "title": getattr(entry, "title", ""),
            "url": getattr(entry, "link", ""),
            "summary": summary,
            "published": pub.isoformat() if pub else None,
            "fetched_at": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat(),
        })

    print(f"  {name}: {len(items)} items in window")
    return items


def main():
    today = datetime.date.today().isoformat()
    out_path = RAW_DIR / f"{today}.json"

    # Load existing IDs to deduplicate across runs
    seen_ids = set()
    if out_path.exists():
        existing = json.loads(out_path.read_text())
        seen_ids = {item["id"] for item in existing}
    else:
        existing = []

    new_items = []
    for feed in FEEDS:
        print(f"Fetching: {feed['name']}")
        items = fetch_feed(feed)
        for item in items:
            if item["id"] not in seen_ids:
                seen_ids.add(item["id"])
                new_items.append(item)

    all_items = existing + new_items
    out_path.write_text(json.dumps(all_items, indent=2))
    print(f"\nTotal: {len(all_items)} items ({len(new_items)} new) → {out_path}")
    return len(all_items)


if __name__ == "__main__":
    main()
