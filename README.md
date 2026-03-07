# commons-wire

A daily news digest that applies a specific analytical framework to current events.
Runs autonomously via GitHub Actions. Posts committed to this repo as markdown.

Built to feed [Power Explained](https://jedelman.github.io/power-explained) but
designed to be forked and run against any analytical framework.

---

## How it works

1. **Fetch** — pulls RSS feeds from `feeds.yaml`, deduplicates, stores raw items
2. **Score** — Claude scores each item 0–10 against the framework in `FRAMEWORK.md`
3. **Write** — items scoring 6+ become 400–700 word analytical posts
4. **Commit** — posts are committed to `posts/` and pushed to this repo

Runs daily at 7am UTC via GitHub Actions.

---

## Setup

### Fork this repo

```bash
git clone https://github.com/jedelman/commons-wire
cd commons-wire
```

### Add your API key

In your fork: **Settings → Secrets and variables → Actions → New repository secret**

- Name: `ANTHROPIC_API_KEY`
- Value: your Anthropic API key

### Customize

- **`feeds.yaml`** — add or remove sources. The pipeline picks them up automatically.
- **`FRAMEWORK.md`** — replace with your own analytical framework.
- **`config.yaml`** — adjust thresholds, model, max posts per run.

### Run locally

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here

# Full run
python scripts/run.py

# Fetch and score only (no writing, no API cost from writing stage)
python scripts/run.py --score-only

# See what would be written without actually writing
python scripts/run.py --dry-run
```

### Trigger manually

In GitHub: **Actions → Daily digest → Run workflow**

Use the dry-run option to preview candidates before committing to writing.

---

## Workflow

**Daily (automated):** Fetch + score runs at 7am UTC. Results committed to `scored/YYYY-MM-DD.json`. The Actions log shows candidates with scores and angles — review these and write posts here or manually.

**Manual dispatch:** Actions → Daily digest → Run workflow → choose mode:
- `score-only` — fetch, score, commit results, print candidates (default)
- `dry-run` — same but no commit
- `full` — fetch, score, and write posts automatically

---

## Output

Posts land in `posts/` as markdown with frontmatter:

```
---
title: ...
description: ...
source: ...
source_url: ...
category: ...
date: YYYY-MM-DD
---

[post body]
```

From here you can pipe them anywhere: Substack, Ghost, atproto, a static site,
a newsletter — whatever. The posts directory is the interface.

---

## Adding sources

Edit `feeds.yaml`. Each source needs:

```yaml
- name: Source Name
  url: https://example.com/feed.xml
  category: labor   # for your own filtering/tagging
  weight: 2         # optional, 1-3, boosts priority in scoring queue
```

The pipeline will start ingesting new sources on the next run. Over time,
high-signal sources reveal themselves through their scoring patterns. Low-signal
sources can be removed or down-weighted.

---

## Cost

Each daily run uses approximately:
- 40 scoring calls × ~400 tokens = ~16k tokens input for scoring
- 3 writing calls × ~1500 tokens = ~4.5k tokens output for writing
- Estimated: **$0.05–0.15/day** at current claude-sonnet-4 pricing

Adjust `max_items_to_score` and `max_posts_per_run` in `config.yaml` to control cost.

---

## License

Public domain. Fork it, run it, change the framework entirely.
