#!/usr/bin/env python3
"""
generate_index.py — Read posts/*.md, build:
  - posts/YYYY-MM-DD-slug.html  (one per post)
  - index.html                  (full listing)
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
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm, text[m.end():]

def first_paragraph(body):
    for para in body.strip().split("\n\n"):
        clean = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", para)
        clean = re.sub(r"[*_`>]", "", clean).strip()
        if clean and not clean.startswith("#"):
            return clean[:220] + ("…" if len(clean) > 220 else "")
    return ""

def md_to_html(body):
    """Convert the post markdown body to HTML. Handles paragraphs,
    blockquotes, inline bold/italic/links. No external deps."""
    lines = body.strip().split("\n")
    html = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Blockquote — collect consecutive > lines
        if line.startswith("> "):
            block = []
            while i < len(lines) and lines[i].startswith("> "):
                block.append(inline(lines[i][2:]))
                i += 1
            html.append("<blockquote>" + " ".join(block) + "</blockquote>")
            continue

        # Heading
        if line.startswith("## "):
            html.append(f"<h2>{inline(line[3:])}</h2>")
            i += 1
            continue
        if line.startswith("# "):
            html.append(f"<h2>{inline(line[2:])}</h2>")
            i += 1
            continue

        # Blank line — separator
        if not line.strip():
            i += 1
            continue

        # Paragraph — collect until blank line
        para = []
        while i < len(lines) and lines[i].strip() and not lines[i].startswith("> ") and not lines[i].startswith("#"):
            para.append(lines[i])
            i += 1
        text = " ".join(para)
        if text:
            html.append(f"<p>{inline(text)}</p>")

    return "\n      ".join(html)

def inline(text):
    """Process inline markdown: links, bold, italic."""
    # Links: [text](url)
    text = re.sub(
        r"\[([^\]]+)\]\(([^\)]+)\)",
        r'<a href="\2" class="xl" target="_blank" rel="noopener">\1</a>',
        text
    )
    # Bold
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    # Italic (not inside words)
    text = re.sub(r"(?<!\w)\*([^*]+)\*(?!\w)", r"<em>\1</em>", text)
    text = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", r"<em>\1</em>", text)
    return text

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

SHARED_CSS = """
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --ink: #1a1714; --paper: #f2ece0; --paper-mid: #e8dfc8;
      --red: #a0291c; --rule: rgba(26,23,20,0.18); --rule-strong: rgba(26,23,20,0.45);
      --display: 'Cormorant Garamond', Georgia, serif;
      --body: 'Lora', Georgia, serif; --mono: 'DM Mono', monospace;
      --max: 680px; --gutter: clamp(1.5rem, 5vw, 4rem);
    }
    html { font-size: 18px; scroll-behavior: smooth; }
    body { background: var(--paper); color: var(--ink); font-family: var(--body); line-height: 1.75; -webkit-font-smoothing: antialiased; }
    header { border-bottom: 2px solid var(--ink); padding: 1.25rem var(--gutter) 1rem; }
    .header-inner { max-width: var(--max); margin: 0 auto; display: flex; align-items: baseline; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
    .site-name { font-family: var(--display); font-size: clamp(1rem,2.5vw,1.2rem); font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink); text-decoration: none; }
    .site-name:hover { color: var(--red); }
    .header-links { display: flex; gap: 1.5rem; align-items: baseline; }
    .header-link { font-family: var(--mono); font-size: 0.6rem; letter-spacing: 0.1em; text-transform: uppercase; color: rgba(26,23,20,0.45); text-decoration: none; }
    .header-link:hover { color: var(--red); }
    .page-wrap { max-width: var(--max); margin: 0 auto; padding: 0 var(--gutter); }
    .xl { color: var(--red); text-decoration: none; border-bottom: 1px solid rgba(160,41,28,0.28); transition: border-color 0.15s; }
    .xl:hover { border-bottom-color: var(--red); }
    footer { border-top: 1px solid var(--rule); padding: 2rem 0 3rem; display: flex; flex-direction: column; gap: 0.5rem; }
    .footer-note { font-family: var(--mono); font-size: 0.6rem; letter-spacing: 0.08em; text-transform: uppercase; color: rgba(26,23,20,0.35); }
    .footer-link { color: rgba(26,23,20,0.35); text-decoration: none; }
    .footer-link:hover { color: var(--red); }"""

SHARED_HEADER = """  <header>
    <div class="header-inner">
      <a href="../index.html" class="site-name">Commons Wire</a>
      <nav class="header-links">
        <a href="https://jedelman.github.io/power-explained" class="header-link">Power Explained</a>
        <a href="https://github.com/jedelman/commons-wire" class="header-link">Source</a>
      </nav>
    </div>
  </header>"""

FONTS = """  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,600&family=DM+Mono:wght@400;500&family=Lora:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet" />"""

