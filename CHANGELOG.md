# Changelog

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

## [Unreleased]

### Added
- Initial scaffold (Wave 2 venture #15).
- `scripts/aggregator.py`: stdlib-only RSS/Atom aggregator with keyword filter, dedupe, Atom 1.0 emitter, static HTML emitter, weekly markdown digest emitter.
- 8 source feeds: EUR-Lex, EC press, EC digital-strategy, EDPB, EDPS, ENISA, DG SANTE, DG CONNECT.
- 12 keyword filters: GDPR, EHDS, CRA, AI Act, NIS2, DORA, MDR, DSA, DGA, eIDAS, Data Act, ePrivacy.
- `web/index.html` + `web/styles.css` + `web/filter.js`: static site with client-side filtering and dark-mode aware styles.
- `web/feed.xml`: placeholder Atom feed for first deployment.
- `.github/workflows/aggregate.yml`: daily 04:00 UTC GH Actions cron with auto-commit.
- `tests/test_aggregator.py`: 11 unittest tests + RSS and Atom fixtures.
- `LICENSE`: dual MIT (code) + CC-BY 4.0 (content).
- `kill-gate.md`: d+30 decision criteria (subscribers ≥30, visitors ≥500, emails ≥5, or citation ≥1).
- `landing-copy.md`: hero / sub-hero / channels / FAQ for ProductHunt + dev.to + Reddit launches.

### Notes
- Stdlib only on the Python side (urllib + xml.etree.ElementTree + html stdlib helpers). No requests, no feedparser, no jinja.
- Vanilla JS on the web side. No frameworks.
- The aggregator handles 404 / 500 / timeout / unreachable hosts gracefully — never raises on a bad source.
