# Task 004 — Base de datos SQLite de ejecuciones

**Fecha:** 2026-09-13 · **Autor:** opencode/Juan · **Rama:** feature/nla-probe · **Estado:** cerrada

## Cumple el checklist
- [x] C2.2 — `src/store.py` + `scripts/export_sqlite.py`; tablas `scenario`, `trajectory`, `step`, `policy`,
  `activation` (vector BLOB); conteos 24/24/96/120/24 verificados en `results/executions.db`; `tests/test_store.py` 3/3.

## Objetivo
Volcar `results/runs.jsonl` a una base SQLite consultable, con activaciones extraídas, para los
análisis del dashboard y las PIP.

## Decisiones y por qué
- SQLite nativo (`sqlite3`, sin ORM) — cero dependencias nuevas; se descartó DuckDB por no estar en pyproject.
- Esquema por escenario/trayectoria/paso, tabla `policy` aparte y `activation` con vector serializado
  (BLOB) — separar señales de política de los vectores evita re-leer todo el jsonl por consulta.
- El export es idempotente: recrea el archivo en `--reset-output`.

## Pasos ejecutados
1. `src/store.py`: `build_db`, `insert_run`, helpers de consulta.
2. `scripts/export_sqlite.py`: lee `runs.jsonl`, escribe `results/executions.db`.
3. `tests/test_store.py`: 3 tests.

## Verificación
- `python -m pytest -q` → todo verde (16/16 en ese momento).
- Consulta de conteos: 24 scenarios, 24 trajectories, 96 steps, 120 policies, 24 activations.

## Límites y pendientes
- El BLOB de activación guarda el vector serializado; no se normaliza NI ZEA de comprensión por consulta.