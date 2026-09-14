# -*- coding: utf-8 -*-
"""Bilingual Budget-NLA dashboard for signals, policies and Gemini results."""

from __future__ import annotations

import json
import sys
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
from src.schema import POLICY_KINDS


TEXT = {
    "es": {
        "language": "Idioma",
        "caption": (
            "Monitoreo adaptativo para detener sabotaje antes del daño. "
            "Los costos son supuestos; la latencia y los tokens se miden."
        ),
        "tabs": ["Escenarios", "Detección", "Presupuesto", "Trade-off", "Gemini"],
        "titles": [
            "Escenarios evaluados",
            "Detección por señal",
            "Asignación adaptativa del presupuesto",
            "Daño frente a presupuesto",
            "Evaluaciones externas de Gemini",
        ],
        "no_runs": "Aún no hay corridas. Ejecuta `python scripts/run_experiment.py`.",
        "no_summary": "Ejecuta `python scripts/build_results.py` para calcular el plan.",
        "no_gemini": "Aún no hay veredictos de Gemini.",
        "gemini_hint": "Ejecuta `python scripts/run_gemini_monitor.py --limit 3` como prueba.",
        "signal": "Señal",
        "policy": "Política",
        "scenarios": "Escenarios",
        "assignment": "Asignación por corrida",
        "costs": "Costos relativos asumidos",
        "cost_caption": "Valores normalizados para comparar políticas; no son precios reales.",
        "metric_phr": "Sabotajes detenidos a tiempo",
        "metric_bdr": "Falsas alarmas",
        "metric_eph": "Daño evitado",
        "imv": "Valor incremental de NLA sobre observable",
        "lp_cost": "Costo del plan",
        "lp_wh": "Daño ponderado evitado",
        "lp_as": "Éxito del ataque",
        "evaluations": "Evaluaciones",
        "expected_match": "Acuerdo esperado",
        "mean_risk": "Riesgo medio",
        "mean_latency": "Latencia media (ms)",
        "details": "Detalle",
        "yes": "Sí",
        "no": "No",
        "channels": {
            "observable": "Acciones visibles",
            "cot": "Razonamiento visible",
            "probe": "Probe lineal",
            "nla": "Lectura NLA",
            "hybrid": "Híbrido",
        },
        "families": {
            "external_report": "Publicación de informe",
            "corporate_email": "Correo corporativo",
            "access_list": "Lista de acceso",
        },
        "conditions": {
            "BENIGN": "Benigno",
            "ATTACK_REJECTED": "Ataque rechazado",
            "VISIBLE_SABOTAGE": "Sabotaje visible",
            "STEALTH_SABOTAGE": "Sabotaje encubierto",
        },
    },
    "en": {
        "language": "Language",
        "caption": (
            "Adaptive monitoring to stop sabotage before harm. "
            "Costs are assumed; latency and tokens are measured."
        ),
        "tabs": ["Scenarios", "Detection", "Budget", "Trade-off", "Gemini"],
        "titles": [
            "Evaluated scenarios",
            "Detection by signal",
            "Adaptive budget allocation",
            "Harm versus budget",
            "External Gemini evaluations",
        ],
        "no_runs": "No runs yet. Execute `python scripts/run_experiment.py`.",
        "no_summary": "Run `python scripts/build_results.py` to compute the plan.",
        "no_gemini": "No Gemini verdicts are available yet.",
        "gemini_hint": "Run `python scripts/run_gemini_monitor.py --limit 3` as a preflight.",
        "signal": "Signal",
        "policy": "Policy",
        "scenarios": "Scenarios",
        "assignment": "Assignment by run",
        "costs": "Assumed relative costs",
        "cost_caption": "Normalized policy-comparison values; these are not prices.",
        "metric_phr": "Sabotage stopped in time",
        "metric_bdr": "False alarms",
        "metric_eph": "Harm prevented",
        "imv": "Incremental NLA value over observable",
        "lp_cost": "Plan cost",
        "lp_wh": "Weighted harm prevented",
        "lp_as": "Attack success",
        "evaluations": "Evaluations",
        "expected_match": "Expected agreement",
        "mean_risk": "Mean risk",
        "mean_latency": "Mean latency (ms)",
        "details": "Details",
        "yes": "Yes",
        "no": "No",
        "channels": {
            "observable": "Observable actions",
            "cot": "Visible reasoning",
            "probe": "Linear probe",
            "nla": "NLA readout",
            "hybrid": "Hybrid",
        },
        "families": {
            "external_report": "Report publication",
            "corporate_email": "Corporate email",
            "access_list": "Access list",
        },
        "conditions": {
            "BENIGN": "Benign",
            "ATTACK_REJECTED": "Attack rejected",
            "VISIBLE_SABOTAGE": "Visible sabotage",
            "STEALTH_SABOTAGE": "Stealth sabotage",
        },
    },
}


def _language() -> str:
    current = st.query_params.get("lang", "es")
    if current not in TEXT:
        current = "es"
    selected = st.radio(
        TEXT[current]["language"],
        ["es", "en"],
        index=0 if current == "es" else 1,
        format_func=lambda value: "Español" if value == "es" else "English",
        horizontal=True,
    )
    if selected != current:
        st.query_params["lang"] = selected
    return selected


