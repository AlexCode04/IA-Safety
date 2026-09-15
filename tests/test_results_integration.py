"""Regression tests for result provenance and external verdict integration."""

import json

import pytest

from scripts.build_results import load_gemini_verdicts, verdict_stops_action


def test_block_and_escalate_both_pause_the_action() -> None:
    assert verdict_stops_action({"gate_decision": "block"})
    assert verdict_stops_action({"gate_decision": "escalate"})
    assert not verdict_stops_action({"gate_decision": "allow"})


def test_loader_refuses_to_mix_gemini_models(tmp_path) -> None:
    path = tmp_path / "verdicts.jsonl"
    rows = [
        {
            "scenario_id": "s1",
            "monitor_channel": "observable",
            "monitor_model": "model-a",
        },
        {
            "scenario_id": "s1",
            "monitor_channel": "cot",
            "monitor_model": "model-b",
        },
    ]
    path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="multiple models"):
        load_gemini_verdicts(path, model=None)


def test_loader_rejects_duplicate_scenario_channel(tmp_path) -> None:
    path = tmp_path / "verdicts.jsonl"
    row = {
        "scenario_id": "s1",
        "monitor_channel": "nla",
        "monitor_model": "model-a",
    }
    path.write_text(
        json.dumps(row) + "\n" + json.dumps(row) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Duplicate"):
        load_gemini_verdicts(path, model="model-a")
