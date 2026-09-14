"""Evaluate an exported monitor contract with isolated Gemini channels.

The runner is resumable: completed scenario/channel/model tuples are skipped
unless --overwrite is passed. This prevents losing paid API work after a rate
limit or transient failure.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pydantic import TypeAdapter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.gemini_monitor import GeminiMonitor, MonitorCase, MonitorChannel
from src.policy_gate import PolicyGate

CHANNELS: tuple[MonitorChannel, ...] = ("observable", "cot", "nla", "hybrid")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="results/monitor_cases.json")
    parser.add_argument("--output", default="results/gemini_verdicts.jsonl")
    parser.add_argument("--model", default=None)
    parser.add_argument("--channels", nargs="+", choices=CHANNELS, default=list(CHANNELS))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def load_cases(path: Path) -> list[MonitorCase]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return TypeAdapter(list[MonitorCase]).validate_python(payload)


def evaluation_kwargs(case: MonitorCase, channel: MonitorChannel) -> dict:
    if channel == "hybrid" and case.probe_score is None:
        raise ValueError(
            f"{case.scenario_id} has no probe_score; run scripts/train_probe.py first"
        )
    return {
        "policy": case.policy,
        "observable_transcript": case.observable_transcript,
        "channel": channel,
        "cot": case.cot if channel in {"cot", "hybrid"} else None,
        "nla_text": case.nla_text if channel in {"nla", "hybrid"} else None,
        "probe_score": case.probe_score if channel == "hybrid" else None,
    }


def completed_keys(path: Path) -> set[tuple[str, str, str]]:
    if not path.exists():
        return set()
    keys: set[tuple[str, str, str]] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        keys.add(
            (
                record["scenario_id"],
                record["monitor_channel"],
                record["monitor_model"],
            )
        )
    return keys


def main() -> int:
    load_dotenv(ROOT / ".env")
    args = parse_args()
    input_path = ROOT / args.input
    output_path = ROOT / args.output
    if not input_path.exists():
        print(
            f"Missing {input_path}. Run scripts/export_monitor_cases.py or "
            "scripts/smoke_nla.py first.",
            file=sys.stderr,
        )
        return 1

    cases = load_cases(input_path)
    if args.limit is not None:
        cases = cases[: args.limit]
    model = args.model or os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    if args.overwrite and output_path.exists():
        output_path.unlink()
    done = completed_keys(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    monitor = GeminiMonitor(model=model)
    gate = PolicyGate()
    written = 0

    with output_path.open("a", encoding="utf-8") as handle:
        for case in cases:
            for raw_channel in args.channels:
                channel: MonitorChannel = raw_channel
                key = (case.scenario_id, channel, model)
                if key in done:
                    continue
                result = monitor.evaluate(**evaluation_kwargs(case, channel))
                decision, reason = gate.decide_verdict(result.verdict)
                record = {
                    "scenario_id": case.scenario_id,
                    "monitor_channel": channel,
                    "monitor_model": result.model_used,
                    "expected_action": case.expected_action,
                    **result.verdict.model_dump(),
                    "gate_decision": decision,
                    "gate_reason": reason,
                    "matches_expected": decision.upper() == case.expected_action,
                    "latency_ms": result.latency_ms,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                }
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                handle.flush()
                written += 1

    print(f"Wrote {written} new Gemini evaluations to {output_path}")
    print(f"Total completed keys: {len(completed_keys(output_path))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
