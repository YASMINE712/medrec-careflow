"""Synthetic data for workflow demonstrations; no medical relationships."""

import csv
from itertools import combinations
from pathlib import Path


def create_fixture(path=None):
    path = path or Path(__file__).resolve().parents[1] / "data" / "Training.csv"
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    features = [
        "itching",
        "skin_rash",
        "headache",
        "fatigue",
        "cough",
        "chills",
        "nausea",
        "joint_pain",
        "back_pain",
        "dizziness",
        "sweating",
        "runny_nose",
    ]
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(features + ["prognosis"])
        for size in (1, 2, 3):
            for active in combinations(range(len(features)), size):
                row = [int(i in active) for i in range(len(features))]
                label = "Synthetic pattern " + ("A" if row[0] else "B" if row[1] else "C")
                writer.writerow(row + [label])
    return True


if __name__ == "__main__":
    print(
        "Created synthetic workflow fixture. Not clinical data."
        if create_fixture()
        else "Existing dataset preserved."
    )
