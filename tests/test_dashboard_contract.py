"""Regression checks for the bilingual operator dashboard contract."""

from pathlib import Path

from app.dashboard import build_payload, render_html
from tests.test_schema import build_sample_record


ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_copy_has_complete_provenance_and_table_headers() -> None:
    source = (ROOT / "app" / "web" / "app.js").read_text(encoding="utf-8")
    assert source.count("syntheticNotice:") == 2
    assert source.count("realNotice:") == 2
    assert '"Adaptativa", "Ruta"' in source
    assert '"Adaptive", "Route"' in source


def test_rendered_dashboard_contains_mock_provenance_and_route() -> None:
    payload = build_payload(
        [build_sample_record()],
        {"observable": 1.0, "cot": 1.2, "probe": 0.25, "nla": 4.0},
        {
            "provenance": {
                "source": "deterministic_mock",
                "mock_mode": True,
                "submission_evidence": False,
            }
        },
    )
    html = render_html(payload)
    assert '"mock_mode": true' in html
    assert '"adaptive_policy": "baseline"' in html
    assert "__DATA__" not in html
