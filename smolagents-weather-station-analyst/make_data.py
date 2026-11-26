"""Regenerate data/readings.csv (deterministic, fictional).

Five stations, hourly readings for 21 days (2026-03-02 .. 2026-03-22).
Planted so the questions have real answers:
  * Summit Pass has a storm on 2026-03-11 (the windiest day of the file).
  * Salt Marsh gets no rain for 9 days in a row (2026-03-08 .. 2026-03-16).
  * A few stretches of missing sensor values (blank cells).
"""

import csv
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

OUT = Path(__file__).parent / "data" / "readings.csv"
START = datetime(2026, 3, 2)
DAYS = 21

# name -> (mean temp C, mean wind km/h, rain chance per hour, base pressure hPa)
STATIONS = {
    "Harbor Point": (9.0, 18.0, 0.10, 1012.0),
    "Ridgeline": (4.0, 26.0, 0.08, 985.0),
    "Cedar Flats": (11.0, 8.0, 0.12, 1008.0),
    "Salt Marsh": (10.0, 14.0, 0.11, 1013.0),
    "Summit Pass": (-2.0, 34.0, 0.07, 940.0),
}
# (station, first hour index, length) blocks where every sensor is blank
GAPS = [("Cedar Flats", 100, 14), ("Ridgeline", 300, 9), ("Harbor Point", 410, 20)]


def build_rows() -> list[dict]:
    rng = random.Random(2026)
    rows = []
    for name, (t0, w0, rain_p, p0) in STATIONS.items():
        for h in range(DAYS * 24):
            ts = START + timedelta(hours=h)
            day = h // 24
            temp = t0 + 5 * math.sin((ts.hour - 9) / 24 * 2 * math.pi) + rng.gauss(0, 0.8)
            hum = min(100.0, max(25.0, 70 - 2.2 * (temp - t0) + rng.gauss(0, 5)))
            wind = max(0.0, w0 + rng.gauss(0, 6))
            rain = round(rng.expovariate(1 / 1.4), 1) if rng.random() < rain_p else 0.0
            pres = p0 + 4 * math.sin(day / 3) + rng.gauss(0, 0.6)
            if name == "Salt Marsh" and 6 <= day <= 14:
                rain = 0.0  # the planted 9-day dry spell
            if name == "Summit Pass" and day == 9 and 8 <= ts.hour <= 20:
                wind = 95 + rng.gauss(0, 12)  # the planted storm
                pres -= 18
            row = {
                "station": name,
                "timestamp": ts.strftime("%Y-%m-%d %H:%M"),
                "temp_c": round(temp, 1),
                "humidity_pct": round(hum),
                "wind_kmh": round(wind, 1),
                "rain_mm": rain,
                "pressure_hpa": round(pres, 1),
            }
            for gs, first, length in GAPS:
                if gs == name and first <= h < first + length:
                    for col in ("temp_c", "humidity_pct", "wind_kmh", "rain_mm", "pressure_hpa"):
                        row[col] = ""
            rows.append(row)
    return rows


if __name__ == "__main__":
    rows = build_rows()
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {OUT}")
