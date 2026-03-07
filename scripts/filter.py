#!/usr/bin/env python3
"""
filter.py — Score raw items against the framework using Claude.
Writes scored/YYYY-MM-DD.json with relevance scores attached.
"""

import json
import os
import sys
import datetime
from pathlib import Path

import anthropic
import yaml

ROOT = Path(__file__).parent.parent
CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text())
FRAMEWORK = (ROOT / "FRAMEWORK.md").read_text()

RAW_DIR = ROOT / CONFIG["output"]["raw_dir"]
SCORED_DIR = ROOT / "scored"
SCORED_DIR.mkdir(exist_ok=True)

MODEL = CONFIG["model"]["name"]
THRESHOLD = CONFIG["pipeline"]["relevance_threshold"]
MAX_TO_SCORE = CONFIG["pipeline"]["max_items_to_score"]

SCORE_SYSTEM = f"""You are an editorial analyst for commons-wire, a news digest that applies a specific analytical framework to current events.

Here is the framework:

{FRAMEWORK}

Your job: given a news item (title + summary), output a JSON object with exactly these fields:
- score: integer 0-10 (how relevant/useful this item is for the framework)
- reason: one sentence explaining the score
- angle: if score >= 6, one sentence describing the specific framework angle to use; otherwise null
- category_tag: the most specific applicable framework concept (e.g. "capture sequence", "alibi structure", "commune layer", "fatal strategy", "routing architecture", "prefigurative politics", "enclosure", "reproductive labor"); or null if score < 6

Be strict. Most news is not relevant. Score 6+ only if the item genuinely illuminates the framework, not just vaguely relates to politics or inequality.

Output ONLY valid JSON. No preamble, no backticks."""


def score_item(client, item):
    prompt = f"Title: {item['title']}\n\nSource: {item['source']} ({item['category']})\n\nSummary: {item['summary']}"

    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=300,
            system=SCORE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip()
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  JSON parse error for '{item['title']}': {e}", file=sys.stderr)
        return {"score": 0, "reason": "parse error", "angle": None, "category_tag": None}
    except Exception as e:
        print(f"  API error for '{item['title']}': {e}", file=sys.stderr)
        return {"score": 0, "reason": f"api error: {e}", "angle": None, "category_tag": None}


def main():
    today = datetime.date.today().isoformat()
    raw_path = RAW_DIR / f"{today}.json"

    if not raw_path.exists():
        print(f"No raw items for {today}. Run fetch.py first.", file=sys.stderr)
        sys.exit(1)

    raw_items = json.loads(raw_path.read_text())

    # Load already-scored IDs to avoid re-scoring
    scored_path = SCORED_DIR / f"{today}.json"
    already_scored = {}
    if scored_path.exists():
        for item in json.loads(scored_path.read_text()):
            already_scored[item["id"]] = item

    to_score = [i for i in raw_items if i["id"] not in already_scored]
    # Sort by weight descending so higher-weight sources get priority
    to_score.sort(key=lambda x: -x.get("weight", 1))
    to_score = to_score[:MAX_TO_SCORE]

    if not to_score:
        print("Nothing new to score.")
        # Still write out existing scored items
        all_scored = list(already_scored.values())
        scored_path.write_text(json.dumps(all_scored, indent=2))
        return

    client = anthropic.Anthropic()

    print(f"Scoring {len(to_score)} items...")
    newly_scored = []
    for i, item in enumerate(to_score):
        print(f"  [{i+1}/{len(to_score)}] {item['title'][:70]}")
        result = score_item(client, item)
        scored_item = {**item, **result}
        newly_scored.append(scored_item)
        if result["score"] >= THRESHOLD:
            print(f"    → {result['score']}/10 ✓  {result['reason'][:80]}")
        else:
            print(f"    → {result['score']}/10    {result['reason'][:80]}")

    all_scored = list(already_scored.values()) + newly_scored
    scored_path.write_text(json.dumps(all_scored, indent=2))

    passing = [i for i in all_scored if i.get("score", 0) >= THRESHOLD]
    print(f"\n{len(passing)} items passed threshold {THRESHOLD}+ → {scored_path}")


if __name__ == "__main__":
    main()
