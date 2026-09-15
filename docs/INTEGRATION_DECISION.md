# Integration decision: Qwen/NLA first, Gemini post-run

**Date:** 2026-09-14
**Status:** accepted for the hackathon integration branch

## Decision

The main experimental loop owns Qwen generation, the pre-action activation
hook, NLA verbalization, the LOTO probe, and policy records. Gemini does not run
inside that expensive loop. It consumes a frozen JSON contract afterward.

## Why

- Juan's real Qwen/NLA/probe work remains the source of sensor evidence.
- Jhoan's Gemini monitor remains the common reader for isolated evidence views.
- API retries cannot force a second Qwen/NLA activation run.
- The fixture in `tests/fixtures/monitor_cases.json` remains a unit/integration
  test; generated evidence lives in ignored `results/monitor_cases.json`.
- Every Gemini call is stateless and channel-isolated.

## Data flow

1. `scripts/run_experiment.py --real --reset-output`
   writes `results/runs.jsonl`.
2. `scripts/export_monitor_cases.py`
   validates and writes `results/monitor_cases.json`.
3. `scripts/run_gemini_monitor.py`
   writes resumable `results/gemini_verdicts.jsonl`.
4. `scripts/build_results.py` and `app/dashboard.py`
   display the experimental and budget results. The dashboard also displays
   Gemini accuracy, risk, and latency by channel when verdicts exist.

## Frozen hand-off contract

Each monitor case contains exactly:

- `scenario_id`
- `policy`
- `observable_transcript`
- `cot`
- `nla_text`
- `probe_score`
- `expected_action`

`src.gemini_monitor.MonitorCase` rejects extra or malformed fields.

## Ownership rule

- Changes to activation acquisition and NLA generation belong in the Qwen/NLA
  modules, not in the Gemini runner.
- Changes to Gemini prompting or structured verdicts belong in
  `src/gemini_monitor.py`.
- Changes to the contract require one coordinated commit plus tests on both
  producers and consumers.
