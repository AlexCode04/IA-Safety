# Task 006 — Contrato del gate con Gemini (decide_verdict)

**Fecha:** 2026-09-13 · **Autor:** opencode/Juan · **Rama:** feature/nla-probe · **Estado:** cerrada (código) / merge externo pendiente

## Cumple el checklist
- [ ] C2.4 — no aplica (es señal CoT de lealtad, otra rama).
- [x] C3.1 — base de interoperación: el gate de Jhoan consume el contrato de señales de esta rama.

## Objetivo
Que `decide_verdict` exista en esta rama, idéntico al de Jhoan (`origin/feature/gemini-monitor-codex`),
para que el merge sea limpio y el contrato de `monitor_cases.json` alimente el monitor de Gemini.

## Decisiones y por qué
- Copiar el método **1:1** desde la rama de Jhoan en vez de reimplementarlo distinto — un merge idéntico
  no genera conflicto funcional; se descartó escribir una variante propia (rompería el contrato de Jhoan).
- El método acepta dict o cualquier objeto con `model_dump()` (pydantic) — contracto flexible.
- Fail-safe: `block_on_alert` + `actionable_alert` bloquean incluso con score bajo; score ≥
  `escalate_threshold` escala aunque el modelo escriba ALLOW (inconsistencia contenida).

## Pasos ejecutados
1. `src/policy_gate.py`: añadido `decide_verdict`, verificado `diff` = 0 contra
   `git show origin/feature/gemini-monitor-codex:src/policy_gate.py`.
2. `tests/test_policy_gate.py`: 4 tests (block actionable, escalar high-score con ALLOW, allow limpio,
   objeto tipo pydantic) + 1 de `as_views` (filtra vistas desconocidas).

## Verificación
- `diff src/policy_gate.py vs origin/feature/gemini-monitor-codex:src/policy_gate.py` → "IDÉNTICO a Jhoan".
- `python -m pytest -q` → 30/30 (5 tests nuevos).

## Límites y pendientes
- Requiere el merge de `feature/gemini-monitor-codex` y `GEMINI_API_KEY` para la corrida real del monitor.
- `smoke_test_monitor.py` de Jhoan apunta a `tests/fixtures/monitor_cases.json`; cuando se apunte a nuestro
  `results/monitor_cases.json`, el contrato ya viene con `probe_score` poblado desde Task 005.