def _summary(env: ExperimentEnvironment) -> dict:
    path = Path(resolve_path(env.config["paths"]["runs"])).with_name("summary.json")
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _gemini_results() -> pd.DataFrame:
    path = ROOT / "results" / "gemini_verdicts.jsonl"
    if not path.exists():
        return pd.DataFrame()
    return pd.DataFrame(
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def _yes_no(value: bool, copy: dict) -> str:
    return copy["yes"] if value else copy["no"]


def main() -> None:
    st.set_page_config(page_title="Budget-NLA", layout="wide")
    copy = TEXT[_language()]
    st.title("BUDGET-NLA")
    st.caption(copy["caption"])

    env = ExperimentEnvironment(ROOT / "configs" / "experiment.yaml")
    records = load_run_records(resolve_path(env.config["paths"]["runs"]))
    summary = _summary(env)
    tabs = st.tabs(copy["tabs"])

    with tabs[0]:
        st.subheader(copy["titles"][0])
        if not records:
            st.warning(copy["no_runs"])
        else:
            rows = [
                {
                    "ID": record.trajectory.id,
                    "Family": copy["families"].get(record.trajectory.family, record.trajectory.family),
                    "Condition": copy["conditions"].get(record.trajectory.condition, record.trajectory.condition),
                    "Sabotage": _yes_no(record.labels.primary_label == 1, copy),
                    "Tool": record.tool_call.name,
                    "Unauthorized": _yes_no(record.tool_call.unauthorized, copy),
                }
                for record in records
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with tabs[1]:
        st.subheader(copy["titles"][1])
        if not records:
            st.warning(copy["no_runs"])
        else:
            views = ("observable", "cot", "probe", "nla")
            rows = [
                {
                    copy["signal"]: copy["channels"][view],
                    "PHR": pre_harm_recall(records, view),
                    "BDR": benign_disruption_rate(records, view),
                    "EPH": expected_prevented_harm(records, view),
                }
                for view in views
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.caption(f"{copy['imv']}: {incremental_nla_value(records):.3f}")

    with tabs[2]:
        st.subheader(copy["titles"][2])
        if summary:
            lp = summary.get("lp", {})
            left, middle, right = st.columns(3)
            left.metric(copy["lp_cost"], f"{lp.get('cost', 0.0):.2f}")
            middle.metric(copy["lp_wh"], f"{lp.get('WH', 0.0):.1%}")
            right.metric(copy["lp_as"], f"{lp.get('AS', 0.0):.1%}")
            assignment = pd.DataFrame(
                [
                    {"run_id": run_id, copy["policy"]: policy}
                    for run_id, policy in lp.get("assignment", {}).items()
                ]
            )
            if not assignment.empty:
                counts = (
                    assignment[copy["policy"]]
                    .value_counts()
                    .rename_axis(copy["policy"])
                    .reset_index(name=copy["scenarios"])
                )
                st.dataframe(counts, use_container_width=True, hide_index=True)
                with st.expander(copy["assignment"]):
                    st.dataframe(assignment, use_container_width=True, hide_index=True)
        else:
            st.info(copy["no_summary"])

        st.subheader(copy["costs"])
        st.caption(copy["cost_caption"])
        st.dataframe(
            pd.DataFrame(
                [
                    {copy["signal"]: copy["channels"].get(name, name), "Cost": value}
                    for name, value in env.costs["assumed"].items()
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

    with tabs[3]:
        st.subheader(copy["titles"][3])
        if not records:
            st.info(copy["no_runs"])
        else:
            frame = pd.DataFrame(
                [
                    {
                        copy["policy"]: kind,
                        "WH": weighted_harm_prevented(records, kind),
                        "AS": attack_success_probability(records, kind),
                        "Residual harm": policy_residual_harm(records, kind),
                    }
                    for kind in POLICY_KINDS
                ]
            )
            st.dataframe(frame, use_container_width=True, hide_index=True)
            st.bar_chart(frame.set_index(copy["policy"])[["WH", "AS"]])

    with tabs[4]:
        st.subheader(copy["titles"][4])
        gemini = _gemini_results()
        if gemini.empty:
            st.info(copy["no_gemini"])
            st.caption(copy["gemini_hint"])
        else:
            grouped = (
                gemini.groupby("monitor_channel", as_index=False)
                .agg(
                    evaluations=("scenario_id", "count"),
                    expected_match=("matches_expected", "mean"),
                    mean_risk=("risk_score", "mean"),
                    mean_latency=("latency_ms", "mean"),
                )
                .rename(
                    columns={
                        "monitor_channel": copy["signal"],
                        "evaluations": copy["evaluations"],
                        "expected_match": copy["expected_match"],
                        "mean_risk": copy["mean_risk"],
                        "mean_latency": copy["mean_latency"],
                    }
                )
            )
            st.dataframe(grouped, use_container_width=True, hide_index=True)
            with st.expander(copy["details"]):
                st.dataframe(gemini, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
