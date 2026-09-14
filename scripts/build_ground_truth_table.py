"""Build the ground-truth table from completed experiment runs."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


INPUT_PATH = ROOT / "results" / "runs.jsonl"
OUTPUT_PATH = ROOT / "data" / "ground_truth.csv"


def main() -> int:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Results file not found: {INPUT_PATH}. "
            "Run scripts/run_experiment.py first."
        )

    rows: list[dict[str, object]] = []

    with INPUT_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue

            record = json.loads(line)
            trajectory = record["trajectory"]
            labels = record["labels"]
            tool_call = record["tool_call"]
            adaptive_policy = record["policies"]["adaptive"]

            rows.append(
                {
                    "run_id": record["run_id"],
                    "scenario_id": trajectory["id"],
                    "task_family": trajectory["family"],
                    "condition": trajectory["condition"],
                    "variant": trajectory["variant"],
                    "severity": trajectory["severity"],
                    "received_attack": labels["attack_instruction_present"],
                    "rejected_attack": labels["malicious_objective_rejected"],
                    "adopted_attack": labels["malicious_objective_adopted"],
                    "ground_truth_attack": labels["primary_label"],
                    "ground_truth_harm": labels["harm_committed"],
                    "harm_event": labels["harm_event"] or "",
                    "tool_name": tool_call["name"],
                    "tool_committed": tool_call["committed"],
                    "adaptive_policy_decision": adaptive_policy["decision"],
                }
            )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "run_id",
        "scenario_id",
        "task_family",
        "condition",
        "variant",
        "severity",
        "received_attack",
        "rejected_attack",
        "adopted_attack",
        "ground_truth_attack",
        "ground_truth_harm",
        "harm_event",
        "tool_name",
        "tool_committed",
        "adaptive_policy_decision",
    ]

    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} ground-truth rows to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())