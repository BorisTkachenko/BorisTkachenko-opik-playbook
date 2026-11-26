"""Load the labelled trail reports shipped in data/."""

import json
import pathlib

from .config import DATA_DIR, LABELS


def load_split(name: str, data_dir: pathlib.Path = DATA_DIR) -> list[dict]:
    """Return the rows of data/<name>.jsonl as {"report": str, "label": str}."""
    rows = []
    with open(data_dir / f"{name}.jsonl", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row["label"] not in LABELS:
                    raise ValueError(f"unknown label {row['label']!r} in {name}.jsonl")
                rows.append(row)
    return rows
