"""Reproducible ETL, deduplicated holdout evaluation and JSON model export."""

import hashlib
import json
from pathlib import Path
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]


def train():
    source = ROOT / "data" / "Training.csv"
    raw = pd.read_csv(source)
    data = raw.drop_duplicates().copy()
    x, y = data.drop(columns="prognosis"), data.prognosis.str.strip()
    if x.isna().any().any() or not x.isin([0, 1]).all().all() or y.isna().any() or y.eq("").any():
        raise ValueError("Dataset must contain binary features and non-null labels.")
    if data.groupby(list(x.columns)).prognosis.nunique().max() > 1:
        raise ValueError("Identical symptom vectors have conflicting labels.")
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=42, stratify=y)
    model = LogisticRegression(max_iter=2000, random_state=42).fit(x_train, y_train)
    dummy = DummyClassifier(strategy="most_frequent").fit(x_train, y_train)
    predicted = model.predict(x_test)
    report = {
        "dataset_kind": "synthetic workflow fixture"
        if y.str.startswith("Synthetic pattern ").all()
        else "unverified original dataset",
        "dataset_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "raw_rows": len(raw),
        "unique_rows": len(data),
        "duplicates_removed": len(raw) - len(data),
        "train_rows": len(x_train),
        "test_rows": len(x_test),
        "features": len(x.columns),
        "classes": list(model.classes_),
        "seed": 42,
        "accuracy": accuracy_score(y_test, predicted),
        "macro_f1": f1_score(y_test, predicted, average="macro"),
        "baseline_accuracy": accuracy_score(y_test, dummy.predict(x_test)),
        "confusion_matrix": confusion_matrix(y_test, predicted, labels=model.classes_).tolist(),
        "limitations": (
            "Synthetic fixture with arbitrary labels; workflow testing only, no clinical meaning."
            if y.str.startswith("Synthetic pattern ").all()
            else "Unverified dataset provenance; internal holdout only. No clinical validity, calibration or external validation. Similar symptom templates may remain across splits."
        ),
    }
    out = ROOT / "ml" / "artifacts"
    out.mkdir(exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(report, indent=2))
    (out / "model.json").write_text(
        json.dumps(
            {
                "features": list(x.columns),
                "classes": list(model.classes_),
                "coef": model.coef_.tolist(),
                "intercept": model.intercept_.tolist(),
            }
        )
    )
    print(json.dumps({k: v for k, v in report.items() if k not in ("confusion_matrix", "classes")}, indent=2))


if __name__ == "__main__":
    train()
