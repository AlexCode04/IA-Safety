import sqlite3

from src.schema import POLICY_KINDS
from src.store import export_runs_to_sqlite
from tests.test_schema import build_sample_record


def _one_record() -> list:
    return [build_sample_record()]


def test_export_creates_all_five_tables(tmp_path):
    db = tmp_path / "executions.db"
    export_runs_to_sqlite(_one_record(), db)
    conn = sqlite3.connect(db)
    names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    assert {"scenario", "trajectory", "step", "policy", "activation"} <= names


def test_export_persists_scenario_and_policy_rows(tmp_path):
    record = build_sample_record()
    db = tmp_path / "executions.db"
    export_runs_to_sqlite([record], db)
    conn = sqlite3.connect(db)
    scenario = conn.execute("SELECT id, family, severity FROM scenario").fetchone()
    assert scenario[0] == record.trajectory.id
    assert scenario[1] == record.trajectory.family
    policy_count = conn.execute("SELECT COUNT(*) FROM policy").fetchone()[0]
    step_count = conn.execute("SELECT COUNT(*) FROM step").fetchone()[0]
    conn.close()
    assert policy_count == len(POLICY_KINDS)
    assert step_count == 4


def test_export_replaces_and_keeps_activation_metadata(tmp_path):
    record = build_sample_record()
    db = tmp_path / "executions.db"
    export_runs_to_sqlite([record], db)
    export_runs_to_sqlite([record], db)
    conn = sqlite3.connect(db)
    n_traj = conn.execute("SELECT COUNT(*) FROM trajectory").fetchone()[0]
    n_act = conn.execute("SELECT COUNT(*) FROM activation").fetchone()[0]
    act = conn.execute("SELECT layer, position_name, captured, vector_dim FROM activation").fetchone()
    conn.close()
    assert n_traj == 1
    assert n_act == 1
    assert act == (20, "PRE_ACTION_DECISION_BOUNDARY", 1, 32)