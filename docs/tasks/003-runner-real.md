# Task 003 — Corredor real del agente (Qwen2.5-7B-Instruct)

**Fecha:** 2026-09-13 · **Autor:** opencode/Juan · **Rama:** feature/nla-probe · **Estado:** cerrada

## Cumple el checklist
- [ ] C1.1 — código listo: `AgentRunner(mock_mode=False)` delega a `RealAgentRunner`; corrida real pendiente de máquina ≥18GB.
- [ ] C1.2 — `decision_marker_found` detecta `\n<DECISION>\n` en la respuesta generada y el hook real añade `position_name = PRE_ACTION_DECISION_BOUNDARY`; verificación del token exacto pendiente de la corrida real.
- [ ] C1.3 — `NlaMonitorReal` ya existía (commit `9dd7eb7`) y ahora `run_experiment.py` usa el monitor real en `mock_mode=false`; verbalización real pendiente de la corrida ≥18GB.
- [ ] C1.5 — parser `parse_tool_call` con fallback a `critical_tool` y `call_parse_failed` probado con tests (sin GPU); corrida completa de los 4 escenarios pendiente.
- [ ] C0.3 — avance parcial: rama real cableada end-to-end, falta la corrida fumada (handoff `VERIFICAR-NLA.md`).

## Objetivo
Que el experimento pueda ejecutarse contra el Qwen real (int4, CPU) en vez del mock determinista, con el
contrato de salida congelado (`<DECISION>` + `ACTION: {"tool_name": ..., "arguments": {...}}`), sin tocar la
firma de `AgentRunner` ni los mocks de los que dependen los tests.

## Decisiones y por qué
- `RealAgentRunner` vive en `src/agent_runner_real.py` nuevo y `_run_live()` importa de forma lazy — los mocks
  siguen siendo los que usan los tests y el modo real no se carga en pytest — se descartó meter la lógica real
  directo en `agent_runner.py`.
- Firma `AgentRunner(model, temperature, mock_mode=True)` intacta con kwargs opcionales
  `model_obj/tokenizer/max_new_tokens/system_prompt` — cero riesgo de romper `tests/test_run_experiment.py` —
  alternativa descartada: añadir argumentos posicionales.
- Parser tolerante: busca el último bloque `{...}` balanceado hacia atrás y valida `tool_name` contra
  `{publish_report, send_email, update_allowlist}` y que `arguments` sea `dict` — el modelo real puede emitir
  texto antes del JSON.
- Fallback explícito: si no hay JSON válido, `proposed_tool = critical_tool`, `arguments = {}`, y el flag
  `call_parse_failed` queda en `AgentOutput` (se persiste el fallback real propuesto) — honestidad en vez de
  inventar una acción.
- En modo real el modelo se carga UNA vez con `ModelLoader` y se comparten `model_obj/tokenizer` entre el
  runner, el hook real y el NLA real — evitar doble carga (RAM), se descartó cargar por componente.
- La captura del hook real usa `output.prefix_until_decision()` (razonamiento + marcador) para disparar el hook
  justo en el límite previo a la acción — igual que el smoke test.

## Pasos ejecutados
1. `src/agent_runner_real.py` nuevo: `SYSTEM_PROMPT`, `KNOWN_TOOLS`, `parse_tool_call`, `RealAgentRunner`.
2. `src/agent_runner.py`: `AgentOutput.call_parse_failed` (default False) + kwargs opcionales + rama `_run_live`.
3. `src/activation_hook_real.py`: añadido `self.position_name = POSITION_NAME` (python: `run_experiment.py` lo lee).
4. `scripts/run_experiment.py`: interruptor mock/real por `config["experiment"]["mock_mode"]`; carga única del
   modelo; hook real con `capture(prefix_until_decision())`.
5. `scripts/train_probe.py`: mismo interruptor, modelo cargado una vez fuera del loop.
6. `tests/test_agent_runner_real.py`: 8 tests del parser y del contrato (sin GPU).

## Verificación
- `python -m pytest -q tests/` → 16/16 OK (8 previos + 8 nuevos).
- `python -m py_compile` sobre los 5 archivos tocados → OK.
- La corrida real de C0.3/C1.x se verifica en máquina ≥18GB siguiendo `VERIFICAR-NLA.md` (delegada).

## Límites y pendientes
- No se ejecutó el Qwen real (sin máquina ≥18GB): falta confirmar el `position_name` correcto del hook, el
  tiempo de generación por trayectoria y que el `apply_chat_template` sea el mismo que usa `smoke_nla.py`.
- `call_parse_failed` no se persiste en el schema (vive en `AgentOutput`); si se quiere en el log, es Pieza posterior.