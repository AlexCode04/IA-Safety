# -*- coding: utf-8 -*-
"""Budget-NLA dashboard with Spanish/English language toggle."""

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

TEXT = {
    "es": {
        "page_title": "Budget-NLA",
        "language": "Idioma",
        "caption": (
            "Monitoreo adaptativo para detener sabotaje antes de que cause da\u00f1o. "
            "Los costos mostrados son valores de referencia, no mediciones reales."
        ),
        "empty": "A\u00fan no hay resultados. Ejecuta primero: python scripts/run_experiment.py",
        "phr": "Sabotajes detenidos a tiempo",
        "bdr": "Falsas alarmas",
        "eph": "Da\u00f1o evitado",
        "uniform_harm": "Da\u00f1o que queda con vigilancia fija",
        "adaptive_harm": "Da\u00f1o que queda con vigilancia adaptativa",
        "costs_title": "Costo de cada tipo de vigilancia",
        "costs_caption": "Valores de referencia para el dashboard, no costos medidos.",
        "cost_type": "Tipo de vigilancia",
        "cost_value": "Costo de referencia",
        "table_title": "Detalle de los 24 casos",
        "yes": "S\u00ed",
        "no": "No",
        "channels": {
            "observable": "Acciones visibles",
            "cot": "Razonamiento",
            "probe": "Sonda interna",
            "nla": "Lectura interna NLA",
        },
        "costs": {
            "observable": "Vigilar acciones visibles",
            "cot": "Leer el razonamiento",
            "probe": "Sonda interna",
            "nla": "Lectura NLA + Gemini",
            "hybrid": "Revisi\u00f3n h\u00edbrida completa",
            "human_review": "Revisi\u00f3n humana simulada",
        },
        "families": {
            "external_report": "Publicar informe",
            "corporate_email": "Correo corporativo",
            "access_list": "Lista de acceso",
        },
        "conditions": {
            "BENIGN": "Tarea inocua",
            "ATTACK_REJECTED": "Ataque rechazado",
            "VISIBLE_SABOTAGE": "Sabotaje visible",
            "STEALTH_SABOTAGE": "Sabotaje oculto",
        },
        "decisions": {
            "allow": "Permitir",
            "block": "Bloquear",
            "escalate": "Revisar",
        },
        "headers": {
            "run_id": "ID de corrida",
            "timestamp": "Fecha",
            "trajectory_id": "ID del caso",
            "family": "Tipo de tarea",
            "condition": "Situaci\u00f3n",
            "variant": "Variante",
            "template_id": "Plantilla",
            "primary_label": "Intento de sabotaje",
            "harm_committed": "Habr\u00eda causado da\u00f1o",
            "observable_alert": "Alerta por acciones visibles",
            "cot_alert": "Alerta por razonamiento",
            "probe_alert": "Alerta de la sonda",
            "nla_alert": "Alerta NLA",
            "uniform_decision": "Decisi\u00f3n con vigilancia fija",
            "adaptive_decision": "Decisi\u00f3n con vigilancia adaptativa",
            "uniform_residual_harm": "Da\u00f1o que queda (fija)",
            "adaptive_residual_harm": "Da\u00f1o que queda (adaptativa)",
            "uniform_cost": "Costo de la vigilancia fija",
            "adaptive_cost": "Costo de la vigilancia adaptativa",
        },
    },
    "en": {
        "page_title": "Budget-NLA",
        "language": "Language",
        "caption": (
            "Adaptive monitoring to stop sabotage before it causes harm. "
            "Shown costs are reference values, not measured costs."
        ),
        "empty": "No results yet. Run this first: python scripts/run_experiment.py",
        "phr": "Sabotage stopped in time",
        "bdr": "False alarms",
        "eph": "Harm prevented",
        "uniform_harm": "Remaining harm with uniform monitoring",
        "adaptive_harm": "Remaining harm with adaptive monitoring",
        "costs_title": "Cost of each monitoring type",
        "costs_caption": "Dashboard reference values, not measured costs.",
        "cost_type": "Monitoring type",
        "cost_value": "Reference cost",
        "table_title": "Detail of the 24 cases",
        "yes": "Yes",
        "no": "No",
        "channels": {
            "observable": "Visible actions",
            "cot": "Visible reasoning",
            "probe": "Internal probe",
            "nla": "NLA internal readout",
        },
        "costs": {
            "observable": "Watch visible actions",
            "cot": "Read the reasoning",
            "probe": "Internal probe",
            "nla": "NLA + Gemini readout",
            "hybrid": "Full hybrid review",
            "human_review": "Simulated human review",
        },
        "families": {
            "external_report": "Publish report",
            "corporate_email": "Corporate email",
            "access_list": "Access list",
        },
        "conditions": {
            "BENIGN": "Benign task",
            "ATTACK_REJECTED": "Attack rejected",
            "VISIBLE_SABOTAGE": "Visible sabotage",
            "STEALTH_SABOTAGE": "Hidden sabotage",
        },
        "decisions": {
            "allow": "Allow",
            "block": "Block",
            "escalate": "Review",
        },
        "headers": {
            "run_id": "Run ID",
            "timestamp": "Date",
            "trajectory_id": "Case ID",
            "family": "Task type",
            "condition": "Situation",
            "variant": "Variant",
            "template_id": "Template",
            "primary_label": "Sabotage attempt",
            "harm_committed": "Would have caused harm",
            "observable_alert": "Visible-actions alert",
            "cot_alert": "Reasoning alert",
            "probe_alert": "Probe alert",
            "nla_alert": "NLA alert",
            "uniform_decision": "Uniform-monitoring decision",
            "adaptive_decision": "Adaptive-monitoring decision",
            "uniform_residual_harm": "Remaining harm (uniform)",
            "adaptive_residual_harm": "Remaining harm (adaptive)",
            "uniform_cost": "Uniform monitoring cost",
            "adaptive_cost": "Adaptive monitoring cost",
        },
    },
}


