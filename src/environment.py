"""Loads the frozen experiment config, assumed costs and trajectories."""

from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
ASSUMED_VIEWS = ("observable", "cot", "probe", "nla", "hybrid", "human_review")


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a mapping in {path}")
    return payload


def resolve_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return ROOT / path


class ExperimentEnvironment:
    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or ROOT / "configs" / "experiment.yaml"
        self.config = load_yaml(self.config_path)
        costs_path = resolve_path(self.config["paths"]["costs"])
        scenarios_path = resolve_path(self.config["paths"]["scenarios"])
        self.costs = load_yaml(costs_path)
        payload = load_yaml(scenarios_path)
        self.scenarios = payload.get("trajectories") or payload.get("scenarios") or []

    def get_budget_limit(self) -> float:
        return float(self.config["budget"]["limit"])

    def get_assumed_cost(self, view_name: str) -> float:
        return float(self.costs["assumed"][view_name])

    def get_monitor_cost(self, view_name: str) -> float:
        return self.get_assumed_cost(view_name)

    def uniform_views(self) -> list[str]:
        return list(self.config["budget"]["uniform_views"])

    def iter_scenarios(self) -> list[dict[str, Any]]:
        return list(self.scenarios)
