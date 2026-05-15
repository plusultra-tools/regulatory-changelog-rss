# Landing-page copy — regulatory-changelog-rss

## Hero

**One feed for EU digital-regulation noise.**

EUR-Lex + EDPB + ENISA + EDPS + the Commission — filtered by GDPR, EHDS, CRA, AI Act, NIS2, DORA, MDR, DSA, DGA, eIDAS, Data Act, ePrivacy. Updated nightly. Atom + static site + weekly digest.

→ **[Subscribe to Atom](./feed.xml)** &nbsp;&nbsp; → **[Source on GitHub](https://github.com/example/regulatory-changelog-rss)**

---

## Sub-hero (one paragraph)

EU privacy / GRC / compliance-eng teams currently subscribe to eight separate RSS feeds and skim 90 % noise. This project does the skim for you: one feed, twelve keywords, nightly. Static HTML + Atom + a weekly markdown digest you can pipe into your newsletter. Free, OSS, no account, no tracking.

---

## Three-up value props

**Eight sources, one feed.** EUR-Lex, EDPB, EDPS, ENISA, DG SANTE, DG CONNECT, the Commission press room, and the digital-strategy news room — consolidated.

**Twelve regulations, whole-word match.** Only items mentioning GDPR / EHDS / CRA / AI Act / NIS2 / DORA / MDR / DSA / DGA / eIDAS / Data Act / ePrivacy. Configurable in 5 lines.

**Zero infra, full ownership.** GitHub Actions cron, GitHub Pages, MIT + CC-BY 4.0. Fork it, change the keywords, point your Feedly at *your* fork.

---

## Channels (where to post — Wave 2 distribution plan)

1. **dev.to** — "I built a static-site RSS aggregator for EU regulatory feeds in 300 lines of stdlib Python." Frame: minimalist, no-deps, Python-without-frameworks angle.
2. **r/programming** — same post link, lead with "no dependencies, single file, runs on GitHub Actions free tier."
3. **r/privacy / r/gdpr** — frame: "if you're tired of 8 newsletters, here's one feed."
4. **HN Show** — only if confidence ≥0.7 the post survives the first hour. Title: `Show HN: One Atom feed for EU digital-regulation updates`.
5. **ProductHunt** — *only after* d+14 once feed has 14+ days of substance. Otherwise it looks empty.
6. **GitHub trending** — passive; depends on the above driving stars.
7. **Cross-link** from `eu-compliance-deadline-tracker` footer.
8. **LinkedIn (operator's network)** — *requires* principal explicit-go and writing samples per CLAUDE.md §3.

---

## Subscribe CTAs (3 variants for A/B testing)

- "Subscribe to the Atom feed →"
- "Get the weekly digest by email — €5/mo →" *(only enable when Stripe is wired)*
- "Star on GitHub & fork to customize keywords →"

---

## FAQ (objection-handling)

**Why not just use Feedly's smart-filtering?**
Because Feedly's filters are per-user, you still have to add 8 source URLs and write 12 keyword rules. This project does that once, shares the result, and is forkable if your keyword list differs.

**How fresh is the feed?**
Updated daily at 04:00 UTC. Most EU bodies publish during European business hours, so items typically appear in the feed the morning after publication.

**Will you add source X?**
PR welcome if X has a stable RSS/Atom URL and CC-BY-compatible reuse terms.

**Is there an email subscription?**
Planned at €5/mo for the weekly digest. The Atom feed and static site stay free forever.

**Why dual-license (MIT + CC-BY)?**
Code is MIT so you can embed it anywhere. Content (the digests) is CC-BY because attribution matters when republishing.

---

## Footer

Maintained by [plusultra-tools](https://github.com/plusultra-tools) · Code: MIT · Content: CC-BY 4.0 · [Source](https://github.com/plusultra-tools/regulatory-changelog-rss) · [Kill-gate](./kill-gate.md)
