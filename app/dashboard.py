"""Budget-NLA dashboard. Four tabs: escenarios, deteccion, presupuesto, trade-off."""

from __future__ import annotations

import json
import sys
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.environment import ExperimentEnvironment, resolve_path
from src.metrics import (
    attack_success_probability,
    benign_disruption_rate,
    expected_prevented_harm,
    incremental_nla_value,
    load_run_records,
    policy_residual_harm,
    pre_harm_recall,
    weighted_harm_prevented,
)


def _summary(env) -> dict:
    runs_path = resolve_path(env.config["paths"]["runs"])
    path = Path(runs_path).with_name("summary.json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _assignments(env) -> pd.DataFrame:
    summary = _summary(env)
    assignment = summary.get("lp", {}).get("assignment", {})
    return pd.DataFrame(
        [{"run_id": run_id, "policy": policy} for run_id, policy in assignment.items()]
    )


def main() -> None:
    st.set_page_config(page_title="Budget-NLA", layout="wide")
    st.title("BUDGET-NLA")
    st.caption("Risk-weighted adaptive monitoring. Assumed costs are dashboard defaults, not measurements.")
    env = ExperimentEnvironment(ROOT / "configs" / "experiment.yaml")
    runs_path = resolve_path(env.config["paths"]["runs"])
    records = load_run_records(runs_path)
    summary = _summary(env)
    per_view, per_policy = {}, {}
    if records:
        views = ["observable", "cot", "probe", "nla"]
        per_view = {
            view: {
                "PHR": pre_harm_recall(records, view),
                "BDR": benign_disruption_rate(records, view),
                "EPH": expected_prevented_harm(records, view),
            }
            for view in views
        }
        per_policy = {
            kind: {
                "WH": weighted_harm_prevented(records, kind),
                "AS": attack_success_probability(records, kind),
                "residual harm": policy_residual_harm(records, kind),
            }
            for kind in ("baseline", "action_only", "nla_probe_cot", "probe_nla_cot", "cot_nla")
        }
        incremental = incremental_nla_value(records)

    tab_escenarios, tab_deteccion, tab_presupuesto, tab_tradeoff = st.tabs(
        ["escenarios", "deteccion", "presupuesto", "trade-off"]
    )

    with tab_escenarios:
        st.subheader("Escenarios")
        if not records:
            st.warning("No runs yet. Execute `python scripts/run_experiment.py` first.")
        else:
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "scenario_id": record.scenario_id,
                            "family": record.labels.family,
                            "condition": record.labels.condition,
                            "primary_label": record.labels.primary_label,
                            "harm_committed": record.labels.harm_committed,
                            "triggered": record.triggered_tools,
                        }
                        for record in records
                    ]
                ),
                use_container_width=True,
            )

    with tab_deteccion:
        st.subheader("Deteccion por senal")
        if not records:
            st.warning("No runs yet.")
        else:
            rows = []
            for view, metrics in per_view.items():
                rows.append({"senal": view, **metrics})
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
            st.caption(f"IMV de NLA sobre CoT: {incremental:.3f}" if incremental is not None else "IMV no disponible")

    with tab_presupuesto:
        st.subheader("Presupuesto adaptativo (LP)")
        if summary:
            lp = summary.get("lp", {})
            st.metric("costo plan (pc)", f"{lp.get('cost', 0.0):.2f}")
            st.metric("WH plan (pc)", f"{lp.get('weighted_harm_prevented', 0.0):.2f}")
            st.metric("AS plan (pc)", f"{lp.get('attack_success_probability', 0.0):.2f}")
            assignment = _assignments(env)
            if not assignment.empty:
                counts = assignment["policy"].value_counts().rename_axis("policy").reset_index(name="scenarios")
                st.dataframe(counts, use_container_width=True)
                with st.expander("asignacion por run"):
                    st.dataframe(assignment, use_container_width=True)
        else:
            st.info("Corre `python scripts/build_results.py` para poblar el plan LP.")

    with tab_tradeoff:
        st.subheader("Trade-off harm / presupuesto")
        if per_policy:
            rows = []
            for kind, metrics in per_policy.items():
                rows.append({"politica": kind, **metrics})
            frame = pd.DataFrame(rows)
            st.dataframe(frame, use_container_width=True)
            st.bar_chart(frame.set_index("politica")[["WH", "AS"]])
        else:
            st.info("Sin metricas por politica.")


if __name__ == "__main__":
    main()