"""Comparable nightly rates near the hotel from SerpApi's google_hotels engine (PKR), disk-cached.

Free plan: 250 searches/month, 50/hour; SerpApi's own 1 h cache is free. We add a 24 h disk cache
keyed by the exact params plus a local monthly counter so a demo loop can't burn the quota.
"""
from __future__ import annotations

import hashlib
import json
import statistics
import time
from datetime import date, timedelta

from munshi import config as cfg
from munshi.schema import Comp, CompsResult


class CompsUnavailable(Exception):
    """Transient SerpApi failure; Temporal retries it."""


def _params(check_in: date, nights: int, adults: int) -> dict:
    return {"engine": "google_hotels", "q": cfg.COMPS_QUERY,
            "check_in_date": check_in.isoformat(), "check_out_date": (check_in + timedelta(days=nights)).isoformat(),
            "adults": adults, "currency": cfg.COMPS_CURRENCY, "gl": cfg.COMPS_GL, "hl": cfg.COMPS_HL,
            "sort_by": 3}  # 3 = lowest price


def _cache_path(params: dict):
    key = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()[:16]
    return cfg.COMPS_CACHE_DIR / f"{key}.json"


def _budget_ok() -> bool:
    counter = cfg.COMPS_CACHE_DIR / f"count-{time.strftime('%Y-%m')}.txt"
    used = int(counter.read_text()) if counter.exists() else 0
    if used >= cfg.SERPAPI_MONTHLY_BUDGET:
        return False
    counter.write_text(str(used + 1))
    return True


def parse_properties(raw: dict) -> list[Comp]:
    comps = []
    for p in raw.get("properties", []):
        rate = (p.get("rate_per_night") or {}).get("extracted_lowest")
        comps.append(Comp(name=p.get("name", "?"), nightly_pkr=int(rate) if rate else None,
                          rating=p.get("overall_rating"), hotel_class=p.get("extracted_hotel_class")))
    return [c for c in comps if c.nightly_pkr][: cfg.COMPS_MAX]


def fetch(check_in: date, nights: int = 1, adults: int = 2) -> CompsResult:
    if not cfg.SERPAPI_API_KEY:
        return CompsResult(source="disabled")
    params = _params(check_in, max(nights, 1), adults)
    path = _cache_path(params)
    cfg.COMPS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    source = "cache"
    if path.exists() and time.time() - path.stat().st_mtime < cfg.COMPS_CACHE_TTL_H * 3600:
        raw = json.loads(path.read_text(encoding="utf-8"))
    elif not _budget_ok():
        return CompsResult(source="disabled")
    else:
        import serpapi

        try:
            raw = dict(serpapi.Client(api_key=cfg.SERPAPI_API_KEY, timeout=30).search(params))
        except serpapi.SerpApiError as e:
            raise CompsUnavailable(str(e)) from e
        path.write_text(json.dumps(raw), encoding="utf-8")
        source = "live"
    comps = parse_properties(raw)
    rates = [c.nightly_pkr for c in comps if c.nightly_pkr]
    return CompsResult(comps=comps, median_nightly_pkr=int(statistics.median(rates)) if rates else None,
                       source=source if comps else "empty")
