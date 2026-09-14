# TwinsBridge Market Monitor — self-updating version

A live team dashboard that **updates itself every morning** with no one having to
touch it. It's an ordinary web page (`index.html`) that reads its numbers from
`data.json`, and a small scheduled job (`refresh.py`, run by GitHub Actions)
rewrites `data.json` every morning from a public futures feed.

Once it's set up (about 10 minutes, one time), the URL is always current and you
can share it with the whole team. Nothing to check every morning.

---

## What updates automatically vs. by hand

**Auto-refreshed every morning (the "Live" tiles):**
natural gas, COMEX copper, corn, soybeans, wheat, live cattle, feeder cattle,
Class III milk, and the three FX pairs (EUR/USD, USD/MXN, USD/CNY).
These come from Yahoo Finance's public price feed — free, no API key.

**Topped up periodically (the "Lagged"/"Proxy" tiles):**
the Gulf/NOLA and US-retail fertilizer benchmarks, LME copper & zinc, sulfuric
acid, manganese, the Drewry/Baltic freight indices, bunker fuel, and the Panama
draft. These have **no free live feed** — they're specialty benchmarks that live
behind paid services (Argus, ICIS, Fastmarkets, Drewry). They carry the most
recent published print, with the as-of date shown on each tile. To refresh them,
edit their numbers in `data.json` (or just ask Claude to update them) — no code
or HTML changes needed. A paid data feed could automate these too later.

---

## One-time setup (GitHub Pages + Actions — free, no credit card)

1. **Create a free GitHub account** at https://github.com (skip if you have one).
2. Click **New repository**. Name it e.g. `market-monitor`, set it **Public**
   (Pages is free on public repos), and create it.
3. **Upload these four items** into the repo (drag them onto the "uploading an
   existing file" page, or use *Add file → Upload files*):
   - `index.html`
   - `data.json`
   - `refresh.py`
   - the `.github` folder (contains `.github/workflows/refresh.yml`)
   Commit the upload.
4. **Turn on Pages:** repo **Settings → Pages →** under *Build and deployment*
   set **Source = Deploy from a branch**, **Branch = main**, **/(root)**, Save.
   After a minute your dashboard is live at
   `https://<your-username>.github.io/market-monitor/`.
5. **Let the job write data:** repo **Settings → Actions → General →** scroll to
   *Workflow permissions*, choose **Read and write permissions**, Save.
6. **Test the auto-refresh now:** repo **Actions** tab → **Refresh market data**
   → **Run workflow**. Give it a minute; it'll pull fresh prices and commit an
   updated `data.json`. Reload your dashboard — the Live tiles are current.

That's it. From then on it refreshes on its own each morning (the schedule is in
`.github/workflows/refresh.yml`, currently ~7:30 AM US Eastern, Mon–Sat).
Share the `github.io` URL with the team — it works for anyone, no login.

---

## Changing things later

- **Refresh time:** edit the `cron:` line in `.github/workflows/refresh.yml`
  (it's in UTC).
- **Top up a specialty benchmark:** edit that metric's `num` / `chg` / `asOf`
  in `data.json` and commit — or ask Claude to do it.
- **Add or remove a metric:** the tile definitions (name, unit, source, YTD
  average, notes) live in the `METRICS` list near the bottom of `index.html`;
  the auto-refreshed symbols live in the `LIVE` map in `refresh.py`.

Public market data · Not investment advice · Verify against your own feeds
before trading decisions.
