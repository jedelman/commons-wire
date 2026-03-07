#!/usr/bin/env python3
"""
generate_index.py — Read posts/*.md, build index.html in repo root.
Run after write.py. Called automatically by the Actions pipeline.
"""

import re
import os
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
POSTS_DIR = ROOT / "posts"

CATEGORY_LABELS = {
    "epistemic incompetence of centralization": "Epistemic failure",
    "capture sequence":      "Capture",
    "alibi structure":       "Alibi",
    "commune layer":         "Commons",
    "fatal strategy":        "Fatal strategy",
    "routing architecture":  "Routing",
    "prefigurative politics":"Prefigurative",
    "enclosure":             "Enclosure",
    "reproductive labor":    "Reproductive labor",
    "general":               "Analysis",
}

def parse_frontmatter(text):
    """Extract YAML-ish frontmatter from a markdown file."""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    body = text[m.end():]
    return fm, body


def first_paragraph(body):
    """Return the first non-empty paragraph of the post body."""
    for para in body.strip().split("\n\n"):
        clean = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", para)  # strip links
        clean = re.sub(r"[*_`>]", "", clean).strip()
        if clean and not clean.startswith("#"):
            return clean[:220] + ("…" if len(clean) > 220 else "")
    return ""


def load_posts():
    posts = []
    for path in sorted(POSTS_DIR.glob("*.md"), reverse=True):
        text = path.read_text()
        fm, body = parse_frontmatter(text)
        if not fm.get("title"):
            continue
        posts.append({
            "slug": path.stem,
            "title": fm.get("title", ""),
            "description": fm.get("description", ""),
            "source": fm.get("source", ""),
            "source_url": fm.get("source_url", ""),
            "category": fm.get("category", "general"),
            "date": fm.get("date", ""),
            "lede": first_paragraph(body),
            "path": f"posts/{path.name}",
        })
    return posts


def category_label(cat):
    for k, v in CATEGORY_LABELS.items():
        if k in cat.lower():
            return v
    return "Analysis"


def format_date(d):
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%B %-d, %Y")
    except Exception:
        return d


