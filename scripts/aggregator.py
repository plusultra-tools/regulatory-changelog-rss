#!/usr/bin/env python3
"""Aggregate EU regulatory RSS/Atom feeds, filter by keyword, emit feed.xml + index.html + weekly digest.

Stdlib only. Python 3.10+.

Usage:
    python scripts/aggregator.py --output web/
    python scripts/aggregator.py --help
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import logging
import re
import socket
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

USER_AGENT = "regulatory-changelog-rss/0.1 (+https://github.com/example/regulatory-changelog-rss)"

SOURCES: list[dict[str, str]] = [
    {"id": "eur-lex",          "name": "EUR-Lex recent legal content",   "url": "https://eur-lex.europa.eu/EN/display-feed.rss?myRssId=recent"},
    {"id": "ec-press",         "name": "Commission press releases",      "url": "https://ec.europa.eu/commission/presscorner/api/rss?language=en"},
    {"id": "ec-digital",       "name": "Commission digital-strategy",    "url": "https://digital-strategy.ec.europa.eu/en/news-redirect/rss.xml"},
    {"id": "edpb",             "name": "EDPB latest outputs",            "url": "https://www.edpb.europa.eu/feeds/news_en.rss"},
    {"id": "edps",             "name": "EDPS news",                      "url": "https://www.edps.europa.eu/rss.xml"},
    {"id": "enisa",            "name": "ENISA news",                     "url": "https://www.enisa.europa.eu/news/RSS"},
    {"id": "dg-sante",         "name": "DG SANTE health-data",           "url": "https://health.ec.europa.eu/rss_en"},
    {"id": "dg-connect",       "name": "DG CONNECT digital-policy",      "url": "https://digital-strategy.ec.europa.eu/en/policies/rss.xml"},
]

KEYWORDS: list[str] = [
    "GDPR", "EHDS", "CRA", "AI Act", "NIS2", "DORA",
    "MDR", "DSA", "DGA", "eIDAS", "Data Act", "ePrivacy",
]

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "dc":   "http://purl.org/dc/elements/1.1/",
}

MAX_FEED_ITEMS = 100
MAX_HTML_ITEMS = 30
DEFAULT_TIMEOUT = 15.0

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Item:
    title: str
    link: str
    pub_date: str  # ISO 8601, UTC
    source_id: str
    source_name: str
    summary: str
    matched: tuple[str, ...] = field(default_factory=tuple)

    @property
    def uid(self) -> str:
        basis = self.link or self.title
        return hashlib.sha1(basis.encode("utf-8")).hexdigest()

# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

def fetch_feed(url: str, timeout: float = DEFAULT_TIMEOUT) -> str | None:
    """Fetch URL and return body text, or None on failure. Never raises."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9, */*;q=0.5",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, socket.timeout,
            ConnectionError, TimeoutError, ValueError) as exc:
        logging.warning("fetch_feed: %s failed: %s", url, exc)
        return None
    except Exception as exc:  # noqa: BLE001 — graceful in all paths
        logging.warning("fetch_feed: %s unexpected: %s", url, exc)
        return None

# ---------------------------------------------------------------------------
# Parse
# ---------------------------------------------------------------------------

_DATE_FORMATS = [
    "%a, %d %b %Y %H:%M:%S %z",
    "%a, %d %b %Y %H:%M:%S GMT",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d",
]

def _parse_date(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # Normalize GMT → +0000 for first format
    candidates = [value, value.replace("GMT", "+0000").replace("UTC", "+0000")]
    for cand in candidates:
        for fmt in _DATE_FORMATS:
            try:
                parsed = dt.datetime.strptime(cand, fmt)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=dt.timezone.utc)
                return parsed.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                continue
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")

def _clean(text: str | None) -> str:
    if not text:
        return ""
    text = _TAG_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text)
    return text.strip()


