"""Export runs.jsonl into the SQLite execution store (scenario/trajectory/step/policy/activation)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.environment import ExperimentEnvironment, resolve_path
from src.metrics import load_run_records
from src.store import export_runs_to_sqlite


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export runs.jsonl to SQLite.")
    parser.add_argument("--config", default="configs/experiment.yaml")
    parser.add_argument("--db", default=None, help="Override SQLite path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    env = ExperimentEnvironment(ROOT / args.config)
    records = load_run_records(resolve_path(env.config["paths"]["runs"]))
    if not records:
        print("No runs found. Execute scripts/run_experiment.py first.")
        return 1
    db_path = Path(args.db) if args.db else resolve_path(env.config["paths"]["db"])
    n = export_runs_to_sqlite(records, db_path)
    print(f"Exported {n} records to {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())