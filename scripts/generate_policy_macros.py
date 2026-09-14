"""Generate shared LaTeX policy-table macros from the canonical result contract.

This keeps the English and Spanish papers numerically synchronized. The script
reads ``results/summary.json`` plus ``results/runs.jsonl`` and writes
``paper/generated_policy_results.tex``. Do not edit the generated TeX file by
hand after a new experiment run; regenerate it with this script instead.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
OUTPUT = ROOT / "paper" / "generated_policy_results.tex"

POLICIES = {
    "baseline": "Baseline",
    "action_only": "ActionOnly",
    "nla_probe_cot": "NlaProbeCot",
    "probe_nla_cot": "ProbeNlaCot",
    "cot_nla": "CotNla",
}


def _number(value: float) -> str:
    value = float(value)
    if value.is_integer():
        return f"{value:.1f}"
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _percent(value: float) -> str:
    return f"{100.0 * float(value):.1f}\\%"


def _load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> int:
    summary_path = RESULTS_DIR / "summary.json"
    runs_path = RESULTS_DIR / "runs.jsonl"
    if not summary_path.exists() or not runs_path.exists():
        raise SystemExit(
            "Missing results/summary.json or results/runs.jsonl. "
            "Run the experiment and scripts/build_results.py first."
        )

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    runs = _load_jsonl(runs_path)
    total_attack_harm = sum(
        float(row["trajectory"]["severity"])
        for row in runs
        if int(row["labels"]["primary_label"]) == 1
    )

    lines = [
        "% Auto-generated from results/summary.json and results/runs.jsonl.",
        "% Shared by main_en.tex and main_es.tex. Do not edit manually.",
    ]

    for key, suffix in POLICIES.items():
        policy = summary["policies"][key]
        lines.extend(
            [
                f"\\newcommand{{\\policy{suffix}Cost}}{{{_number(policy['cost'])}}}",
                f"\\newcommand{{\\policy{suffix}Residual}}{{{_number(policy['residual_harm'])}}}",
                f"\\newcommand{{\\policy{suffix}AS}}{{{_percent(policy['AS'])}}}",
            ]
        )

    lp = summary["lp"]
    lp_residual = total_attack_harm * (1.0 - float(lp["WH"]))
    lines.extend(
        [
            f"\\newcommand{{\\policyLPCost}}{{{_number(lp['cost'])}}}",
            f"\\newcommand{{\\policyLPResidual}}{{{_number(lp_residual)}}}",
            f"\\newcommand{{\\policyLPAS}}{{{_percent(lp['AS'])}}}",
        ]
    )

    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
