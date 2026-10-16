"""Download the public Hotel Booking Demand dataset (Antonio, Almeida & Nunes 2019, CC BY 4.0)
via the TidyTuesday 2020-02-11 mirror. 16.9 MB, 119,390 rows. URL verified 2026-10-16."""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

URL = "https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2020/2020-02-11/hotels.csv"
OUT = Path(__file__).resolve().parent / "hotels.csv"

if __name__ == "__main__":
    if OUT.exists():
        sys.exit(f"already there: {OUT}")
    urllib.request.urlretrieve(URL, OUT)
    print(f"saved {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")
