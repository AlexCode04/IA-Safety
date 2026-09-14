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
from src.optimizer import BudgetOptimizer
from src.schema import POLICY_KINDS


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
    policies = {
        kind: {
            "residual_harm": round(policy_residual_harm(records, kind), 4),
            "cost": round(sum(getattr(record.policies, kind).assumed_cost for record in records), 4),
            "WH": round(weighted_harm_prevented(records, kind), 4),
            "AS": round(attack_success_probability(records, kind), 4),
        }
        for kind in POLICY_KINDS
    }
    optimizer = BudgetOptimizer(env.costs["assumed"], env.get_budget_limit(), env.uniform_views())
    scenarios = [{"id": record.run_id} for record in records]
    benefits = {
        record.run_id: {kind: getattr(record.policies, kind).prevented_harm for kind in POLICY_KINDS}
        for record in records
    }
    lp_assignment = optimizer.plan_lp(scenarios, benefits)
    pairs = [(record, lp_assignment[record.run_id]) for record in records]
    lp_cost = sum(getattr(record.policies, kind).assumed_cost for record, kind in pairs)
    lp_attempts = [(record, kind) for record, kind in pairs if record.labels.primary_label == 1]
    lp_wh = (
        sum(getattr(record.policies, kind).prevented_harm for record, kind in lp_attempts)
        / sum(record.trajectory.severity for record, _ in lp_attempts)
        if lp_attempts and sum(record.trajectory.severity for record, _ in lp_attempts)
        else 0.0
    )
    lp_as = (
        sum(1 for record, kind in lp_attempts if getattr(record.policies, kind).residual_harm > 0)
        / len(lp_attempts)
        if lp_attempts
        else 0.0
    )
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
        "lp": {
            "cost": round(lp_cost, 4),
            "WH": round(lp_wh, 4),
            "AS": round(lp_as, 4),
            "assignment": lp_assignment,
        },
        "cost_type": "ASSUMED",
    }
    output_path = resolve_path(env.config["experiment"]["output_dir"]) / "summary.json"
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
