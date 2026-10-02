from pathlib import Path
from functools import lru_cache
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "ml" / "artifacts" / "model.json"


@lru_cache(maxsize=1)
def symptom_names():
    return [c for c in pd.read_csv(ROOT / "data" / "Training.csv", nrows=0).columns if c != "prognosis"]


@lru_cache(maxsize=1)
def load_model():
    return json.loads(ARTIFACT.read_text()) if ARTIFACT.exists() else None


def predict(symptoms):
    names = symptom_names()
    if not symptoms or not set(symptoms) <= set(names):
        raise ValueError("Unknown or empty symptoms")
    model = load_model()
    if model is None:
        return {"disease": "Model not trained - clinician review required"}
    vector = np.array([float(name in symptoms) for name in model["features"]])
    score = np.array(model["intercept"]) + np.array(model["coef"]) @ vector
    return {"disease": model["classes"][int(score.argmax())]}
