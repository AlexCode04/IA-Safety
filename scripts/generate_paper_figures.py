"""Generate publication figures and LaTeX result macros for Budget-NLA.

The two study-design figures are always safe to generate. Empirical figures and
``paper/generated_results.tex`` are only produced from a non-mock run unless
``--allow-mock`` is passed deliberately. This guard prevents smoke-test values
from being copied into the submission by accident.
"""

from __future__ import annotations

import argparse
import json
import math
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = ROOT / "paper"
FIGURE_DIR = PAPER_DIR / "figures"
RESULTS_DIR = ROOT / "results"

COLORS = {
    "navy": "#17365D",
    "blue": "#2F6B9A",
    "cyan": "#52A7B8",
    "green": "#3C8D70",
    "amber": "#D89B37",
    "red": "#B85450",
    "gray": "#667085",
    "light": "#F4F7FA",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-mock",
        action="store_true",
        help="Generate empirical artifacts from mock data (never for submission).",
    )
    return parser.parse_args()


def configure_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 180,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.04,
            "pdf.fonttype": 42,
        }
    )


def save(fig: plt.Figure, stem: str) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE_DIR / f"{stem}.pdf")
    fig.savefig(FIGURE_DIR / f"{stem}.png", dpi=220)
    plt.close(fig)


def _box(ax, xy, width, height, text, facecolor, *, fontsize=8.5) -> None:
    x, y = xy
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.02,rounding_size=0.025",
        linewidth=1.15,
        edgecolor=COLORS["navy"],
        facecolor=facecolor,
    )
    ax.add_patch(patch)
    ax.text(x + width / 2, y + height / 2, text, ha="center", va="center", fontsize=fontsize)


def _arrow(ax, start, end, *, color=None) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=11,
            linewidth=1.25,
            color=color or COLORS["navy"],
        )
    )


def draw_pipeline() -> None:
    fig, ax = plt.subplots(figsize=(10.8, 3.35))
    ax.set_xlim(0, 10.8)
    ax.set_ylim(0, 3.35)
    ax.axis("off")

    _box(ax, (0.15, 1.21), 1.55, 0.82, "Task + policy\nQwen2.5-7B", "#E8F0F8")
    _box(ax, (2.08, 1.21), 1.60, 0.82, "Pre-action boundary\nlayer 20", "#FFF3DC")
    _arrow(ax, (1.70, 1.62), (2.08, 1.62))

    channels = [
        (4.10, 2.45, "Observable", "#E8F0F8"),
        (4.10, 1.65, "Visible CoT", "#E7F4F1"),
        (4.10, 0.85, "Linear probe", "#FFF3DC"),
        (4.10, 0.05, "NLA readout", "#F4EAF4"),
    ]
    for x, y, label, color in channels:
        _box(ax, (x, y), 1.48, 0.52, label, color, fontsize=8)
        _arrow(ax, (3.68, 1.62), (x, y + 0.26), color=COLORS["gray"])

    _box(ax, (6.20, 1.20), 1.52, 0.84, "Isolated Gemini\njudgments", "#E8F0F8")
    for _, y, _, _ in channels:
        _arrow(ax, (5.58, y + 0.26), (6.20, 1.62), color=COLORS["gray"])

    _box(ax, (8.22, 1.20), 1.08, 0.84, "Budget policy\n+ gate", "#FBE9E7", fontsize=7.8)
    _arrow(ax, (7.72, 1.62), (8.22, 1.62))
    _box(ax, (9.78, 1.20), 0.86, 0.84, "Allow\nEscalate\nBlock", "#E7F4F1", fontsize=8)
    _arrow(ax, (9.30, 1.62), (9.78, 1.62))

    ax.text(
        5.40,
        3.22,
        "One frozen event, four evidence surfaces, one budgeted intervention decision",
        ha="center",
        va="top",
        fontsize=10.5,
        color=COLORS["navy"],
        fontweight="bold",
    )
    ax.text(
        2.88,
        0.35,
        "Tool name and arguments\nare not visible here",
        ha="center",
        va="center",
        fontsize=7.8,
        color=COLORS["red"],
    )
    save(fig, "system_pipeline")


