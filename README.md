# regulatory-changelog-rss

> One feed for EU digital-regulation noise. EUR-Lex + EDPB + ENISA + EDPS + Commission press releases, filtered by GDPR / EHDS / CRA / AI Act / NIS2 / DORA / MDR / DSA / DGA / eIDAS / Data Act / ePrivacy.

[![Update](https://img.shields.io/badge/updated-nightly-blue)]()
[![License](https://img.shields.io/badge/license-MIT%20%2B%20CC--BY--4.0-green)]()

## Why this exists

A small DPO / GRC / privacy-eng team in the EU subscribes to 8+ official RSS feeds to stay current: EUR-Lex, EDPB, EDPS, ENISA, DG SANTE, DG CONNECT, the Commission's digital-strategy press room, and so on. Each emits dozens of items per week, almost none of which are relevant to any particular regulation.

This project consolidates those 8 feeds into a single, keyword-filtered Atom feed. You subscribe **once**, and you receive only items whose title or summary mentions one of the regulations you care about.

## What it does

- **Nightly aggregation** via GitHub Actions cron (04:00 UTC).
- **Keyword filter**: case-insensitive whole-word match on `GDPR`, `EHDS`, `CRA`, `AI Act`, `NIS2`, `DORA`, `MDR`, `DSA`, `DGA`, `eIDAS`, `Data Act`, `ePrivacy`.
- **Emits three outputs**:
  - `web/feed.xml` — Atom 1.0 feed of the latest 100 filtered items.
  - `web/index.html` — static site showing the latest 30 with client-side filtering UI (no JS framework).
  - `web/digest-YYYY-WW.md` — weekly markdown digest, ready to paste into a newsletter.
- **Zero infra**: GitHub Pages serves the feed and the site. Workflow commits back to `main`.
- **Graceful degradation**: a source returning 404 / 500 / timeout is logged and skipped; the run still produces output.

## Sources

| Source                        | URL                                                                       | License / Terms                          |
|-------------------------------|---------------------------------------------------------------------------|------------------------------------------|
| EUR-Lex recent legal content  | https://eur-lex.europa.eu/EN/display-feed.rss?myRssId=recent              | Reuse free under © European Union notice |
| Commission press releases     | https://ec.europa.eu/commission/presscorner/api/rss?language=en           | CC-BY 4.0                                |
| Commission digital-strategy   | https://digital-strategy.ec.europa.eu/en/news-redirect/rss.xml            | CC-BY 4.0                                |
| EDPB latest outputs           | https://www.edpb.europa.eu/feeds/news_en.rss                              | © EDPB, reuse with attribution           |
| EDPS news                     | https://www.edps.europa.eu/rss.xml                                        | © EDPS, reuse with attribution           |
| ENISA news                    | https://www.enisa.europa.eu/news/RSS                                      | CC-BY 4.0                                |
| DG SANTE health-data updates  | https://health.ec.europa.eu/rss_en                                        | CC-BY 4.0                                |
| DG CONNECT digital-policy     | https://digital-strategy.ec.europa.eu/en/policies/rss.xml                 | CC-BY 4.0                                |

URLs are best-effort at time of writing; the script tolerates broken sources and the source table in `scripts/aggregator.py` is the single source of truth.

## Quickstart

```bash
git clone https://github.com/<you>/regulatory-changelog-rss
cd regulatory-changelog-rss
python scripts/aggregator.py --output web/
open web/index.html
```

No dependencies. Stdlib only. Python 3.10+.

## Subscribe

- **Atom**: `https://<you>.github.io/regulatory-changelog-rss/feed.xml`
- **Web**:  `https://<you>.github.io/regulatory-changelog-rss/`
- **Weekly digest**: see `web/digest-YYYY-WW.md` in the repo, or pipe via a newsletter sender of your choice.

## Pricing

- **OSS, free.** Apache 2 / MIT for code, CC-BY 4.0 for the digest content.
- **Optional paid tier (planned)**: €5/mo for an email newsletter of the weekly digest, with a single-click unsubscribe. Stripe Checkout, no account. Email infra TBD (Buttondown or similar). Email-only, no tracking pixels.
- The OSS feed is always free and always public.

## Local development

```bash
# Run the aggregator
python scripts/aggregator.py --output web/ --verbose

# Run tests (5+ unittests, fixture-based, no network)
python -m unittest tests.test_aggregator -v

# Help
python scripts/aggregator.py --help
```

## How filtering works

A keyword `KW` matches an item if the regex `\b<KW>\b` matches `(title + " " + summary)` case-insensitively. Multi-word keywords like `AI Act` are treated as a literal phrase with `\b` boundaries on each end.

Items must match **at least one** keyword to pass. To change the keyword set, edit `KEYWORDS` in `scripts/aggregator.py`.

## How the workflow runs

`.github/workflows/aggregate.yml` runs daily at 04:00 UTC. It:

1. Checks out the repo.
2. Sets up Python 3.11.
3. Runs `python scripts/aggregator.py --output web/`.
4. If `git diff --quiet web/feed.xml` is non-zero (feed changed), commits `chore: nightly update` and pushes.

If a source feed is down, the script logs `WARN <source>` and continues. No source is critical.

## Roadmap

- d+7: validate Atom feed with a third-party validator (W3C feed validator).
- d+14: add ELI/CELEX extraction from EUR-Lex items, link to consolidated text.
- d+30: kill-gate (see `kill-gate.md`).

## Status

Wave 2 venture, scaffolded 2026-05-14. See `CHANGELOG.md` for substantive changes.

## License

Code: MIT. Content / digests: CC-BY 4.0. See `LICENSE`.

## Contributing

PRs welcome for: new sources (with a stable RSS URL + reuse-terms note), better keyword regex (false-positive reports), Atom validation hardening.

Out of scope: paid plans, user accounts, anything that isn't a static file.
