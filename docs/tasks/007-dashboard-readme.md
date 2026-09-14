# Task 007 — Dashboard 4 pestañas + README reproducible

**Fecha:** 2026-09-13 · **Autor:** opencode/Juan · **Rama:** feature/nla-probe · **Estado:** cerrada (código) / corrida streamlit real pendiente

## Cumple el checklist
- [x] C3.2 — `app/dashboard.py` con `st.tabs` (escenarios, deteccion, presupuesto, trade-off); helpers
  verificados (`_summary`, `_assignments` → 24 rows usando `results/summary.json` real).
- [ ] C4.4 — README reescrito con flujo 1-2-3 y nota de Gemini; pyproject.toml pinned ya existe; congelación pendiente.

## Objetivo
Dashboard legible en resolución mínima, con 4 pestañas y que sobreviva a datos vacíos (sin runs).

## Decisiones y por qué
- `st.tabs` en vez de `st.columns` fijos — las columnas apiladas en 4 rompían la resolución mínima.
- `summary.json` se resuelve junto a `runs.jsonl` (misma carpeta `results/`) — se descartó hardcodear ruta.
- Pestañas con datos opcionales: si no hay runs, `st.warning` en vez de excepción.
- Métrica explícita de `incremental_nla_value` en la pestaña detección (IMV sobre CoT).

## Pasos ejecutados
1. `app/dashboard.py`: reescrito con 4 tabs, tablas de escenarios, métricas por señal, plan LP
   (costo/WH/AS + asignación por run) y trade-off con `st.bar_chart`.
2. `README.md`: flujo de un entry point 1-2-3 (`run_experiment` → `train_probe` → `export_sqlite`/`smoke`),
   descripción de los artefactos del probe y del contrato del gate.
3. `docs/00-checklist.md`: marcados C2.2, C3.1, C3.2; parciales C2.5 y C4.4.

## Verificación
- `python -m py_compile app/dashboard.py` → OK.
- Helper `_summary/_assignments` ejecutado sobre `results/summary.json` real → 24 asignaciones.
- `python -m pytest -q` → 30/30.
- La visualización real requiere `streamlit run app/dashboard.py` en máquina con resultados de la corrida.

## Límites y pendientes
- No se lanzó Streamlit en esta máquina (no hay `results/runs.jsonl` real de la corrida ≥18GB).
- `apply assignment` depende de la corrida real; en mock el plan LP es demostrativo.