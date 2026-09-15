# -*- coding: utf-8 -*-
"""Professional Budget-NLA dashboard backed by the canonical result schema."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parents[1]
WEB = Path(__file__).resolve().parent / "web"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.environment import ExperimentEnvironment, resolve_path
from src.metrics import load_run_records


def load_summary(runs_path: Path) -> dict:
    path = runs_path.with_name("summary.json")
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def build_payload(records, costs: dict, summary: dict | None = None) -> dict:
    summary = summary or {}
    assignments = summary.get("lp", {}).get("assignment", {})
    effective = summary.get("case_alerts", {})
    cases = []
    for record in records:
        scenario_id = record.trajectory.id
        alerts = {
            view: bool(getattr(record.channels, view).alert_before_harm)
            for view in ("observable", "cot", "probe", "nla")
        }
        alerts.update(effective.get(scenario_id, {}))

        baseline = record.policies.baseline
        adaptive_kind = assignments.get(record.run_id, "baseline")
        if adaptive_kind not in record.policies.model_fields:
            adaptive_kind = "baseline"
        adaptive = getattr(record.policies, adaptive_kind)
        primary = record.labels.primary_label == 1
        adaptive_stops = any(
            alerts.get(view, False) for view in adaptive.selected_views
        )
        adaptive_residual = (
            0.0 if primary and adaptive_stops
            else record.trajectory.severity if primary
            else 0.0
        )
        cases.append(
            {
                "id": scenario_id,
                "family": record.trajectory.family,
                "condition": record.trajectory.condition,
                "variant": record.trajectory.variant,
                "primary_label": int(primary),
                "severity": record.trajectory.severity,
                "alerts": alerts,
                "uniform_decision": baseline.decision,
                "adaptive_decision": "block" if adaptive_stops else "allow",
                "adaptive_policy": adaptive_kind,
                "uniform_residual_harm": baseline.residual_harm,
                "adaptive_residual_harm": adaptive_residual,
                "uniform_cost": baseline.assumed_cost,
                "adaptive_cost": adaptive.assumed_cost,
            }
        )
    provenance = summary.get("provenance") or {
        "source": "unaggregated_run",
        "mock_mode": bool(records and records[0].experiment.mock_mode),
        "submission_evidence": False,
    }
    return {"cases": cases, "costs": costs, "provenance": provenance}


def render_html(payload: dict) -> str:
    html = (WEB / "index.html").read_text(encoding="utf-8")
    css = (WEB / "styles.css").read_text(encoding="utf-8")
    js = (WEB / "app.js").read_text(encoding="utf-8")
    return (
        html.replace("/*__CSS__*/", css)
        .replace("/*__JS__*/", js)
        .replace("__DATA__", json.dumps(payload, ensure_ascii=False))
    )


def main() -> None:
    st.set_page_config(
        page_title="Budget-NLA",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(
        """
        <style>
          html, body, .stApp, [data-testid="stAppViewContainer"],
          [data-testid="stAppScrollToBottomContainer"], .stMain,
          .stMainBlockContainer, .block-container, [data-testid="stVerticalBlock"],
          [data-testid="stElementContainer"] {
            height: 100vh !important;
            max-height: 100vh !important;
            min-height: 100vh !important;
            padding: 0 !important;
            margin: 0 !important;
            overflow: hidden !important;
          }
          header, footer, [data-testid="stHeader"], [data-testid="stToolbar"],
          [data-testid="stDecoration"], [data-testid="stStatusWidget"], #MainMenu {
            display: none !important;
          }
          iframe[data-testid="stIFrame"] {
            position: fixed !important;
            inset: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            border: 0 !important;
            background: #F8FAFC;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )
    env = ExperimentEnvironment(ROOT / "configs" / "experiment.yaml")
    runs_path = resolve_path(env.config["paths"]["runs"])
    records = load_run_records(runs_path)
    if not records:
        st.warning(
            "Aún no hay resultados. Ejecuta: "
            "python scripts/run_experiment.py --reset-output && "
            "python scripts/build_results.py"
        )
        return
    payload = build_payload(records, env.costs["assumed"], load_summary(runs_path))
    components.html(render_html(payload), height=900, scrolling=False)


if __name__ == "__main__":
    main()
