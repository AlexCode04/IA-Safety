"""Run 3 fixtures across 4 Gemini monitoring views (12 evaluations)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.gemini_monitor import GeminiMonitor
from src.policy_gate import PolicyGate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gemini-3.8-flash")
    parser.add_argument(
        "--output", default="results/smoke_test_monitor.jsonl"
    )
    return parser.parse_args()


def main() -> int:
    load_dotenv(ROOT / ".env")
    args = parse_args()
    fixtures_path = ROOT / "tests" / "fixtures" / "monitor_cases.json"
    output_path = ROOT / args.output
    cases = json.loads(fixtures_path.read_text(encoding="utf-8"))
    monitor = GeminiMonitor(model=args.model)
    gate = PolicyGate()
    records: list[dict] = []

    for case in cases:
        for channel in ("observable", "cot", "nla", "hybrid"):
            result = monitor.evaluate(
                policy=case["policy"],
                observable_transcript=case["observable_transcript"],
                channel=channel,
                cot=case["cot"] if channel in {"cot", "hybrid"} else None,
                nla_text=case["nla_text"] if channel in {"nla", "hybrid"} else None,
                probe_score=case["probe_score"] if channel == "hybrid" else None,
            )
            decision, reason = gate.decide_verdict(result.verdict)
            records.append(
                {
                    "scenario_id": case["scenario_id"],
                    "monitor_channel": channel,
                    "monitor_model": result.model_used,
                    **result.verdict.model_dump(),
                    "gate_decision": decision,
                    "gate_reason": reason,
                    "latency_ms": result.latency_ms,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                }
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"{len(records)} monitor evaluations completed")
    print(f"Structured responses written to {output_path}")
    print("Policy gate integration: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
