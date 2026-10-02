import numpy as np
import pytest
from ml.ml_model import predict, load_model


def test_empty_unknown_inputs():
    with pytest.raises(ValueError):
        predict([])
    with pytest.raises(ValueError):
        predict(["not-a-symptom"])


def test_model_feature_contract():
    model = load_model()
    assert model is not None
    assert np.array(model["coef"]).shape == (len(model["classes"]), len(model["features"]))
    result = predict(["itching", "skin_rash"])
    assert result["disease"] in model["classes"]


def test_pipeline_deduplicates_and_reproduces(tmp_path, monkeypatch):
    import json
    import pandas as pd
    from scripts.create_fixture import create_fixture
    import ml.train as training

    source = tmp_path / "data" / "Training.csv"
    assert create_fixture(source)
    assert not create_fixture(source)
    data = pd.read_csv(source)
    pd.concat([data, data]).to_csv(source, index=False)
    (tmp_path / "ml").mkdir()
    monkeypatch.setattr(training, "ROOT", tmp_path)
    training.train()
    artifact = tmp_path / "ml" / "artifacts"
    report = json.loads((artifact / "metrics.json").read_text())
    assert report["duplicates_removed"] == len(data)
    assert report["train_rows"] + report["test_rows"] == len(data)
    first = (artifact / "model.json").read_bytes()
    training.train()
    assert (artifact / "model.json").read_bytes() == first
    broken = data.copy()
    broken.loc[0, "itching"] = 2
    broken.to_csv(source, index=False)
    with pytest.raises(ValueError, match="binary"):
        training.train()


def test_pipeline_rejects_conflicting_labels(tmp_path, monkeypatch):
    import pandas as pd
    from scripts.create_fixture import create_fixture
    import ml.train as training

    source = tmp_path / "data" / "Training.csv"
    create_fixture(source)
    data = pd.read_csv(source)
    conflict = data.iloc[[0]].copy()
    conflict["prognosis"] = "Different label"
    pd.concat([data, conflict]).to_csv(source, index=False)
    monkeypatch.setattr(training, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="conflicting"):
        training.train()
