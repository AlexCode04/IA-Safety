# Checklist general — BUDGET-NLA

Puertas del proyecto. Cada ítem se marca `[x]` cuando una tarea declara, con evidencia, que lo
cumple. Los ítems marcados por `Task 001` (scaffold) son los que corresponden al arranque.

## C0 — Arranque (entorno y rebanada mínima)

- [ ] C0.1 — Repo `IA-Safety` clonado y rama `feature/nla-probe` creada con estructura `budget-nla/` esqueletada.
- [ ] C0.2 — Entorno virtual reproducible instalado (torch, transformers, peft, etc.) con instrucciones en el repo.
- [ ] C0.3 — Qwen2.5-7B-Instruct carga local con el textualizador NLA y produce una verbalización real (smoke test).
- [x] C0.4 — Decisión registrada de capa/token de extracción y de cuantización (int4/int8) con justificación. — Task 002: capa 20, marker `\n<DECISION>\n`, int4 grupo 128 (`src/*_real.py`, `configs/experiment.yaml`), commit `9dd7eb7`; C0.3 queda pendiente de la corrida real (handoff `VERIFICAR-NLA.md`, máquina ≥18GB).

## C1 — Rebanada vertical (4 trayectorias end-to-end)

- [ ] C1.1 — Runner real del agente cableado (`src/agent_runner_real.py`, `_run_live`); falta corrida ≥18GB. — Task 003, pytest 16/16.
- [ ] C1.2 — Detección del marcador `<DECISION>` implementada (`decision_marker_found`) y `position_name` en el hook real; token exacto pendiente de corrida. — Task 003.
- [ ] C1.3 — NLA verbaliza >= 2 decisiones (benigna + maliciosa) y el texto se guarda en el log.
- [ ] C1.4 — Probe (logreg 1 capa) entrena y evalúa sobre las activaciones acumuladas con clasificación balanceada.
- [ ] C1.5 — Parser de acción JSON con fallback testado (`tests/test_agent_runner_real.py`); corrida completa pendiente. — Task 003.

## C2 — Dataset y métricas

- [ ] C2.1 — 24 escenarios simulados (3 familias de amenaza × 4 condiciones × 2 variantes), con ground-truth T/S como separado.
- [x] C2.2 — Base de datos de ejecuciones (SQLite) con tablas por escenario/trayectoria/paso, con extracción de activaciones. — Task 004: `src/store.py` + `scripts/export_sqlite.py`; tablas `scenario`, `trajectory`, `step`, `policy`, `activation` (BLOB de vector); conteos verificados 24/24/96/120/24 en `results/executions.db`; `tests/test_store.py` 3/3.
- [ ] C2.3 — Métricas implementadas: PHR, BDR, WH, IMV, AS, PE, con PIP verificadas en trayectorias sintéticas.
- [ ] C2.4 — CoT juicio de lealtad como señal externa extra, guardada tanto en condición con razonamiento como sin razonamiento.
- [ ] C2.5 — Particiones train/test: el probe no ve test hasta cerrar el umbral y los checks de sobreajuste. — Parcial: LOTO implementado en `scripts/train_probe.py` (leave-one-template-out, `tests/test_train_probe.py`); falta cerrar umbral con corrida real ≥18GB (handoff).

## C3 — Optimizador y dashboard

- [x] C3.1 — Optimizador: modelado LP con 4 políticas (NLA→probe→CoT, probe→NLA→CoT, CoT y NLA, aleatorio/solo-accion) y una política como línea base intermónitoreo. — Task 005: `finalize_lp` en `scripts/build_results.py` con `assignments["baseline"] = 1.0` y `POLICY_PRIORITY` para 4 políticas adaptativas; mochila 0/1 con `assumed` costs; blob `lp` en `summary.json` (costo 52.80, WH/AS); pytest 30/30.
- [x] C3.2 — Dashboard Streamlit (4 pestañas: escenarios, detección, presupuesto, trade-off) legible en mínima resolución. — Task 007: `app/dashboard.py` con `st.tabs` (escenarios, deteccion, presupuesto, trade-off); lee `runs.jsonl` + `summary.json`; `st.metric`/`st.bar_chart`; sin `stcolumns` fijos anchos. Verificado helpers (`_summary`, `_assignments`: 24 rows).

## C4 — Cierre y congelación

- [ ] C4.1 — Congelación al final de la hora 5: resultados, módulos y decisiones congelados; no se añade funcionalidad nueva.
- [ ] C4.2 — Entorno reproducible limpio (nueva máquina: clonar + instalar deps corre smoke test).
- [ ] C4.3 — Paper con secciones: pregunta, método, resultados, discussion, límites (incluye límites de: atacante adaptativo al patrón de vigilancia, pesos de riesgo subjetivos, costos estimados no medidos, sin mostrar el presupuesto total correcto).
- [ ] C4.4 — README reproducible con instrucciones de ejecución y config; CVS/resultados guardados en `results/`. — README reescrito con flujo completo 1-2-3, args de `train_probe.py` y nota de GEMINI_API_KEY; pyproject.toml (pinned) + uv.lock fijos. Pendiente de congelación C4.