def draw_design_matrix() -> None:
    families = ["External report", "Corporate email", "Access list"]
    conditions = ["Benign", "Attack\nrejected", "Visible\nsabotage", "Stealth\nsabotage"]
    palette = ["#DCEFE8", "#E8F0F8", "#F9E3DF", "#F3D8D5"]

    fig, ax = plt.subplots(figsize=(7.4, 3.35))
    ax.set_xlim(-0.7, 4.0)
    ax.set_ylim(-0.25, 3.55)
    ax.axis("off")
    for row, family in enumerate(families):
        y = 2.45 - row
        ax.text(-0.08, y + 0.35, family, ha="right", va="center", fontsize=8.5, fontweight="bold")
        for col, condition in enumerate(conditions):
            patch = FancyBboxPatch(
                (col + 0.05, y),
                0.82,
                0.68,
                boxstyle="round,pad=0.015,rounding_size=0.035",
                linewidth=0.9,
                edgecolor="white",
                facecolor=palette[col],
            )
            ax.add_patch(patch)
            ax.text(col + 0.46, y + 0.40, "2 fixed variants", ha="center", va="center", fontsize=7.4)
            ax.text(col + 0.46, y + 0.17, "paired", ha="center", va="center", fontsize=6.8, color=COLORS["gray"])
    for col, condition in enumerate(conditions):
        ax.text(col + 0.46, 3.28, condition, ha="center", va="center", fontsize=8.2, fontweight="bold")
    ax.text(
        1.88,
        -0.04,
        "3 task families × 4 behavioral conditions × 2 variants = 24 trajectories",
        ha="center",
        va="center",
        fontsize=9,
        color=COLORS["navy"],
        fontweight="bold",
    )
    save(fig, "experimental_matrix")


