"""Audit per-scenario policy enforcement and anti-leak constraints."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ground_truth import build_labels
from src.tools import is_unauthorized, matches_harmful_action


SCENARIOS_PATH = ROOT / "data" / "scenarios.yaml"
FORBIDDEN_MARKERS = ("CANARY_", "PRIVATE_")


def main() -> int:
    with SCENARIOS_PATH.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)

    scenarios = payload["trajectories"]
    errors: list[str] = []

    if len(scenarios) != 24:
        errors.append(f"Expected 24 scenarios, found {len(scenarios)}.")

    for scenario in scenarios:
        scenario_id = scenario["scenario_id"]

        if "authorized_action" not in scenario:
            errors.append(f"{scenario_id}: missing authorized_action.")
            continue

        if "harmful_action" not in scenario:
            errors.append(f"{scenario_id}: missing harmful_action.")
            continue

        if not scenario.get("protected_resource"):
            errors.append(f"{scenario_id}: missing protected_resource.")

        if not scenario.get("harm_event"):
            errors.append(f"{scenario_id}: missing harm_event.")

        authorized_action = scenario["authorized_action"]
        harmful_action = scenario["harmful_action"]

        authorized_violation = is_unauthorized(
            scenario,
            authorized_action["tool"],
            authorized_action["arguments"],
        )

        if authorized_violation:
            errors.append(
                f"{scenario_id}: authorized_action was incorrectly rejected."
            )

        harmful_violation = is_unauthorized(
            scenario,
            harmful_action["tool"],
            harmful_action["arguments"],
        )

        if not harmful_violation:
            errors.append(
                f"{scenario_id}: harmful_action was not rejected by policy."
            )

        declared_harm = matches_harmful_action(
            scenario,
            harmful_action["tool"],
            harmful_action["arguments"],
        )

        if not declared_harm:
            errors.append(
                f"{scenario_id}: harmful_action does not match its declaration."
            )

        safe_labels = build_labels(
            scenario,
            authorized_action["tool"],
            authorized_action["arguments"],
            committed=True,
        )

        if safe_labels.primary_label != 0 or safe_labels.harm_committed:
            errors.append(
                f"{scenario_id}: authorized action produced harmful labels."
            )

        harmful_labels = build_labels(
            scenario,
            harmful_action["tool"],
            harmful_action["arguments"],
            committed=True,
        )

        if harmful_labels.primary_label != 1:
            errors.append(
                f"{scenario_id}: harmful action did not produce attack label 1."
            )

        if not harmful_labels.harm_committed:
            errors.append(
                f"{scenario_id}: harmful committed action did not produce harm."
            )

        if harmful_labels.harm_event != scenario["harm_event"]:
            errors.append(
                f"{scenario_id}: harm_event does not match scenario configuration."
            )

    for directory in (ROOT / "src", ROOT / "data"):
        for path in directory.rglob("*"):
            if not path.is_file():
                continue

            if path.suffix not in {".py", ".yaml", ".csv", ".md"}:
                continue

            text = path.read_text(encoding="utf-8").upper()

            for marker in FORBIDDEN_MARKERS:
                if marker in text:
                    errors.append(
                        f"{path.relative_to(ROOT)} still contains {marker}."
                    )

    if errors:
        print("Module 2 policy audit failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Module 2 policy audit passed.")
    print("- 24 scenarios contain explicit authorized and harmful actions")
    print("- Every authorized action is accepted by its own scenario policy")
    print("- Every harmful action is rejected programmatically")
    print("- Every harmful action produces its configured harm_event")
    print("- No CANARY_ or PRIVATE_ markers remain in src/ or data/")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())