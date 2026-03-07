#!/usr/bin/env python3
"""
write.py — Turn top-scored items into published posts via the blogging agent.
Writes posts/YYYY-MM-DD-slug.md committed to git.
"""

import json
import os
import re
import sys
import datetime
from pathlib import Path

import anthropic
import yaml

ROOT = Path(__file__).parent.parent
CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text())
FRAMEWORK = (ROOT / "FRAMEWORK.md").read_text()

SCORED_DIR = ROOT / "scored"
POSTS_DIR = ROOT / CONFIG["output"]["posts_dir"]
POSTS_DIR.mkdir(exist_ok=True)

MODEL = CONFIG["model"]["name"]
MAX_TOKENS = CONFIG["model"]["max_tokens"]
THRESHOLD = CONFIG["pipeline"]["relevance_threshold"]
PRIORITY = CONFIG["pipeline"]["priority_threshold"]
MAX_POSTS = CONFIG["pipeline"]["max_posts_per_run"]

WRITE_SYSTEM = f"""You are the writer for commons-wire — a news analysis digest that applies a specific analytical framework to current events. The framework is:

{FRAMEWORK}

When given a news item (title, source, summary) and an editorial angle, write a short analytical post.

Requirements:
- 400–700 words
- Open with the specific story — one concrete event or moment, not a general claim
- Apply one or two tools from the framework explicitly — name them, use them precisely
- Say what most coverage is missing
- Land on something generative: what does this moment reveal, and what does it imply for building alternatives?
- No jargon without translation. If you use a framework concept, define it in the same sentence.
- Analytical point of view is legitimate. Polemic is not.
- No padding. Every sentence must pull weight.
- End with a plain-language title (not clickbait) and a one-sentence description

Output format — EXACTLY this structure, no other text:

---
title: [title here]
description: [one sentence]
source: [source name]
source_url: [url]
category: [category_tag from scoring]
date: [YYYY-MM-DD]
---

[body of post here]"""


def slugify(title):
    s = title.lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s.strip())
    return s[:60].rstrip("-")


def post_already_exists(url):
    """Check if we've already written about this URL."""
    for p in POSTS_DIR.glob("*.md"):
        if url in p.read_text():
            return True
    return False


def write_post(client, item):
    today = datetime.date.today().isoformat()
    prompt = (
        f"Title: {item['title']}\n"
        f"Source: {item['source']}\n"
        f"URL: {item['url']}\n"
        f"Summary: {item['summary']}\n\n"
        f"Editorial angle: {item.get('angle', 'Apply the most relevant framework tools.')}\n"
        f"Framework concept: {item.get('category_tag', 'general')}"
    )

    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=WRITE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip()
    except Exception as e:
        print(f"  API error writing '{item['title']}': {e}", file=sys.stderr)
        return None


def save_post(content, item, today):
    """Parse the post output and save to posts/."""
    # Extract title for slug
    title_match = re.search(r"^title:\s*(.+)$", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else item["title"]
    slug = slugify(title)
    fname = POSTS_DIR / f"{today}-{slug}.md"

    # Avoid overwriting
    if fname.exists():
        fname = POSTS_DIR / f"{today}-{slug}-2.md"

    fname.write_text(content)
    print(f"  → Saved: {fname.name}")
    return fname


def main():
    today = datetime.date.today().isoformat()
    scored_path = SCORED_DIR / f"{today}.json"

    if not scored_path.exists():
        print(f"No scored items for {today}. Run filter.py first.", file=sys.stderr)
        sys.exit(1)

    scored = json.loads(scored_path.read_text())

    # Filter to passing items not yet written
    candidates = [
        i for i in scored
        if i.get("score", 0) >= THRESHOLD and not post_already_exists(i.get("url", ""))
    ]

    # Priority items first, then by score
    candidates.sort(key=lambda x: (-int(x.get("score", 0) >= PRIORITY), -x.get("score", 0)))
    candidates = candidates[:MAX_POSTS]

    if not candidates:
        print("No new items to write.")
        return 0

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    written = 0

    print(f"Writing {len(candidates)} post(s)...")
    for item in candidates:
        print(f"\n  [{item['score']}/10] {item['title'][:70]}")
        content = write_post(client, item)
        if content:
            save_post(content, item, today)
            written += 1

    print(f"\n{written} post(s) written.")
    return written


if __name__ == "__main__":
    main()
