"""Unit tests for scripts/aggregator.py — fixture-based, no network."""
from __future__ import annotations

import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

# Allow `python -m unittest tests.test_aggregator` from repo root.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import aggregator  # noqa: E402

FIXTURE_RSS = ROOT / "tests" / "fixtures" / "sample-feed.xml"
FIXTURE_ATOM = ROOT / "tests" / "fixtures" / "sample-atom.xml"


class ParseTests(unittest.TestCase):
    def test_parse_rss_items_count(self) -> None:
        xml = FIXTURE_RSS.read_text(encoding="utf-8")
        items = aggregator.parse_items(xml, source={"id": "fix", "name": "Fixture"})
        self.assertEqual(len(items), 6)
        self.assertEqual(items[0].source_id, "fix")
        self.assertTrue(items[0].title.startswith("EDPB"))

    def test_parse_atom_items_count(self) -> None:
        xml = FIXTURE_ATOM.read_text(encoding="utf-8")
        items = aggregator.parse_items(xml, source={"id": "atom", "name": "Atom Fix"})
        self.assertEqual(len(items), 2)
        self.assertIn("DORA", items[0].title)

    def test_parse_invalid_xml_returns_empty(self) -> None:
        self.assertEqual(aggregator.parse_items("<<<not xml>>>"), [])
        self.assertEqual(aggregator.parse_items(""), [])


class FilterTests(unittest.TestCase):
    def test_filter_keeps_regulatory_items(self) -> None:
        xml = FIXTURE_RSS.read_text(encoding="utf-8")
        items = aggregator.parse_items(xml, source={"id": "fix", "name": "Fixture"})
        filtered = aggregator.filter_by_keywords(items)
        # 5 of 6 fixture items mention a regulation; agri-subsidies item should drop.
        titles = [it.title for it in filtered]
        self.assertTrue(all("agriculture" not in t.lower() for t in titles))
        self.assertGreaterEqual(len(filtered), 4)
        # Each kept item must have ≥1 matched keyword.
        for it in filtered:
            self.assertGreater(len(it.matched), 0)

    def test_filter_matches_phrase_ai_act(self) -> None:
        xml = FIXTURE_RSS.read_text(encoding="utf-8")
        items = aggregator.parse_items(xml, source={"id": "fix", "name": "Fixture"})
        filtered = aggregator.filter_by_keywords(items)
        ai_act_items = [it for it in filtered if "AI Act" in it.matched]
        self.assertEqual(len(ai_act_items), 1)

    def test_filter_whole_word_boundary(self) -> None:
        from aggregator import Item, filter_by_keywords
        items = [
            Item(title="MDRAGON not a regulation", link="x", pub_date="2026-01-01T00:00:00Z",
                 source_id="t", source_name="t", summary=""),
            Item(title="MDR rules updated", link="y", pub_date="2026-01-01T00:00:00Z",
                 source_id="t", source_name="t", summary=""),
        ]
        kept = filter_by_keywords(items)
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0].link, "y")


class DedupeTests(unittest.TestCase):
    def test_dedupe_by_link(self) -> None:
        xml = FIXTURE_RSS.read_text(encoding="utf-8")
        items = aggregator.parse_items(xml, source={"id": "fix", "name": "Fixture"})
        deduped = aggregator.dedupe(items)
        # Fixture has one duplicate link → expect 5 unique items.
        self.assertEqual(len(deduped), 5)


class EmitTests(unittest.TestCase):
    def test_emit_atom_is_well_formed(self) -> None:
        xml = FIXTURE_RSS.read_text(encoding="utf-8")
        items = aggregator.filter_by_keywords(
            aggregator.dedupe(aggregator.parse_items(xml, source={"id": "fix", "name": "Fixture"}))
        )
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "feed.xml"
            aggregator.emit_atom(items, out)
            parsed = ET.fromstring(out.read_text(encoding="utf-8"))
            self.assertTrue(parsed.tag.endswith("feed"))
            entries = parsed.findall("{http://www.w3.org/2005/Atom}entry")
            self.assertEqual(len(entries), len(items))

    def test_emit_html_contains_items(self) -> None:
        xml = FIXTURE_RSS.read_text(encoding="utf-8")
        items = aggregator.filter_by_keywords(
            aggregator.dedupe(aggregator.parse_items(xml, source={"id": "fix", "name": "Fixture"}))
        )
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "index.html"
            aggregator.emit_html(items, out)
            html = out.read_text(encoding="utf-8")
            self.assertIn("EU Regulatory Changelog", html)
            self.assertIn("data-keywords", html)
            self.assertIn("GDPR", html)

    def test_emit_weekly_digest(self) -> None:
        xml = FIXTURE_RSS.read_text(encoding="utf-8")
        items = aggregator.filter_by_keywords(
            aggregator.dedupe(aggregator.parse_items(xml, source={"id": "fix", "name": "Fixture"}))
        )
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "digest.md"
            aggregator.emit_weekly_digest(items, (2026, 19), out)
            md = out.read_text(encoding="utf-8")
            self.assertIn("EU Regulatory Changelog", md)
            self.assertIn("2026-W19", md)


class FetchTests(unittest.TestCase):
    def test_fetch_feed_unreachable_returns_none(self) -> None:
        # RFC 5737 TEST-NET-1 + nonsense port → never reachable, never raises.
        result = aggregator.fetch_feed("http://192.0.2.1:1/feed", timeout=1.0)
        self.assertIsNone(result)

    def test_fetch_feed_bad_url_returns_none(self) -> None:
        result = aggregator.fetch_feed("not-a-url-at-all", timeout=1.0)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