def render_post_html(post, prev_post=None, next_post=None):
    label = category_label(post["category"])
    date_str = format_date(post["date"])
    body_html = md_to_html(post["body"])

    prev_link = ""
    next_link = ""
    if next_post:
        next_link = f'<a href="{next_post["slug"]}.html" class="nav-link nav-next">← {next_post["title"]}</a>'
    if prev_post:
        prev_link = f'<a href="{prev_post["slug"]}.html" class="nav-link nav-prev">{prev_post["title"]} →</a>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{post['title']} — Commons Wire</title>
  <meta name="description" content="{post['description']}" />
{FONTS}
  <style>
{SHARED_CSS}
    .kicker {{ padding: clamp(2rem,5vw,3.5rem) 0 1.5rem; border-bottom: 1px solid var(--rule-strong); margin-bottom: 2rem; }}
    .kicker-label {{ font-family: var(--mono); font-size: 0.62rem; letter-spacing: 0.14em; text-transform: uppercase; color: var(--red); display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; }}
    .kicker-label::before {{ content: ''; display: block; width: 2rem; height: 1px; background: var(--red); flex-shrink: 0; }}
    .kicker-date {{ font-family: var(--mono); font-size: 0.6rem; letter-spacing: 0.1em; text-transform: uppercase; color: rgba(26,23,20,0.4); }}
    h1 {{ font-family: var(--display); font-size: clamp(2rem,7vw,3.2rem); font-weight: 700; line-height: 1.05; margin-bottom: 1rem; }}
    .dek {{ font-family: var(--display); font-size: clamp(1.05rem,2.5vw,1.25rem); font-style: italic; color: rgba(26,23,20,0.7); line-height: 1.55; }}
    .body-text {{ padding: 2rem 0; }}
    .body-text p {{ margin-bottom: 1.4rem; font-size: 1rem; line-height: 1.85; }}
    .body-text h2 {{ font-family: var(--display); font-size: 1.5rem; font-weight: 700; margin: 2rem 0 0.75rem; }}
    .body-text blockquote {{ border-left: 2px solid var(--rule-strong); padding: 0.25rem 0 0.25rem 1.25rem; margin: 1.5rem 0; color: rgba(26,23,20,0.75); font-style: italic; }}
    .source-line {{ font-family: var(--mono); font-size: 0.6rem; letter-spacing: 0.1em; text-transform: uppercase; color: rgba(26,23,20,0.4); padding: 1.5rem 0; border-top: 1px solid var(--rule); }}
    .source-line a {{ color: rgba(26,23,20,0.4); text-decoration: none; }}
    .source-line a:hover {{ color: var(--red); }}
    .post-nav {{ display: flex; justify-content: space-between; padding: 1.5rem 0; border-top: 1px solid var(--rule); gap: 1rem; flex-wrap: wrap; }}
    .nav-link {{ font-family: var(--mono); font-size: 0.6rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink); text-decoration: none; max-width: 45%; line-height: 1.5; }}
    .nav-link:hover {{ color: var(--red); }}
    .nav-prev {{ margin-left: auto; text-align: right; }}
    @keyframes fadeUp {{ from {{ opacity: 0; transform: translateY(12px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    .kicker {{ animation: fadeUp 0.6s ease both; }}
  </style>
</head>
<body>

{SHARED_HEADER}

  <main class="page-wrap">
    <div class="kicker">
      <div class="kicker-label">{label}</div>
      <div class="kicker-date">{date_str}</div>
    </div>

    <h1>{post['title']}</h1>
    <p class="dek">{post['description']}</p>

    <div class="body-text">
      {body_html}
    </div>

    <div class="source-line">
      Via <a href="{post['source_url']}" target="_blank" rel="noopener">{post['source']}</a>
    </div>

    <nav class="post-nav">
      {next_link}
      {prev_link}
    </nav>

  </main>

  <footer class="page-wrap">
    <span class="footer-note">
      <a href="../index.html" class="footer-link">← All dispatches</a>
    </span>
    <span class="footer-note">
      Built with <a href="https://github.com/jedelman/commons-wire" class="footer-link">commons-wire</a>
      — <a href="https://jedelman.github.io/power-explained" class="footer-link">Power Explained</a>
    </span>
  </footer>

</body>
</html>"""


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
            "body": body,
        })
    return posts


def render_index(posts):
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
          <a href="posts/{p['slug']}.html" class="post-link">{p['title']}</a>
        </h2>
        <p class="post-lede">{p['lede']}</p>
        <div class="post-source">
          Via <a href="{p['source_url']}" class="source-link" target="_blank" rel="noopener">{p['source']}</a>
        </div>
      </article>"""

    if not posts:
        post_html = '<p class="empty">No posts yet. First run coming soon.</p>'

    count_str = f"{len(posts)} dispatch{'es' if len(posts) != 1 else ''}"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Commons Wire</title>
  <meta name="description" content="Daily dispatches applying a framework to current events. Power, capture, and the commons — in the news." />
{FONTS}
  <style>
{SHARED_CSS}
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

    # Render individual post HTML files
    for i, post in enumerate(posts):
        prev_post = posts[i - 1] if i > 0 else None          # newer
        next_post = posts[i + 1] if i < len(posts) - 1 else None  # older
        html = render_post_html(post, prev_post, next_post)
        out = POSTS_DIR / f"{post['slug']}.html"
        out.write_text(html)

    # Render index
    html = render_index(posts)
    (ROOT / "index.html").write_text(html)

    print(f"Generated {len(posts)} post HTML file(s) + index.html")


if __name__ == "__main__":
    main()
