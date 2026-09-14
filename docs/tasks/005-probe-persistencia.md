# Task 005 — Persistencia del probe (artefactos: .pkl, activaciones, scores)

**Fecha:** 2026-09-13 · **Autor:** opencode/Juan · **Rama:** feature/nla-probe · **Estado:** cerrada

## Cumple el checklist
- [x] C1.4 — parcial: probe logreg entrena y evalúa (LOTO) y ahora se persiste.
- [x] C2.5 — parcial: partición train/test por leave-one-template-out implementada; umbral pendiente de corrida real.

## Objetivo
Que el probe sea reutilizable: guardar/cargar pesos y umbral, y que `probe_score` quede poblado en
el contrato de señales sin depender del orden de ejecución.

## Decisiones y por qué
- `pickle` con `{"model", "threshold"}` en `LinearProbe.save/load` — formato más simple y probado para un
  objeto único; se descartó checkpoint de HF (sin necesidad de usar las rutas del hub).
- `scripts/train_probe.py` persiste 3 artefactos (`probe.pkl`, `probe_scores.json`, `probe_activations.npz`)
  y rellena `probe_score` en `results/monitor_cases.json` si ya existe — la correspondencia es por
  `scenario_id` (los ids de `data/scenarios.yaml` coinciden con los de `monitor_cases.json`).
- `smoke_nla.py` lee `results/probe_scores.json` y fusiona `probe_score` inline al generar el contrato —
  con esto el flujo funciona en cualquier orden (train_probe antes o después del smoke) y el contrato
  nunca queda con `null`.

## Pasos ejecutados
1. `src/probe.py`: `LinearProbe.save(path)` / `classmethod load(path)` con pickle (restaura `is_fitted`).
2. `scripts/train_probe.py`: escritura de `probe.pkl`, `probe_scores.json`, `probe_activations.npz` y
   relleno de `monitor_cases.json` (clave `scenario_id`).
3. `scripts/smoke_nla.py`: carga `probe_scores.json`, pone `probe_score` por id y
   reporta los ids faltantes como nota (no como fallo).
4. `tests/test_train_probe.py`: 2 tests mock (artefactos generados + relleno de monitor_cases).

## Verificación
- `python -m pytest -q` → 25/25.
- Corrida mock de `scripts/train_probe.py --config configs/experiment.yaml`: `LOTO AUROC 1.000`,
  `AUPRC 1.000`, `accuracy 1.000`; artefactos presentes en `results/`.

## Límites y pendientes
- Scores con sobreajuste trivial en mock (LOTO sobre datos sintéticos) — no son evidencia real.
- El umbral de decisión (`threshold`) real se cierra con la corrida ≥18GB.