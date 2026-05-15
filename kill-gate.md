# Kill-gate — regulatory-changelog-rss

Wave 2 venture #15. Cluster D (audience asset). Expected direct monetization: low (P(€1K/mo) = 2–5 %). Justification for existing: traffic-and-trust pre-asset for `eu-compliance-deadline-tracker` (Bet B) and the compliance-manifest cluster.

## Decision date

**d+30 from public launch** (date of first ProductHunt / dev.to / /r/programming post).

## Pass conditions (any ONE → keep building)

1. **≥30 RSS subscribers.** Measure via Cloudflare Analytics (if behind CF) on `feed.xml` requests with `User-Agent` containing `Feedly|NewsBlur|Inoreader|FeedBin|RSS`. De-duplicate by IP/UA daily and take 7-day average.
2. **≥500 unique visitors to the site.** GitHub Pages → no built-in analytics; if site is behind Cloudflare, use CF Web Analytics (privacy-preserving). Otherwise instrument server-side log parsing of GH Pages access logs (not possible) — proxy with: `web/index.html` rendered count via a Cloudflare Worker that increments a KV counter, OR self-host on a tiny VPS with Plausible.
3. **≥5 inbound emails** (any: feedback, feature requests, "thanks for shipping this", "can you add X feed?"). Threshold of intent ≫ vanity metric.
4. **Cited by ≥1 other compliance newsletter or compliance-tech blog.** Inbound link tracked via Google Search Console or manual search (`"regulatory-changelog-rss" -github.com -site:reddit.com`).

## Kill condition

All four fail at d+30 → archive to `archive/regulatory-changelog-rss/post-mortem.md` and re-invest the maintenance slot elsewhere.

## Soft-keep condition (zombie tolerance)

Cron costs ~0 € / month (GitHub Actions free tier) and ~5 min/quarter maintenance. Even if all kill-gate metrics fail, the workflow keeps running passively as long as it doesn't break — pure ambient cost. **A real kill means**: actively disable the workflow, archive the repo, post a final note on the site. Only do this if the venture is generating *negative* signal (e.g. damaging brand because feeds are broken and we look incompetent).

## Anti-kill (do not let this happen)

- Sunk-cost bias: "I spent 4h on this, let me give it another month." No. d+30 is d+30.
- Vanity-metric inflation: counting GitHub stars or HN upvotes. Neither is a subscriber.
- Confounding traffic from Bet B (deadline tracker) cross-linking. If 80 % of traffic is from Bet B's footer link, that's Bet B working, not this venture working.

## What I am explicitly NOT measuring

- Stripe revenue (the €5/mo email digest is a future-pivot option, not d+30 expectation).
- Star count on the GitHub repo (vanity).
- Social-media impressions on launch posts (one-off spike, not durable).

## Decision log entry to write at d+30

```
- d+30 evaluation regulatory-changelog-rss: <pass|kill>. Subscribers=<n>, visitors=<n>, emails=<n>, citations=<n>. Decision: <keep|kill>. If kill, reason and what we learned about Cluster D in 2026.
```