def parse_items(xml_text: str, source: dict[str, str] | None = None) -> list[Item]:
    """Parse RSS 2.0 or Atom 1.0 into a list of Item. Returns [] on parse failure."""
    source = source or {"id": "unknown", "name": "Unknown"}
    if not xml_text:
        return []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        logging.warning("parse_items: %s: %s", source.get("id"), exc)
        return []

    items: list[Item] = []
    tag = root.tag.lower()
    # RSS: <rss><channel><item>...
    rss_items = root.findall(".//item")
    if rss_items:
        for el in rss_items:
            title = _clean((el.findtext("title") or "").strip())
            link = (el.findtext("link") or "").strip()
            summary = _clean(el.findtext("description") or "")
            pub = el.findtext("pubDate") or el.findtext("{http://purl.org/dc/elements/1.1/}date") or ""
            items.append(Item(
                title=title, link=link, summary=summary,
                pub_date=_parse_date(pub),
                source_id=source["id"], source_name=source["name"],
            ))
        return items
    # Atom: <feed><entry>...
    atom_entries = root.findall("{http://www.w3.org/2005/Atom}entry")
    if not atom_entries:
        atom_entries = root.findall(".//entry")

    def _first(parent: ET.Element, *tags: str) -> ET.Element | None:
        for t in tags:
            found = parent.find(t)
            if found is not None:
                return found
        return None

    for el in atom_entries:
        title_el = _first(el, "{http://www.w3.org/2005/Atom}title", "title")
        title = _clean(title_el.text if title_el is not None else "")
        link = ""
        link_el = _first(el, "{http://www.w3.org/2005/Atom}link", "link")
        if link_el is not None:
            link = (link_el.get("href") or link_el.text or "").strip()
        summary_el = _first(
            el,
            "{http://www.w3.org/2005/Atom}summary",
            "{http://www.w3.org/2005/Atom}content",
            "summary",
            "content",
        )
        summary = _clean(summary_el.text if summary_el is not None else "")
        pub_el = _first(
            el,
            "{http://www.w3.org/2005/Atom}updated",
            "{http://www.w3.org/2005/Atom}published",
            "updated",
            "published",
        )
        pub = pub_el.text if pub_el is not None else ""
        items.append(Item(
            title=title, link=link, summary=summary,
            pub_date=_parse_date(pub),
            source_id=source["id"], source_name=source["name"],
        ))
    if not items:
        logging.info("parse_items: no items in feed %s (root=%s)", source.get("id"), tag)
    return items

# ---------------------------------------------------------------------------
# Filter / dedupe
# ---------------------------------------------------------------------------

def _kw_pattern(kw: str) -> re.Pattern[str]:
    # Whole-word, case-insensitive; phrases keep internal spaces literal.
    escaped = re.escape(kw)
    return re.compile(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])", re.IGNORECASE)


_COMPILED_KEYWORDS = [(kw, _kw_pattern(kw)) for kw in KEYWORDS]


def filter_by_keywords(items: Iterable[Item], keywords: list[str] | None = None) -> list[Item]:
    """Return items whose title+summary match ≥1 keyword. Matched keywords attached."""
    compiled = [(kw, _kw_pattern(kw)) for kw in keywords] if keywords else _COMPILED_KEYWORDS
    out: list[Item] = []
    for it in items:
        hay = f"{it.title} {it.summary}"
        hits = tuple(kw for kw, pat in compiled if pat.search(hay))
        if hits:
            out.append(Item(
                title=it.title, link=it.link, pub_date=it.pub_date,
                source_id=it.source_id, source_name=it.source_name,
                summary=it.summary, matched=hits,
            ))
    return out


def dedupe(items: Iterable[Item]) -> list[Item]:
    """Dedupe by canonical link (or title-hash if no link). Preserves order."""
    seen: set[str] = set()
    out: list[Item] = []
    for it in items:
        key = (it.link or "").strip().lower() or hashlib.sha1(it.title.encode("utf-8")).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out

# ---------------------------------------------------------------------------
# Emit
# ---------------------------------------------------------------------------

