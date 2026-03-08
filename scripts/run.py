#!/usr/bin/env python3
"""
run.py — Orchestrate the full commons-wire pipeline.

Usage:
    python scripts/run.py              # full run
    python scripts/run.py --fetch-only # stop after fetching
    python scripts/run.py --score-only # fetch + score, no writing
    python scripts/run.py --dry-run    # fetch + score, print candidates without writing
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import fetch
import filter as score_module
import write as write_module
import generate_index
import yaml

CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text())


def git_commit_posts():
    """Commit any new posts to git."""
    try:
        subprocess.run(["git", "config", "user.email", "claude@anthropic.com"], cwd=ROOT, check=True)
        subprocess.run(["git", "config", "user.name", "Claude"], cwd=ROOT, check=True)

        result = subprocess.run(
            ["git", "status", "--porcelain", "posts/"],
            cwd=ROOT, capture_output=True, text=True
        )
        if not result.stdout.strip():
            print("No new posts to commit.")
            return

        today = datetime.date.today().isoformat()
        subprocess.run(["git", "add", "posts/"], cwd=ROOT, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"posts: {today}"],
            cwd=ROOT, check=True
        )
        print("Committed new posts to git.")
    except subprocess.CalledProcessError as e:
        print(f"Git error: {e}", file=sys.stderr)


def print_candidates(today):
    """Print scored candidates without writing (--dry-run)."""
    scored_path = ROOT / "scored" / f"{today}.json"
    if not scored_path.exists():
        print("No scored items.")
        return

    scored = json.loads(scored_path.read_text())
    threshold = CONFIG["pipeline"]["relevance_threshold"]
    candidates = [i for i in scored if i.get("score", 0) >= threshold]
    candidates.sort(key=lambda x: -x.get("score", 0))

    print(f"\n{'='*60}")
    print(f"Candidates (score >= {threshold}):")
    print(f"{'='*60}")
    for item in candidates:
        print(f"\n  [{item['score']}/10] {item['title']}")
        print(f"  {item['source']} | {item.get('category_tag', '—')}")
        print(f"  Angle: {item.get('angle', '—')}")
        print(f"  URL: {item['url']}")


def main():
    parser = argparse.ArgumentParser(description="commons-wire pipeline")
    parser.add_argument("--fetch-only", action="store_true")
    parser.add_argument("--score-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    today = datetime.date.today().isoformat()
    print(f"\ncommons-wire | {today}")
    print("=" * 40)

    if not args.fetch_only and not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY is not set.", file=sys.stderr)
        sys.exit(1)

    # ── Stage 1: Fetch ─────────────────────────────────────────────
    print("\n[1/3] Fetching feeds...")
    n_items = fetch.main()

    if args.fetch_only:
        return

    # ── Stage 2: Score ─────────────────────────────────────────────
    print("\n[2/3] Scoring items...")
    score_module.main()

    if args.score_only:
        print_candidates(today)
        print("\nRegenerating index.html...")
        generate_index.main()
        return

    if args.dry_run:
        print_candidates(today)
        return

    # ── Stage 3: Write ─────────────────────────────────────────────
    print("\n[3/3] Writing posts...")
    n_written = write_module.main()

    # ── Stage 3b: Regenerate index ────────────────────────────────────
    print("\n[3b] Regenerating index.html...")
    generate_index.main()

    # ── Stage 4: Commit ────────────────────────────────────────────
    if CONFIG["output"]["git_commit"] and n_written:
        print("\n[4/4] Committing to git...")
        git_commit_posts()

    print(f"\nDone. {n_written} post(s) published.")


if __name__ == "__main__":
    main()
