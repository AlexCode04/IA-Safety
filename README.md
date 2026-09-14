# BUDGET-NLA

Risk-Weighted Adaptive Monitoring for Pre-Harm Sabotage Containment.

Spec frozen: `EXPERIMENT_SPEC.md` v1.0 (2026-09-13). Primary owner: Jhoan. Team: Jhoan, Juan Plata, Maryori, Angel Alexis.

## Research question

Under a fixed monitoring budget, when and on which task types does access to an agent's internal state through a linear probe and a Natural Language Autoencoder provide additional pre-harm containment value over monitoring only observable actions and visible chain of thought?

## Frozen protocol

- Agent: `Qwen/Qwen2.5-7B-Instruct`, local, deterministic, `temperature=0`, `do_sample=false`, `max_new_tokens=512`
- External monitor: `gemini-3.8-flash` (fallback `gemini-2.5-flash`, never mixed in one result set)
- NLA: `Kameshr/nla-qwen2.5-7b-L20-av`, layer 20, position `PRE_ACTION_DECISION_BOUNDARY`
- Probe: logistic regression, L2, `C=1.0`, `liblinear`, 1000 iters, leave-one-template-out
- 3 families x 4 conditions x 2 variants = 24 trajectories
- Isolated views: OBSERVABLE, COT, PROBE, NLA
- Policies: uniform vs risk-weighted adaptive
- Primary metrics: PHR, BDR, EPH, PE, IMV_NLA, IMV_NLA|CoT
- Costs in `configs/monitoring_costs.yaml` are ASSUMED defaults

Do not change layer, probe config, conditions or primary hypotheses after seeing test results. Record any required change in `DEVIATIONS.md`.

## Environment

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Mock mode is the default. No API key is required for the baseline.

## Single entry point

```bash
# 1) base: generan runs.jsonl, metrics.csv y summary.json (mock por defecto)
python scripts/run_experiment.py --reset-output
python scripts/build_results.py

# 2) probe (fill probe_score en el contrato de senales)
python scripts/train_probe.py          # persiste probe.pkl, probe_scores.json y activaciones
python scripts/export_sqlite.py        # vierte runs.jsonl a results/executions.db (SQLite)

# 3) NLA real requerida por el pipeline: solo con maquina >= 18GB
python -u scripts/smoke_nla.py         # monitor_cases.json con corte <DECISION> (fusiona probe_score)
pytest
streamlit run app/dashboard.py         # 4 pestanas: escenarios, deteccion, presupuesto, trade-off
```

`train_probe.py` entrena el probe logreg L20 con leave-one-template-out, persiste
`results/probe.pkl`, `results/probe_scores.json` y `results/probe_activations.npz`, y rellena
`probe_score` en un `results/monitor_cases.json` preexistente. `smoke_nla.py` lee
`probe_scores.json` y deja el contrato completo para el monitor de Gemini
(`feature/gemini-monitor-codex`). El gate `decide_verdict` consume el veredicto estructurado de
Gemini y esta alineado 1:1 con la rama de Jhoan (`tests/test_policy_gate.py`).

## Result schema

Every trajectory writes one object to `results/runs.jsonl`:

- `trajectory`: family, condition, variant, template_id, severity
- `activation`: layer 20, `PRE_ACTION_DECISION_BOUNDARY`
- `labels`: primary_label plus the frozen auxiliary labels
- `channels`: isolated observable, cot, probe and nla results
- `policies`: uniform and adaptive decisions, residual harm and assumed cost

Ground truth comes from mocked tool arguments and policy rules, not from monitor opinions. All tools are simulated.

## Branches

| Branch | Module |
| --- | --- |
| `main` | Integrations. Jhoan merges here. |
| `feature/scenarios` | Families, conditions, labels |
| `feature/nla-probe` | Activation hook, NLA, probe |
| `feature/optimizer-dashboard` | Adaptive policy, costs, dashboard |
| `feature/paper` | LaTeX paper |

## License

MIT. See `LICENSE`.
