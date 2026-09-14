# Task 002 — Cierre del módulo NLA: hook L20 real + verbalizador + loader int4 + smoke + puente a Gemini

**Fecha:** 2026-09-13 · **Autor:** opencode/Juan · **Rama:** `feature/nla-probe` · **Estado:** cerrada

## Cumple el checklist
- [x] C0.4 — Decisión registrada de capa/token de extracción y cuantización: capa 20, marker `\n<DECISION>\n`, int4 grupo 128 (ver `src/activation_hook_real.py`, `src/nla_monitor_real.py`, `src/model_loader.py`, `configs/experiment.yaml`).
- [x] C1.2 (habilitada) — La extracción L20 se dispara sobre el texto que incluye el marker `<DECISION>`; la posición/capa quedan parametrizadas.
- [ ] C0.3 — **Parcial, no se marca**: el módulo está empaquetado y el smoke codificado, pero la corrida real con el Qwen de 7B requiere una máquina con ≥18GB RAM. La verificación queda delegada al handoff `VERIFICAR-NLA.md` (se cierra cuando el verificador confirme el output esperado).

## Objetivo
Que quede funcionando y verificable por un tercero el camino NLA real: cargar Qwen2.5-7B-Instruct cuantizado int4 en CPU, capturar la activación de la capa 20 en el límite de decisión, verbalizarla, y emitir un contrato de señales que el monitor de Gemini (`feature/gemini-monitor-codex`) pueda consumir tal cual.

## Decisiones y por qué
- **Los módulos reales viven en archivos `*_real.py` y los mock quedan intactos** — `run_experiment.py`/`train_probe.py`/`pytest` dependen de la firma mock (`ActivationHook(seed)`, `NlaMonitor()`); romperla violaba la coexistencia acordada (D1). Alternativa descartada: reescribir en su lugar los archivos (rompía el pipeline).
- **`max_new_tokens=20` por defecto + flag `--max-new-tokens`** — decisión de Juan: respuesta corta y rápida para la prueba; el verbalizador no necesita generar mucho. Alternativa descartada: 80 (lento, más RAM durante generación).
- **El smoke emite `results/monitor_cases.json`** con el contrato exacto que ya consume `smoke_test_monitor.py` de Jhoan (`scenario_id`, `policy`, `observable_transcript`, `cot`, `nla_text`, `probe_score`, `expected_action`) — así la integración se prueba sin tocar la rama de Jhoan ni su fixture. Se usa `None` en `probe_score` hasta correr `scripts/train_probe.py`.
- **`probe_score=None` hasta entrenar el probe** — el score real sale de `train_probe.py` (mismas activaciones); inventar un número habría corrompido la honestidad del puente.

## Pasos ejecutados
1. Verificación de estado git y diff en `feature/nla-probe`; detecté que `activation_hook.py`/`nla_monitor.py` locales ya tenían la versión real (rompía run_experiment).
2. Moví la versión real a `src/activation_hook_real.py` y `src/nla_monitor_real.py`; restauré los mocks con `git checkout`.
3. Reescribí `scripts/smoke_nla.py`: importa los `*_real`, flag `--max-new-tokens` (default 20) aplicado al agente y al verbalizador, y emisión de `results/monitor_cases.json`.
4. Maté dos procesos viejos de `smoke_nla.py` que colgaban RAM/logs (PID 1192/9844) y limpié logs sueltos de `results/`.
5. Commit `9dd7eb7` (4 archivos, 367 inserciones).
6. `pytest` → 8/8 OK (mocks intactos).

## Verificación
- `python -m pytest tests/ -q` → `........` (8 passed) desde `.venv/Scripts/python.exe`.
- `python -m py_compile` sobre los 4 archivos → OK.
- Los módulos reales quedan committeados en `9dd7eb7`; el smoke solo se puede validar end-to-end en la máquina de ≥18GB (ver `VERIFICAR-NLA.md`).

## Límites y pendientes
- No se marcó C0.3: la corrida real queda para el verificador de 18GB (handoff). No inventé su resultado.
- `probe_score` queda `None` hasta que corra `scripts/train_probe.py`; el canal `hybrid` de Gemini no se puede completar hasta entonces.
- Quedaron sin commitear (fuera del módulo): `pyproject.toml`, `uv.lock`, `scripts/run_smoke_detached.ps1`, `scripts/test_cpu_int4.py`, `scripts/test_peft_int4_toy.py` — tooling ad-hoc de exploración, decisión de incluirla cuando el equipo defina la gestión de deps.
- La integración completa con Gemini (merge + correr su monitor con nuestra data real) es pendiente explícito para la reunión: requiere la API key del encargado y el merge que hace Jhoan.