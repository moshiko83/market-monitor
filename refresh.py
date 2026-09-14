#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TwinsBridge Market Monitor — daily data refresh.

Runs on GitHub Actions every morning. Pulls the "Live" metrics from Yahoo
Finance's public chart API (server-side, so no browser CORS limits and no API
key), then rewrites data.json. Metrics with no free live feed (fertilizer FOB
and retail, LME metals, sulfuric acid, manganese, freight, bunker, Panama) are
left untouched — their values are carried over from the existing data.json and
topped up by hand or on request.

Nothing here can fail the whole file: each symbol is fetched in its own try, and
if a fetch fails the previous value is kept.
"""
import json, os, sys, time, urllib.request, urllib.error, urllib.parse
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data.json")
UA = {"User-Agent": "Mozilla/5.0 (compatible; TwinsBridgeMonitor/1.0)"}

# id -> (Yahoo symbol, divisor, decimals)
#   divisor 100 converts US grain cents/bushel to dollars/bushel.
LIVE = {
    "natgas":        ("NG=F",     1,   2),
    "copper_comex":  ("HG=F",     1,   2),
    "milk":          ("DC=F",     1,   2),
    "corn":          ("ZC=F",     100, 2),
    "soy":           ("ZS=F",     100, 2),
    "wheat":         ("ZW=F",     100, 2),
    "live_cattle":   ("LE=F",     1,   2),
    "feeder_cattle": ("GF=F",     1,   2),
    "eurusd":        ("EURUSD=X", 1,   4),
    "usdmxn":        ("MXN=X",    1,   2),
    "usdcny":        ("CNY=X",    1,   4),
}
# Optional: kept live only if Yahoo happens to carry it; never downgrades on miss.
OPTIONAL = {
    "baltic": ("^BDI", 1, 0),
}

YQ = ("https://query1.finance.yahoo.com/v8/finance/chart/{s}"
      "?interval=1d&range=7d&includePrePost=false")


def fetch_symbol(sym):
    """Return (latest_price, prev_close, epoch_seconds) or raise."""
    url = YQ.format(s=urllib.parse.quote(sym))
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        j = json.loads(r.read().decode("utf-8", "replace"))
    res = j["chart"]["result"][0]
    meta = res.get("meta", {})
    closes = []
    try:
        closes = [c for c in res["indicators"]["quote"][0]["close"] if c is not None]
    except Exception:
        closes = []
    latest = meta.get("regularMarketPrice")
    if latest is None and closes:
        latest = closes[-1]
    if latest is None:
        raise ValueError("no price")
    prev = None
    if closes:
        # the most recent close that differs from `latest` is the prior session
        if len(closes) >= 2:
            prev = closes[-2] if abs(closes[-1] - latest) < 1e-9 else closes[-1]
    if prev is None:
        prev = meta.get("chartPreviousClose") or meta.get("previousClose")
    ep = meta.get("regularMarketTime")
    return float(latest), (float(prev) if prev is not None else None), ep


def fmt_num(v, dec):
    return f"{v:,.{dec}f}"


def as_of(ep):
    if not ep:
        return datetime.now(timezone.utc).strftime("%b %-d")
    return datetime.fromtimestamp(ep, tz=timezone.utc).strftime("%b %-d")


def move(latest, prev):
    if prev is None or prev == 0:
        return "—", "flat"
    pct = (latest - prev) / prev * 100.0
    if abs(pct) < 0.05:
        return "flat d/d", "flat"
    sign = "+" if pct > 0 else "−"           # U+2212 minus
    d = "up" if pct > 0 else "down"
    return f"{sign}{abs(pct):.1f}% d/d", d


def update_one(metrics, mid, sym, divisor, dec, live_flag=True):
    try:
        latest, prev, ep = fetch_symbol(sym)
    except Exception as e:
        print(f"  ! {mid:14} {sym:10} FAILED ({e}) — keeping previous", file=sys.stderr)
        return False
    latest /= divisor
    prev = (prev / divisor) if prev is not None else None
    chg, direction = move(latest, prev)
    entry = metrics.setdefault(mid, {})
    entry["num"] = fmt_num(latest, dec)
    entry["chg"] = chg
    entry["dir"] = direction
    entry["asOf"] = as_of(ep)
    if live_flag:
        entry["q"] = "live"
    print(f"  ✓ {mid:14} {sym:10} -> {entry['num']:>12}  {chg}")
    return True


def main():
    data = {"generated": None, "metrics": {}}
    if os.path.exists(DATA):
        try:
            with open(DATA, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Could not read existing data.json ({e}); starting fresh.",
                  file=sys.stderr)
    metrics = data.setdefault("metrics", {})

    print("Refreshing live metrics from Yahoo Finance...")
    ok = 0
    for mid, (sym, div, dec) in LIVE.items():
        if update_one(metrics, mid, sym, div, dec):
            ok += 1
        time.sleep(0.4)  # be polite

    for mid, (sym, div, dec) in OPTIONAL.items():
        update_one(metrics, mid, sym, div, dec, live_flag=False)
        time.sleep(0.4)

    data["generated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"\nDone. {ok}/{len(LIVE)} live metrics refreshed. Wrote {DATA}")
    # Never exit non-zero for partial failures — a stale tile beats a broken run.
    return 0


if __name__ == "__main__":
    sys.exit(main())