def _xml_escape(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;"))


def emit_atom(items: list[Item], output_path: Path, *, feed_url: str = "https://example.invalid/feed.xml") -> None:
    """Write Atom 1.0 feed of the first MAX_FEED_ITEMS items."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    parts: list[str] = []
    parts.append('<?xml version="1.0" encoding="utf-8"?>')
    parts.append('<feed xmlns="http://www.w3.org/2005/Atom">')
    parts.append("  <title>EU Regulatory Changelog</title>")
    parts.append('  <subtitle>Filtered digital-regulation updates from EUR-Lex, EDPB, EDPS, ENISA, and the Commission.</subtitle>')
    parts.append(f'  <link href="{_xml_escape(feed_url)}" rel="self"/>')
    parts.append(f'  <id>{_xml_escape(feed_url)}</id>')
    parts.append(f"  <updated>{now}</updated>")
    parts.append('  <generator uri="https://github.com/example/regulatory-changelog-rss">regulatory-changelog-rss</generator>')
    for it in items[:MAX_FEED_ITEMS]:
        parts.append("  <entry>")
        parts.append(f"    <title>{_xml_escape(it.title)}</title>")
        if it.link:
            parts.append(f'    <link href="{_xml_escape(it.link)}"/>')
        parts.append(f"    <id>urn:rcr:{it.uid}</id>")
        parts.append(f"    <updated>{_xml_escape(it.pub_date)}</updated>")
        parts.append(f"    <author><name>{_xml_escape(it.source_name)}</name></author>")
        if it.matched:
            for kw in it.matched:
                parts.append(f'    <category term="{_xml_escape(kw)}"/>')
        if it.summary:
            parts.append(f"    <summary>{_xml_escape(it.summary)}</summary>")
        parts.append("  </entry>")
    parts.append("</feed>")
    output_path.write_text("\n".join(parts), encoding="utf-8")


_HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>EU Regulatory Changelog</title>
<link rel="alternate" type="application/atom+xml" href="feed.xml" title="EU Regulatory Changelog Atom feed"/>
<link rel="stylesheet" href="styles.css"/>
</head>
<body>
<header>
  <h1>EU Regulatory Changelog</h1>
  <p>Filtered digital-regulation updates. <a href="feed.xml">Atom feed</a>. Last update: {updated}.</p>
</header>
<section class="filters">
  <label>Keyword: <select id="kw"><option value="">all</option>{kw_opts}</select></label>
  <label>Source:  <select id="src"><option value="">all</option>{src_opts}</select></label>
  <span id="count"></span>
</section>
<main id="items">
{items_html}
</main>
<footer>
  <p>Code: MIT &middot; Content: CC-BY 4.0 &middot; <a href="https://github.com/example/regulatory-changelog-rss">source</a></p>
</footer>
<script src="filter.js"></script>
</body>
</html>
"""


def emit_html(items: list[Item], output_path: Path, template_path: Path | None = None) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    kws = sorted({m for it in items for m in it.matched})
    srcs = sorted({(it.source_id, it.source_name) for it in items})
    kw_opts = "".join(f'<option value="{_xml_escape(k)}">{_xml_escape(k)}</option>' for k in kws)
    src_opts = "".join(f'<option value="{_xml_escape(sid)}">{_xml_escape(sname)}</option>' for sid, sname in srcs)
    rows: list[str] = []
    for it in items[:MAX_HTML_ITEMS]:
        kw_attr = " ".join(it.matched)
        rows.append(
            f'<article class="item" data-source="{_xml_escape(it.source_id)}" data-keywords="{_xml_escape(kw_attr)}">'
            f'<h2><a href="{_xml_escape(it.link or "#")}">{_xml_escape(it.title) or "(untitled)"}</a></h2>'
            f'<p class="meta"><span class="source">{_xml_escape(it.source_name)}</span>'
            f' &middot; <time>{_xml_escape(it.pub_date)}</time>'
            f' &middot; <span class="tags">{" ".join(f"<code>{_xml_escape(k)}</code>" for k in it.matched)}</span></p>'
            f'<p class="summary">{_xml_escape(it.summary[:400])}{"…" if len(it.summary) > 400 else ""}</p>'
            f"</article>"
        )
    html = _HTML_TEMPLATE.format(
        updated=_xml_escape(now),
        kw_opts=kw_opts,
        src_opts=src_opts,
        items_html="\n".join(rows) or "<p>No items yet — feeds may be offline.</p>",
    )
    if template_path and template_path.exists():
        # Replace marker if present, else fall through to default template.
        custom = template_path.read_text(encoding="utf-8")
        if "{items_html}" in custom:
            html = custom.format(updated=_xml_escape(now), kw_opts=kw_opts, src_opts=src_opts, items_html="\n".join(rows))
    output_path.write_text(html, encoding="utf-8")


def emit_weekly_digest(items: list[Item], week: tuple[int, int], output_path: Path) -> None:
    """Write a markdown digest for ISO year-week tuple (year, week)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    year, wk = week
    lines: list[str] = [
        f"# EU Regulatory Changelog — {year}-W{wk:02d}",
        "",
        f"Generated {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. {len(items)} item(s) matched.",
        "",
    ]
    # Group by keyword
    by_kw: dict[str, list[Item]] = {}
    for it in items:
        for kw in it.matched or ("(uncategorised)",):
            by_kw.setdefault(kw, []).append(it)
    for kw in sorted(by_kw):
        lines.append(f"## {kw}")
        lines.append("")
        for it in by_kw[kw]:
            link = it.link or ""
            lines.append(f"- [{it.title or '(untitled)'}]({link}) — *{it.source_name}*, {it.pub_date}")
        lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")

# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def _iso_week(now: dt.datetime | None = None) -> tuple[int, int]:
    now = now or dt.datetime.now(dt.timezone.utc)
    iso = now.isocalendar()
    return (iso[0], iso[1])


def run(output_dir: Path, *, sources: list[dict[str, str]] | None = None, timeout: float = DEFAULT_TIMEOUT) -> int:
    sources = sources or SOURCES
    all_items: list[Item] = []
    for src in sources:
        body = fetch_feed(src["url"], timeout=timeout)
        if body is None:
            continue
        all_items.extend(parse_items(body, source=src))
    logging.info("run: %d raw items across %d sources", len(all_items), len(sources))
    filtered = filter_by_keywords(all_items)
    deduped = dedupe(filtered)
    deduped.sort(key=lambda it: it.pub_date, reverse=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    emit_atom(deduped, output_dir / "feed.xml")
    emit_html(deduped, output_dir / "index.html", template_path=output_dir / "index.template.html")
    year, wk = _iso_week()
    emit_weekly_digest(deduped, (year, wk), output_dir / f"digest-{year}-W{wk:02d}.md")
    logging.info("run: emitted %d filtered items", len(deduped))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="aggregator.py",
        description="Aggregate EU regulatory RSS/Atom feeds; emit Atom, HTML, and weekly markdown digest.",
    )
    parser.add_argument("--output", "-o", type=Path, default=Path("web/"), help="Output directory.")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="HTTP timeout in seconds.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging.")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    return run(args.output, timeout=args.timeout)


if __name__ == "__main__":
    sys.exit(main())
