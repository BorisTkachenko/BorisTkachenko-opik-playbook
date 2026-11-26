from truth import (
    grade,
    load,
    longest_dry_spell,
    missing_hours,
    rainfall_by_station,
    reference_answers,
    windiest_day,
)
import make_data


def test_generated_csv_is_deterministic():
    rows = make_data.build_rows()
    assert len(rows) == 5 * 21 * 24
    assert rows == make_data.build_rows()


def test_planted_storm_is_the_windiest_day():
    station, date, value = windiest_day(load())
    assert (station, date) == ("Summit Pass", "2026-03-11")
    assert value > 60


def test_planted_dry_spell_and_sensor_gaps():
    assert longest_dry_spell(load()) == ("Salt Marsh", 9, "2026-03-08", "2026-03-16")
    assert missing_hours(load()) == {"Cedar Flats": 14, "Harbor Point": 20, "Ridgeline": 9}


def test_rainfall_totals_cover_every_station():
    totals = rainfall_by_station(load())
    assert len(totals) == 5 and totals["Salt Marsh"] < totals["Cedar Flats"]


def test_grade_requires_every_fact():
    _, facts = reference_answers(load())[2]
    assert grade("Salt Marsh had a 9 day dry spell", facts)
    assert not grade("Cedar Flats had a 20 day dry spell", facts)
