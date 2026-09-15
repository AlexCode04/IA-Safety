#!/usr/bin/env python3
"""Regenerate the browser-only dashboard preview from canonical run artifacts."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.dashboard import build_payload, load_summary, render_html
from src.environment import ExperimentEnvironment, resolve_path
from src.metrics import load_run_records


def main() -> None:
    env = ExperimentEnvironment(ROOT / "configs" / "experiment.yaml")
    runs_path = resolve_path(env.config["paths"]["runs"])
    records = load_run_records(runs_path)
    if not records:
        raise SystemExit(
            "No run records found. Execute scripts/run_experiment.py first."
        )

    payload = build_payload(records, env.costs["assumed"], load_summary(runs_path))
    output = ROOT / "app" / "web" / "preview.html"
    output.write_text(render_html(payload), encoding="utf-8")
    print(f"Wrote {output.relative_to(ROOT)} from {len(records)} canonical records.")


if __name__ == "__main__":
    main()