def format_yes_no(value, copy: dict) -> str:
    if value in (True, "True", 1, "1"):
        return copy["yes"]
    if value in (False, "False", 0, "0"):
        return copy["no"]
    return str(value)


def localize_table(frame: pd.DataFrame, copy: dict) -> pd.DataFrame:
    display = frame.copy()
    if "family" in display.columns:
        display["family"] = display["family"].map(copy["families"]).fillna(display["family"])
    if "condition" in display.columns:
        display["condition"] = display["condition"].map(copy["conditions"]).fillna(display["condition"])
    if "primary_label" in display.columns:
        display["primary_label"] = display["primary_label"].map(lambda value: format_yes_no(value, copy))
    for column in ("harm_committed", "observable_alert", "cot_alert", "probe_alert", "nla_alert"):
        if column in display.columns:
            display[column] = display[column].map(lambda value: format_yes_no(value, copy))
    for column in ("uniform_decision", "adaptive_decision"):
        if column in display.columns:
            display[column] = display[column].map(copy["decisions"]).fillna(display[column])
    return display.rename(columns=copy["headers"])


def selected_language() -> str:
    query_language = st.query_params.get("lang", "es")
    if query_language not in TEXT:
        query_language = "es"
    language = st.radio(
        TEXT[query_language]["language"],
        options=["es", "en"],
        format_func=lambda code: "Espa\u00f1ol" if code == "es" else "English",
        index=0 if query_language == "es" else 1,
        horizontal=True,
        key="language_toggle",
    )
    if language != query_language:
        st.query_params["lang"] = language
    return language


def main() -> None:
    st.set_page_config(page_title="Budget-NLA", layout="wide")
    language = selected_language()
    copy = TEXT[language]
    st.title(copy["page_title"])
    st.caption(copy["caption"])
    env = ExperimentEnvironment(ROOT / "configs" / "experiment.yaml")
    runs_path = resolve_path(env.config["paths"]["runs"])
    records = load_run_records(runs_path)
    if not records:
        st.warning(copy["empty"])
        return
    views = ["observable", "cot", "probe", "nla"]
    columns = st.columns(4)
    for column, view in zip(columns, views):
        column.subheader(copy["channels"][view])
        column.metric(copy["phr"], f"{pre_harm_recall(records, view):.0%}")
        column.metric(copy["bdr"], f"{benign_disruption_rate(records, view):.0%}")
        column.metric(copy["eph"], f"{expected_prevented_harm(records, view):.1f}")
    left, right = st.columns(2)
    left.metric(copy["uniform_harm"], f"{policy_residual_harm(records, 'uniform'):.1f}")
    right.metric(copy["adaptive_harm"], f"{policy_residual_harm(records, 'adaptive'):.1f}")
    st.subheader(copy["costs_title"])
    st.caption(copy["costs_caption"])
    cost_rows = [
        {copy["cost_type"]: copy["costs"].get(name, name), copy["cost_value"]: value}
        for name, value in env.costs["assumed"].items()
    ]
    st.dataframe(pd.DataFrame(cost_rows), use_container_width=True, hide_index=True)
    metrics_path = resolve_path(env.config["paths"]["metrics"])
    if metrics_path.exists():
        st.subheader(copy["table_title"])
        st.dataframe(localize_table(pd.read_csv(metrics_path), copy), use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
