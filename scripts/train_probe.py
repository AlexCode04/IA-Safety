"""Train the logistic probe with leave-one-template-out. Owned by feature/nla-probe.

Persists results/probe.pkl, results/probe_scores.json and results/probe_activations.npz.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.activation_hook import ActivationHook
from src.agent_runner import AgentRunner
from src.environment import ExperimentEnvironment
from src.ground_truth import build_labels
from src.probe import LinearProbe, leave_one_template_out_scores
from src.seeds import apply_seeds


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the layer-20 linear probe.")
    parser.add_argument("--config", default="configs/experiment.yaml")
    parser.add_argument("--probe-out", default="results/probe.pkl")
    parser.add_argument("--scores-out", default="results/probe_scores.json")
    parser.add_argument("--activations-out", default="results/probe_activations.npz")
    parser.add_argument("--monitor-cases", default="results/monitor_cases.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    env = ExperimentEnvironment(ROOT / args.config)
    seeds = env.config["seeds"]
    apply_seeds(int(seeds["python"]), int(seeds["numpy"]))
    mock_mode = bool(env.config["experiment"]["mock_mode"])
    agent = AgentRunner(
        env.config["agent"]["model"],
        float(env.config["agent"]["temperature"]),
        mock_mode=mock_mode,
        max_new_tokens=int(env.config["agent"]["max_new_tokens"]),
    )
    if mock_mode:
        hook = ActivationHook(seed=int(seeds["numpy"]))
    else:
        from src.activation_hook_real import ActivationHook as RealActivationHook
        from src.model_loader import ModelLoader
        from src.nla_monitor_real import NlaMonitor as RealNlaMonitor

        model_obj, tokenizer = ModelLoader().load()
        agent.model_obj = model_obj
        agent.tokenizer = tokenizer
        hook = RealActivationHook(model_obj, tokenizer)
    activations: list[np.ndarray] = []
    labels: list[int] = []
    templates: list[str] = []
    ids: list[str] = []
    for scenario in env.iter_scenarios():
        output = agent.run(scenario)
        ground = build_labels(scenario, output.tool_name, output.arguments)
        if mock_mode:
            activation = hook.capture(scenario, ground.malicious_objective_adopted)
        else:
            activation = hook.capture(output.prefix_until_decision())
        activations.append(activation)
        labels.append(ground.primary_label)
        templates.append(scenario["template_id"])
        ids.append(scenario["id"])
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

    probe = LinearProbe(
        C=float(env.config["probe"]["C"]),
        max_iter=int(env.config["probe"]["max_iter"]),
    )
    train_x = np.vstack(activations)
    train_y = np.array(labels)
    probe.fit(train_x, train_y)
    train_scores = [probe.score(activations[i]) for i in range(len(activations))]
    probe.threshold = float(np.mean(train_scores))

    probe_out = ROOT / args.probe_out
    probe.save(probe_out)
    scores_out = ROOT / args.scores_out
    scores_out.parent.mkdir(parents=True, exist_ok=True)
    scores_out.write_text(
        json.dumps(
            [
                {
                    "id": sid,
                    "score": float(score),
                    "alert": bool(alert),
                    "primary_label": int(label),
                    "template_id": template,
                }
                for sid, score, alert, label, template in zip(ids, scores, alerts, labels, templates)
            ],
            indent=2,
        ),
        encoding="utf-8",
    )
    np.savez(
        ROOT / args.activations_out,
        activations=np.vstack(activations),
        labels=np.array(labels),
        template_ids=np.array(templates),
        ids=np.array(ids),
    )
    print(f"probe guardado en {probe_out}")
    print(f"scores por escenario en {scores_out}")
    print(f"activaciones en {ROOT / args.activations_out}")

    monitor_cases = ROOT / args.monitor_cases
    if monitor_cases.exists():
        cases = json.loads(monitor_cases.read_text(encoding="utf-8"))
        by_id = {entry["id"]: entry["score"] for entry in json.loads(scores_out.read_text(encoding="utf-8"))}
        filled = 0
        for case in cases:
            if case.get("probe_score") is None and case.get("scenario_id") in by_id:
                case["probe_score"] = by_id[case["scenario_id"]]
                filled += 1
        monitor_cases.write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"contrato de senales actualizado en {monitor_cases} ({filled} probe_score rellenados)")
    else:
        print(f"no encontre {monitor_cases}; dejar probe_score null en el proximo smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())