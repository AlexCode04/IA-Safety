"""Build the frozen primary and secondary metric tables."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.environment import ExperimentEnvironment, resolve_path
from src.metrics import (
    attack_success_probability,
    benign_disruption_rate,
    expected_prevented_harm,
    incremental_nla_given_cot,
    incremental_nla_value,
    load_run_records,
    policy_residual_harm,
    pre_harm_recall,
    prevention_efficiency,
    weighted_harm_prevented,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build aggregate metrics from runs.jsonl.")
    parser.add_argument("--config", default="configs/experiment.yaml")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    env = ExperimentEnvironment(ROOT / args.config)
    runs_path = resolve_path(env.config["paths"]["runs"])
    records = load_run_records(runs_path)
    if not records:
        print("No runs found. Execute scripts/run_experiment.py first.")
        return 1
    views = ["observable", "cot", "probe", "nla"]
    from src.schema import POLICY_KINDS

    policies = {
        kind: {
            "residual_harm": round(policy_residual_harm(records, kind), 4),
            "cost": round(sum(getattr(record.policies, kind).assumed_cost for record in records), 4),
            "WH": round(weighted_harm_prevented(records, kind), 4),
            "AS": round(attack_success_probability(records, kind), 4),
        }
        for kind in POLICY_KINDS
    }
    summary = {
        "spec_version": "1.0",
        "runs": len(records),
        "primary": {
            view: {
                "PHR": round(pre_harm_recall(records, view), 4),
                "BDR": round(benign_disruption_rate(records, view), 4),
                "EPH": round(expected_prevented_harm(records, view), 4),
                "PE": round(prevention_efficiency(records, view), 4),
            }
            for view in views
        },
        "incremental": {
            "IMV_NLA": round(incremental_nla_value(records), 4),
            "IMV_NLA_given_CoT": round(incremental_nla_given_cot(records), 4),
        },
        "policies": policies,
        "cost_type": "ASSUMED",
    }
    output_path = resolve_path(env.config["experiment"]["output_dir"]) / "summary.json"
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
