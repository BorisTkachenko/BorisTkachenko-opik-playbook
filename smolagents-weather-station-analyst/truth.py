"""Ground truth for the questions, computed directly with pandas.

The agent derives its answers by writing its own code; these functions are the
reference the run prints next to each answer so you can see whether the code
the model wrote measured the right thing.
"""

from pathlib import Path

import pandas as pd

CSV_PATH = Path(__file__).parent / "data" / "readings.csv"


def load(path: Path = CSV_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df["date"] = df["timestamp"].dt.date
    return df


def windiest_day(df: pd.DataFrame) -> tuple[str, str, float]:
    """(station, date, mean wind km/h) of the highest daily mean wind speed."""
    daily = df.groupby(["station", "date"])["wind_kmh"].mean()
    (station, date), value = daily.idxmax(), daily.max()
    return station, str(date), round(float(value), 1)


def rainfall_by_station(df: pd.DataFrame) -> dict[str, float]:
    """Total rainfall (mm) per station; blank readings count as zero."""
    return {k: round(float(v), 1) for k, v in df.groupby("station")["rain_mm"].sum().items()}


def longest_dry_spell(df: pd.DataFrame) -> tuple[str, int, str, str]:
    """(station, days, first date, last date) of the longest run of calendar
    days with 0.0 mm total rain. Days with no rain readings at all are not dry."""
    best = ("", 0, "", "")
    for station, g in df.groupby("station"):
        daily = g.groupby("date")["rain_mm"].agg(["sum", "count"])
        run, start = 0, None
        for date, row in daily.iterrows():
            if row["count"] > 0 and row["sum"] == 0:
                run, start = run + 1, (start or date)
                if run > best[1]:
                    best = (station, run, str(start), str(date))
            else:
                run, start = 0, None
    return best


def missing_hours(df: pd.DataFrame) -> dict[str, int]:
    """Hours per station where the sensors reported nothing (blank rows)."""
    blank = df["temp_c"].isna()
    return {k: int(v) for k, v in blank.groupby(df["station"]).sum().items() if v}


def reference_answers(df: pd.DataFrame) -> list[tuple[str, list[str]]]:
    """One (reference sentence, facts the answer must contain) pair per question,
    in the same order as agent.QUESTIONS."""
    station, date, wind = windiest_day(df)
    rain = rainfall_by_station(df)
    d_station, days, first, last = longest_dry_spell(df)
    return [
        (f"{station} on {date}, mean wind {wind} km/h", [station, date, str(wind)]),
        ("; ".join(f"{k} {v}" for k, v in rain.items()), [f"{v}" for v in rain.values()]),
        (f"{d_station}, {days} days, {first} to {last}", [d_station, str(days)]),
    ]


def grade(answer: str, facts: list[str]) -> bool:
    """True when every expected fact appears in the answer text."""
    return all(f in answer for f in facts)
