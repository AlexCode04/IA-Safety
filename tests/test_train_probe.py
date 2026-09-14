import json

import pytest

from src.environment import ExperimentEnvironment


@pytest.fixture
def probe_env(tmp_path, monkeypatch):
    env = ExperimentEnvironment()
    outputs = {
        "probe_out": str(tmp_path / "probe.pkl"),
        "scores_out": str(tmp_path / "probe_scores.json"),
        "activations_out": str(tmp_path / "probe_activations.npz"),
        "monitor_cases": str(tmp_path / "monitor_cases.json"),
    }
    fake_args = type("Args", (), dict(config="configs/experiment.yaml", **outputs))
    return env, tmp_path, monkeypatch, fake_args


def test_train_probe_persists_artifacts_in_mock(probe_env):
    import scripts.train_probe as trainer

    env, tmp_path, monkeypatch, fake_args = probe_env
    monkeypatch.setattr(
        trainer,
        "parse_args",
        lambda: fake_args,
    )
    assert trainer.main() == 0
    assert (tmp_path / "probe.pkl").exists()
    scores = json.loads((tmp_path / "probe_scores.json").read_text(encoding="utf-8"))
    assert len(scores) == 24
    assert all("id" in entry and "score" in entry for entry in scores)
    assert (tmp_path / "probe_activations.npz").exists()
    assert all(0.0 <= entry["score"] <= 1.0 for entry in scores)


def test_train_probe_fills_monitor_cases(probe_env):
    import scripts.train_probe as trainer

    env, tmp_path, monkeypatch, fake_args = probe_env
    (tmp_path / "monitor_cases.json").write_text(
        json.dumps(
            [
                {"scenario_id": "external_report-BENIGN-v1", "probe_score": None},
                {"scenario_id": "non-existent-id", "probe_score": None},
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(trainer, "parse_args", lambda: fake_args)
    assert trainer.main() == 0
    cases = json.loads((tmp_path / "monitor_cases.json").read_text(encoding="utf-8"))
    by_id = {entry["id"]: entry["score"] for entry in json.loads((tmp_path / "probe_scores.json").read_text(encoding="utf-8"))}
    assert cases[0]["probe_score"] == by_id["external_report-BENIGN-v1"]
    assert cases[1]["probe_score"] is None