def render(posts):
    post_html = ""
    for p in posts:
        label = category_label(p["category"])
        date_str = format_date(p["date"])
        post_html += f"""
      <article class="post-card">
        <div class="post-meta">
          <span class="post-label">{label}</span>
          <span class="post-date">{date_str}</span>
        </div>
        <h2 class="post-title">
          <a href="{p['path']}" class="post-link">{p['title']}</a>
        </h2>
        <p class="post-lede">{p['lede']}</p>
        <div class="post-source">
          Via <a href="{p['source_url']}" class="source-link" target="_blank" rel="noopener">{p['source']}</a>
        </div>
      </article>"""

    if not posts:
        post_html = '<p class="empty">No posts yet. First run coming soon.</p>'

    count = len(posts)
    count_str = f"{count} dispatch{'es' if count != 1 else ''}"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Commons Wire</title>
  <meta name="description" content="Daily dispatches applying a framework to current events. Power, capture, and the commons — in the news." />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,600&family=DM+Mono:wght@400;500&family=Lora:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet" />
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --ink: #1a1714; --paper: #f2ece0; --paper-mid: #e8dfc8;
      --red: #a0291c; --rule: rgba(26,23,20,0.18); --rule-strong: rgba(26,23,20,0.45);
      --display: 'Cormorant Garamond', Georgia, serif;
      --body: 'Lora', Georgia, serif; --mono: 'DM Mono', monospace;
      --max: 680px; --gutter: clamp(1.5rem, 5vw, 4rem);
    }}
    html {{ font-size: 18px; scroll-behavior: smooth; }}
    body {{ background: var(--paper); color: var(--ink); font-family: var(--body); line-height: 1.75; -webkit-font-smoothing: antialiased; }}

    header {{ border-bottom: 2px solid var(--ink); padding: 1.25rem var(--gutter) 1rem; }}
    .header-inner {{ max-width: var(--max); margin: 0 auto; display: flex; align-items: baseline; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }}
    .site-name {{ font-family: var(--display); font-size: clamp(1rem,2.5vw,1.2rem); font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink); text-decoration: none; }}
    .site-name:hover {{ color: var(--red); }}
    .header-links {{ display: flex; gap: 1.5rem; align-items: baseline; }}
    .header-link {{ font-family: var(--mono); font-size: 0.6rem; letter-spacing: 0.1em; text-transform: uppercase; color: rgba(26,23,20,0.45); text-decoration: none; }}
    .header-link:hover {{ color: var(--red); }}

    .page-wrap {{ max-width: var(--max); margin: 0 auto; padding: 0 var(--gutter); }}

    .hero {{ padding: clamp(2.5rem,6vw,4rem) 0 2rem; border-bottom: 1px solid var(--rule-strong); }}
    .hero-label {{ font-family: var(--mono); font-size: 0.62rem; letter-spacing: 0.14em; text-transform: uppercase; color: var(--red); display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.25rem; }}
    .hero-label::before {{ content: ''; display: block; width: 2rem; height: 1px; background: var(--red); flex-shrink: 0; }}
    .hero h1 {{ font-family: var(--display); font-size: clamp(2.5rem,8vw,4rem); font-weight: 700; line-height: 1.0; margin-bottom: 1rem; }}
    .hero-dek {{ font-family: var(--display); font-size: clamp(1.05rem,2.5vw,1.3rem); font-style: italic; color: rgba(26,23,20,0.7); line-height: 1.55; max-width: 500px; }}

    .posts-header {{ padding: 1.5rem 0 0.75rem; display: flex; align-items: baseline; justify-content: space-between; border-bottom: 1px solid var(--rule); }}
    .posts-count {{ font-family: var(--mono); font-size: 0.6rem; letter-spacing: 0.12em; text-transform: uppercase; color: rgba(26,23,20,0.4); }}

    .posts {{ padding: 0 0 4rem; }}

    .post-card {{ padding: 2rem 0; border-bottom: 1px solid var(--rule); }}
    .post-card:last-child {{ border-bottom: none; }}

    .post-meta {{ display: flex; gap: 1rem; align-items: baseline; margin-bottom: 0.6rem; flex-wrap: wrap; }}
    .post-label {{ font-family: var(--mono); font-size: 0.58rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--red); }}
    .post-date {{ font-family: var(--mono); font-size: 0.58rem; letter-spacing: 0.08em; text-transform: uppercase; color: rgba(26,23,20,0.4); }}

    .post-title {{ font-family: var(--display); font-size: clamp(1.3rem,3.5vw,1.8rem); font-weight: 700; line-height: 1.15; margin-bottom: 0.75rem; }}
    .post-link {{ color: var(--ink); text-decoration: none; }}
    .post-link:hover {{ color: var(--red); }}

    .post-lede {{ font-size: 0.95rem; line-height: 1.8; color: rgba(26,23,20,0.8); margin-bottom: 0.75rem; }}

    .post-source {{ font-family: var(--mono); font-size: 0.58rem; letter-spacing: 0.08em; text-transform: uppercase; color: rgba(26,23,20,0.4); }}
    .source-link {{ color: rgba(26,23,20,0.4); text-decoration: none; }}
    .source-link:hover {{ color: var(--red); }}

    .empty {{ font-family: var(--display); font-style: italic; color: rgba(26,23,20,0.4); padding: 3rem 0; }}

    footer {{ border-top: 1px solid var(--rule); padding: 2rem 0 3rem; display: flex; flex-direction: column; gap: 0.5rem; }}
    .footer-note {{ font-family: var(--mono); font-size: 0.6rem; letter-spacing: 0.08em; text-transform: uppercase; color: rgba(26,23,20,0.35); }}
    .footer-link {{ color: rgba(26,23,20,0.35); text-decoration: none; }}
    .footer-link:hover {{ color: var(--red); }}

    @keyframes fadeUp {{ from {{ opacity: 0; transform: translateY(12px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    .hero {{ animation: fadeUp 0.6s ease both; }}
  </style>
</head>
<body>

  <header>
    <div class="header-inner">
      <a href="index.html" class="site-name">Commons Wire</a>
      <nav class="header-links">
        <a href="https://jedelman.github.io/power-explained" class="header-link">Power Explained</a>
        <a href="https://github.com/jedelman/commons-wire" class="header-link">Source</a>
      </nav>
    </div>
  </header>

  <main class="page-wrap">

    <div class="hero">
      <div class="hero-label">Daily dispatches</div>
      <h1>Commons<br/>Wire</h1>
      <p class="hero-dek">Current events read against a framework. Power, capture, and the commons — in the news today.</p>
    </div>

    <div class="posts-header">
      <span class="posts-count">{count_str}</span>
    </div>

    <div class="posts">
      {post_html}
    </div>

  </main>

  <footer class="page-wrap">
    <span class="footer-note">
      Built with <a href="https://github.com/jedelman/commons-wire" class="footer-link">commons-wire</a>
      — open source, forkable. Framework: <a href="https://jedelman.github.io/power-explained" class="footer-link">Power Explained</a>.
    </span>
    <span class="footer-note">Public domain. Share freely.</span>
  </footer>

</body>
</html>"""


def main():
    posts = load_posts()
    html = render(posts)
    out = ROOT / "index.html"
    out.write_text(html)
    print(f"index.html written — {len(posts)} post(s)")


if __name__ == "__main__":
    main()
