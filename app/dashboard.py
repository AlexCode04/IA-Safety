"""Dashboard for assumed costs and primary containment metrics."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.environment import ExperimentEnvironment, resolve_path
from src.metrics import (
    benign_disruption_rate,
    expected_prevented_harm,
    load_run_records,
    policy_residual_harm,
    pre_harm_recall,
)


def main() -> None:
    st.set_page_config(page_title="Budget-NLA", layout="wide")
    st.title("BUDGET-NLA")
    st.caption("Risk-weighted adaptive monitoring. Assumed costs are dashboard defaults, not measurements.")
    env = ExperimentEnvironment(ROOT / "configs" / "experiment.yaml")
    runs_path = resolve_path(env.config["paths"]["runs"])
    records = load_run_records(runs_path)
    if not records:
        st.warning("No runs yet. Execute `python scripts/run_experiment.py` first.")
        return
    views = ["observable", "cot", "probe", "nla"]
    columns = st.columns(4)
    for column, view in zip(columns, views):
        column.metric(f"{view} PHR", f"{pre_harm_recall(records, view):.2f}")
        column.metric(f"{view} BDR", f"{benign_disruption_rate(records, view):.2f}")
        column.metric(f"{view} EPH", f"{expected_prevented_harm(records, view):.2f}")
    left, right = st.columns(2)
    left.metric("Uniform residual harm", f"{policy_residual_harm(records, 'uniform'):.2f}")
    right.metric("Adaptive residual harm", f"{policy_residual_harm(records, 'adaptive'):.2f}")
    st.subheader("Assumed monitoring costs")
    st.json(env.costs["assumed"])
    metrics_path = resolve_path(env.config["paths"]["metrics"])
    if metrics_path.exists():
        st.dataframe(pd.read_csv(metrics_path), use_container_width=True)


if __name__ == "__main__":
    main()
