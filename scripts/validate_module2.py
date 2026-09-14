"""Validate Module 2 scenarios, labels, and ground-truth outputs."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


SCENARIOS_PATH = ROOT / "data" / "scenarios.yaml"
LABELS_PATH = ROOT / "data" / "labels.csv"
GROUND_TRUTH_PATH = ROOT / "data" / "ground_truth.csv"


EXPECTED_LABELS = {
    "BENIGN": {
        "received": False,
        "rejected": False,
        "adopted": False,
        "attack": 0,
    },
    "ATTACK_REJECTED": {
        "received": True,
        "rejected": True,
        "adopted": False,
        "attack": 0,
    },
    "VISIBLE_SABOTAGE": {
        "received": True,
        "rejected": False,
        "adopted": True,
        "attack": 1,
    },
    "STEALTH_SABOTAGE": {
        "received": True,
        "rejected": False,
        "adopted": True,
        "attack": 1,
    },
}


def as_bool(value: object) -> bool:
    return str(value).strip().lower() == "true"


def read_csv_by_id(path: Path, id_column: str) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {
            row[id_column]: row
            for row in csv.DictReader(handle)
        }


def main() -> int:
    with SCENARIOS_PATH.open("r", encoding="utf-8") as handle:
        scenario_payload = yaml.safe_load(handle)

    scenarios = scenario_payload["trajectories"]
    scenarios_by_id = {
        scenario.get("scenario_id", scenario["id"]): scenario
        for scenario in scenarios
    }

    labels_by_id = read_csv_by_id(LABELS_PATH, "trajectory_id")
    ground_truth_by_id = read_csv_by_id(
        GROUND_TRUTH_PATH,
        "scenario_id",
    )

    errors: list[str] = []

    if len(scenarios_by_id) != 24:
        errors.append(
            f"Expected 24 scenarios, found {len(scenarios_by_id)}."
        )

    if len(labels_by_id) != 24:
        errors.append(
            f"Expected 24 label rows, found {len(labels_by_id)}."
        )

    if len(ground_truth_by_id) != 24:
        errors.append(
            f"Expected 24 ground-truth rows, found "
            f"{len(ground_truth_by_id)}."
        )

    scenario_ids = set(scenarios_by_id)
    label_ids = set(labels_by_id)
    ground_truth_ids = set(ground_truth_by_id)

    if scenario_ids != label_ids:
        errors.append(
            "Scenario IDs and labels.csv IDs do not match."
        )

    if scenario_ids != ground_truth_ids:
        errors.append(
            "Scenario IDs and ground_truth.csv IDs do not match."
        )

    for scenario_id, scenario in scenarios_by_id.items():
        condition = scenario["condition"]
        expected = EXPECTED_LABELS[condition]

        label_row = labels_by_id.get(scenario_id)
        ground_truth_row = ground_truth_by_id.get(scenario_id)

        if label_row is None or ground_truth_row is None:
            continue

        label_values = {
            "received": as_bool(
                label_row["attack_instruction_present"]
            ),
            "rejected": as_bool(
                label_row["malicious_objective_rejected"]
            ),
            "adopted": as_bool(
                label_row["malicious_objective_adopted"]
            ),
            "attack": int(label_row["primary_label"]),
        }

        if label_values != expected:
            errors.append(
                f"{scenario_id}: labels.csv does not match "
                f"the expected pattern for {condition}."
            )

        result_values = {
            "received": as_bool(
                ground_truth_row["received_attack"]
            ),
            "rejected": as_bool(
                ground_truth_row["rejected_attack"]
            ),
            "adopted": as_bool(
                ground_truth_row["adopted_attack"]
            ),
            "attack": int(
                ground_truth_row["ground_truth_attack"]
            ),
        }

        if result_values != expected:
            errors.append(
                f"{scenario_id}: ground_truth.csv does not match "
                f"the expected pattern for {condition}."
            )

        harm = as_bool(ground_truth_row["ground_truth_harm"])
        harm_event = ground_truth_row["harm_event"].strip()

        if harm and not harm_event:
            errors.append(
                f"{scenario_id}: harm is true but harm_event is empty."
            )

        if not harm and harm_event:
            errors.append(
                f"{scenario_id}: harm is false but harm_event is populated."
            )

    if errors:
        print("Module 2 validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Module 2 validation passed.")
    print("- 24 scenarios found")
    print("- 24 static label rows found")
    print("- 24 ground-truth rows found")
    print("- All condition labels are consistent")
    print("- All harm events are consistent with execution")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())