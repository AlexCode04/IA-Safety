"""SQLite execution store: scenario / trajectory / step / policy / activation tables."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from src.schema import POLICY_KINDS, RunRecord

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS scenario (
    id TEXT PRIMARY KEY,
    family TEXT NOT NULL,
    condition TEXT NOT NULL,
    variant TEXT NOT NULL,
    template_id TEXT NOT NULL,
    authorized_task TEXT NOT NULL,
    critical_tool TEXT NOT NULL,
    severity REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS trajectory (
    run_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    scenario_id TEXT NOT NULL REFERENCES scenario(id),
    schema_version TEXT NOT NULL,
    mock_mode INTEGER NOT NULL,
    config_hash TEXT NOT NULL,
    agent_model TEXT NOT NULL,
    monitor_model TEXT NOT NULL,
    nla_model TEXT NOT NULL,
    decision_marker_found INTEGER NOT NULL,
    proposed_tool TEXT NOT NULL,
    committed INTEGER NOT NULL,
    primary_label INTEGER NOT NULL,
    harm_committed INTEGER NOT NULL,
    latency_ms REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS step (
    run_id TEXT NOT NULL REFERENCES trajectory(run_id),
    view TEXT NOT NULL,
    enabled INTEGER NOT NULL,
    alert INTEGER NOT NULL,
    alert_before_harm INTEGER NOT NULL,
    score REAL NOT NULL,
    assumed_cost REAL NOT NULL,
    measured_latency_ms REAL NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    api_calls INTEGER NOT NULL,
    gpu_seconds REAL NOT NULL,
    PRIMARY KEY (run_id, view)
);

CREATE TABLE IF NOT EXISTS policy (
    run_id TEXT NOT NULL REFERENCES trajectory(run_id),
    kind TEXT NOT NULL,
    selected_views TEXT NOT NULL,
    decision TEXT NOT NULL,
    reason TEXT NOT NULL,
    assumed_cost REAL NOT NULL,
    alert_before_harm INTEGER NOT NULL,
    intervention_successful INTEGER NOT NULL,
    containment_successful INTEGER NOT NULL,
    residual_harm REAL NOT NULL,
    prevented_harm REAL NOT NULL,
    PRIMARY KEY (run_id, kind)
);

CREATE TABLE IF NOT EXISTS activation (
    run_id TEXT NOT NULL REFERENCES trajectory(run_id),
    layer INTEGER NOT NULL,
    position_name TEXT NOT NULL,
    captured INTEGER NOT NULL,
    vector_dim INTEGER NOT NULL,
    vector_blob BLOB,
    PRIMARY KEY (run_id)
);
"""


def export_runs_to_sqlite(records: list[RunRecord], db_path: Path) -> int:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        for record in records:
            insert_record(conn, record)
        conn.commit()
    finally:
        conn.close()
    return len(records)


def insert_record(conn: sqlite3.Connection, record: RunRecord) -> None:
    t = record.trajectory
    conn.execute(
        """
        INSERT OR REPLACE INTO scenario
        (id, family, condition, variant, template_id, authorized_task, critical_tool, severity)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            t.id,
            t.family,
            t.condition,
            t.variant,
            t.template_id,
            t.authorized_task,
            t.critical_tool,
            t.severity,
        ),
    )
    e = record.experiment
    a = record.agent
    conn.execute(
        """
        INSERT OR REPLACE INTO trajectory
        (run_id, timestamp, scenario_id, schema_version, mock_mode, config_hash,
         agent_model, monitor_model, nla_model, decision_marker_found, proposed_tool,
         committed, primary_label, harm_committed, latency_ms)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record.run_id,
            record.timestamp,
            t.id,
            record.schema_version,
            int(e.mock_mode),
            e.config_hash,
            e.agent_model,
            e.monitor_model,
            e.nla_model,
            int(a.decision_marker_found),
            a.proposed_tool,
            int(record.tool_call.committed),
            int(record.labels.primary_label),
            int(record.labels.harm_committed),
            a.latency_ms,
        ),
    )
    for channel in (record.channels.observable, record.channels.cot, record.channels.probe, record.channels.nla):
        conn.execute(
            """
            INSERT OR REPLACE INTO step
            (run_id, view, enabled, alert, alert_before_harm, score, assumed_cost,
             measured_latency_ms, input_tokens, output_tokens, api_calls, gpu_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.run_id,
                channel.view,
                int(channel.enabled),
                int(channel.alert),
                int(channel.alert_before_harm),
                channel.score,
                channel.assumed_cost,
                channel.measured_latency_ms,
                channel.input_tokens,
                channel.output_tokens,
                channel.api_calls,
                channel.gpu_seconds,
            ),
        )
    for kind in POLICY_KINDS:
        policy = getattr(record.policies, kind)
        conn.execute(
            """
            INSERT OR REPLACE INTO policy
            (run_id, kind, selected_views, decision, reason, assumed_cost, alert_before_harm,
             intervention_successful, containment_successful, residual_harm, prevented_harm)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.run_id,
                policy.kind,
                ",".join(policy.selected_views),
                policy.decision,
                policy.reason,
                policy.assumed_cost,
                int(policy.alert_before_harm),
                int(policy.intervention_successful),
                int(policy.containment_successful),
                policy.residual_harm,
                policy.prevented_harm,
            ),
        )
    activation = record.activation
    conn.execute(
        """
        INSERT OR REPLACE INTO activation
        (run_id, layer, position_name, captured, vector_dim, vector_blob)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            record.run_id,
            activation.layer,
            activation.position_name,
            int(activation.captured),
            activation.vector_dim,
            None,
        ),
    )