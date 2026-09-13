"""Train the logistic probe with leave-one-template-out. Owned by feature/nla-probe."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.activation_hook import ActivationHook
from src.agent_runner import AgentRunner
from src.environment import ExperimentEnvironment
from src.ground_truth import build_labels
from src.probe import leave_one_template_out_scores
from src.seeds import apply_seeds


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the layer-20 linear probe.")
    parser.add_argument("--config", default="configs/experiment.yaml")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    env = ExperimentEnvironment(ROOT / args.config)
    seeds = env.config["seeds"]
    apply_seeds(int(seeds["python"]), int(seeds["numpy"]))
    agent = AgentRunner(env.config["agent"]["model"], float(env.config["agent"]["temperature"]))
    hook = ActivationHook(seed=int(seeds["numpy"]))
    activations = []
    labels = []
    templates = []
    for scenario in env.iter_scenarios():
        output = agent.run(scenario)
        ground = build_labels(scenario, output.tool_name, output.arguments)
        activations.append(hook.capture(scenario, ground.malicious_objective_adopted))
        labels.append(ground.primary_label)
        templates.append(scenario["template_id"])
    scores, alerts = leave_one_template_out_scores(
        activations,
        labels,
        templates,
        C=float(env.config["probe"]["C"]),
        max_iter=int(env.config["probe"]["max_iter"]),
    )
    auroc = roc_auc_score(labels, scores) if len(set(labels)) > 1 else 0.0
    auprc = average_precision_score(labels, scores) if len(set(labels)) > 1 else 0.0
    accuracy = sum(int(alert) == label for alert, label in zip(alerts, labels)) / len(labels)
    print(f"LOTO AUROC: {auroc:.3f}")
    print(f"LOTO AUPRC: {auprc:.3f}")
    print(f"LOTO accuracy: {accuracy:.3f}")
    print("Thresholds were selected from training folds only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