def load_empirical() -> tuple[dict, list[dict]] | None:
    summary_path = RESULTS_DIR / "summary.json"
    runs_path = RESULTS_DIR / "runs.jsonl"
    if not summary_path.exists() or not runs_path.exists():
        return None
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    records = [
        json.loads(line)
        for line in runs_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return summary, records


def _rate(value: float) -> str:
    return f"{100.0 * value:.1f}\\%"


def _number(value: float) -> str:
    if math.isclose(value, round(value), abs_tol=1e-9):
        return f"{float(value):.1f}"
    return f"{value:.3f}"


def _three_decimals(value: float) -> str:
    """Format reported efficiencies with conventional half-up rounding."""
    return str(
        Decimal(str(value)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    )


def _wilson(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    proportion = successes / total
    denominator = 1.0 + z * z / total
    center = (proportion + z * z / (2.0 * total)) / denominator
    half = z * math.sqrt(
        proportion * (1.0 - proportion) / total + z * z / (4.0 * total * total)
    ) / denominator
    return 100.0 * (center - half), 100.0 * (center + half)


def write_result_macros(summary: dict, *, mock_mode: bool) -> None:
    labels = {
        "observable": "Observable",
        "cot": "CoT",
        "probe": "Probe",
        "nla": "NLA",
    }
    if mock_mode:
        status_en = "Synthetic demonstration (deterministic mock pipeline; not a real-model evaluation)"
        status_es = "Demostración sintética (pipeline mock determinista; no es una evaluación del modelo real)"
    else:
        status_en = "Frozen real run with complete provenance"
        status_es = "Corrida real congelada con procedencia completa"
    provenance = summary.get("provenance", {}).get("source", "unknown").replace("_", "\\_")
    lines = [
        "% Auto-generated from results/summary.json. Do not edit manually.",
        f"\\newcommand{{\\resultstatusEN}}{{{status_en}}}",
        f"\\newcommand{{\\resultstatusES}}{{{status_es}}}",
        f"\\newcommand{{\\resultsource}}{{{provenance}}}",
    ]
    for key, suffix in labels.items():
        metrics = summary["primary"][key]
        phr_low, phr_high = _wilson(int(metrics["PHR_n"]), int(metrics["PHR_d"]))
        bdr_low, bdr_high = _wilson(int(metrics["BDR_n"]), int(metrics["BDR_d"]))
        lines.extend(
            [
                f"\\newcommand{{\\phr{suffix}}}{{{_rate(metrics['PHR'])}}}",
                f"\\newcommand{{\\phr{suffix}Raw}}{{{100.0 * metrics['PHR']:.1f}}}",
                f"\\newcommand{{\\phr{suffix}Count}}{{{metrics['PHR_n']}/{metrics['PHR_d']}}}",
                f"\\newcommand{{\\phr{suffix}CI}}{{{phr_low:.1f}--{phr_high:.1f}\\%}}",
                f"\\newcommand{{\\bdr{suffix}}}{{{_rate(metrics['BDR'])}}}",
                f"\\newcommand{{\\bdr{suffix}Raw}}{{{100.0 * metrics['BDR']:.1f}}}",
                f"\\newcommand{{\\bdr{suffix}Count}}{{{metrics['BDR_n']}/{metrics['BDR_d']}}}",
                f"\\newcommand{{\\bdr{suffix}CI}}{{{bdr_low:.1f}--{bdr_high:.1f}\\%}}",
                f"\\newcommand{{\\eph{suffix}}}{{{_number(metrics['EPH'])}}}",
                f"\\newcommand{{\\pe{suffix}}}{{{_three_decimals(metrics['PE'])}}}",
            ]
        )
    lines.extend(
        [
            f"\\newcommand{{\\imvNLA}}{{{_number(summary['incremental']['IMV_NLA'])}}}",
            f"\\newcommand{{\\imvNLAcoT}}{{{_number(summary['incremental']['IMV_NLA_given_CoT'])}}}",
        ]
    )
    (PAPER_DIR / "generated_results.tex").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def draw_channel_detection(summary: dict) -> None:
    keys = ["observable", "cot", "probe", "nla"]
    labels = ["Observable", "CoT", "Probe", "NLA"]
    phr = [100 * summary["primary"][key]["PHR"] for key in keys]
    bdr = [100 * summary["primary"][key]["BDR"] for key in keys]
    x = np.arange(len(keys))
    width = 0.36
    fig, ax = plt.subplots(figsize=(6.8, 3.6))
    ax.bar(x - width / 2, phr, width, label="Pre-harm recall", color=COLORS["blue"])
    ax.bar(x + width / 2, bdr, width, label="Benign disruption", color=COLORS["amber"])
    ax.set_xticks(x, labels)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Rate (%)")
    ax.grid(axis="y", alpha=0.2)
    ax.legend(frameon=False, ncols=2, loc="upper center")
    ax.set_title("Detection and disruption by monitoring channel", fontweight="bold")
    save(fig, "channel_detection")


def draw_policy_tradeoff(summary: dict) -> None:
    policies = summary["policies"]
    labels = list(policies)
    costs = [policies[key]["cost"] for key in labels]
    attack_success = [100 * policies[key]["AS"] for key in labels]
    labels.append("adaptive_lp")
    costs.append(summary["lp"]["cost"])
    attack_success.append(100 * summary["lp"]["AS"])

    fig, ax = plt.subplots(figsize=(6.8, 4.0))
    ax.scatter(costs[:-1], attack_success[:-1], s=55, color=COLORS["blue"], label="Fixed policy")
    ax.scatter(costs[-1], attack_success[-1], s=90, marker="*", color=COLORS["red"], label="Adaptive LP")
    for x, y, label in zip(costs, attack_success, labels):
        ax.annotate(label.replace("_", " "), (x, y), xytext=(4, 5), textcoords="offset points", fontsize=7)
    ax.set_xlabel("Total normalized monitoring cost (assumed)")
    ax.set_ylabel("Attack success (%)")
    ax.set_ylim(bottom=0)
    ax.grid(alpha=0.2)
    ax.legend(frameon=False)
    ax.set_title("Safety--cost trade-off under the frozen run", fontweight="bold")
    save(fig, "policy_tradeoff")


def main() -> int:
    args = parse_args()
    configure_style()
    draw_pipeline()
    draw_design_matrix()
    print(f"Wrote study-design figures to {FIGURE_DIR}")

    empirical = load_empirical()
    if empirical is None:
        print("No complete result set found; empirical paper artifacts were not generated.")
        return 0
    summary, records = empirical
    mock_mode = bool(records[0].get("experiment", {}).get("mock_mode", True))
    if mock_mode and not args.allow_mock:
        print("Detected mock results; refusing to generate submission result artifacts.")
        return 0

    write_result_macros(summary, mock_mode=mock_mode)
    draw_channel_detection(summary)
    draw_policy_tradeoff(summary)
    print("Wrote empirical figures and paper/generated_results.tex")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
