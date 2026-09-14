# -*- coding: utf-8 -*-
"""Professional Budget-NLA dashboard."""

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


def build_payload(records, costs: dict) -> dict:
    cases = []
    for record in records:
        cases.append(
            {
                "id": record.trajectory.id,
                "family": record.trajectory.family,
                "condition": record.trajectory.condition,
                "variant": record.trajectory.variant,
                "primary_label": record.labels.primary_label,
                "severity": record.trajectory.severity,
                "alerts": {
                    "observable": record.channels.observable.alert,
                    "cot": record.channels.cot.alert,
                    "probe": record.channels.probe.alert,
                    "nla": record.channels.nla.alert,
                },
                "uniform_decision": record.policies.uniform.decision,
                "adaptive_decision": record.policies.adaptive.decision,
                "uniform_residual_harm": record.policies.uniform.residual_harm,
                "adaptive_residual_harm": record.policies.adaptive.residual_harm,
                "uniform_cost": record.policies.uniform.assumed_cost,
                "adaptive_cost": record.policies.adaptive.assumed_cost,
            }
        )
    return {"cases": cases, "costs": costs}


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
    st.set_page_config(page_title="Budget-NLA", layout="wide", initial_sidebar_state="collapsed")
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
    records = load_run_records(resolve_path(env.config["paths"]["runs"]))
    if not records:
        st.warning("Aun no hay resultados. Ejecuta: python scripts/run_experiment.py")
        return
    html = render_html(build_payload(records, env.costs["assumed"]))
    (WEB / "preview.html").write_text(html, encoding="utf-8")
    components.html(html, height=900, scrolling=False)


if __name__ == "__main__":
    main()
