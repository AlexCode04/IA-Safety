# VERIFICAR-NLA.md — Verificación del módulo NLA (para la persona verificadora)

Este documento te guía paso a paso para verificar que el módulo NLA funciona sobre el modelo
real. Está escrito asumiendo que sos la persona que menos conoce el repo. Al final vas a
comprobar (a) que el modelo carga, (b) que se verbaliza la activación de la capa 20, y
(c) que se generan las señales que alimentan al monitor de Gemini.

Tiempo estimado: **5 a 10 minutos** contando la carga y generación.

---

## 1. Requisitos

- **RAM: 18 GB libres (mínimo).** En esta máquina NUNCA debe ejecutarse (se murió varias veces
  en 16 GB). Si tenés dudas de si tu máquina alcanza, no lo corras: avisá y lo corremos en
  otra.
- Python 3.11.
- Git.

## 2. Preparar el entorno (primer uso)

Desde una terminal dentro de la carpeta del repo:

```bash
python -m venv .venv
```

- Windows: `.venv\Scripts\activate`
- Linux/macOS: `source .venv/bin/activate`

Instalar dependencias:

```bash
pip install -r requirements.txt
pip install torch torchao peft transformers accelerate sentencepiece psutil
```

> Si `pip install torch` baja la versión CUDA gigante y no querés, instalá la versión CPU:
> `pip install torch --index-url https://download.pytorch.org/whl/cpu`.
> En esta prueba usamos CPU (int4), no se necesita GPU.

La primera corrida descarga los pesos del modelo (~15 GB en el caché de Hugging Face). Hacelo
con paciencia; después queda cacheado.

## 3. Correr el smoke test

```bash
python -u scripts/smoke_nla.py
```

`-u` es importante: el proceso imprime en vivo, no parece "colgado". No filtres la salida con
pipes. Si querés ahorrar tiempo en esta primera verificación:

```bash
python -u scripts/smoke_nla.py --max-new-tokens 20
```

(20 tokens es el valor por defecto; es lo que necesitamos para el pipe con Gemini.)

## 4. Qué tenés que ver

Al arrancar:

```
RAM libre antes de cargar:  XX.XXGB
RAM libre despues de cargar: YY.YYGB
```

Después, para cada uno de los 3 escenarios (`external_report-BENIGN-v1`,
`external_report-VISIBLE_SABOTAGE-v1`, `external_report-STEALTH_SABOTAGE-v1`):

```
=== external_report-BENIGN-v1 ===
prompt: ...
respuesta del agente:
<texto que genera el modelo>
activation: shape=(1, 3584)
verbalizacion de la capa 20:
<texto de ~20 tokens describiendo el vector>
```

`shape=(1, 3584)` es la dimensión oculta del Qwen2.5-7B: si ves otra cosa, avisá.

Al final:

```
smoke test guardado en results/smoke_nla.txt
contrato de senales guardado en results/monitor_cases.json
nota: probe_score es null hasta correr scripts/train_probe.py
```

## 5. Checklist de verificación (marcá y respondé)

| # | Ítem | OK / Detalle |
|---|------|--------------|
| 1 | El modelo cargó sin excepción | ☐ |
| 2 | Para los 3 escenarios hay `respuesta del agente` + `verbalizacion de la capa 20` | ☐ |
| 3 | `activation: shape=(1, 3584)` en todos | ☐ |
| 4 | `results/smoke_nla.txt` y `results/monitor_cases.json` existen y no están vacíos | ☐ |
| 5 | `monitor_cases.json` tiene 3 entradas con: `scenario_id`, `policy`, `observable_transcript`, `cot`, `nla_text`, `probe_score`, `expected_action` | ☐ |
| 6 | RAM libre tras la corrida volvió a un valor sano (no quedó proceso colgado) | ☐ |

Si todos son ☐ → el módulo NLA quedó verificado y avisá al equipo el resultado (guardá el
checklist). Si algo falla, copiá el mensaje de error completo y avisá.

## 6. Qué significa cada salida (para entenderlo)

- **Respuesta del agente**: el modelo contesta el prompt del escenario siguiendo el system
  prompt, que le pide terminar con `<DECISION>`.
- **Activación L20**: el vector residual de la capa 20 en el token `<DECISION>`. Es la "señal
  interna" que leemos del modelo.
- **Verbalización NLA**: el verbalizador re-inyecta ese vector en su propio prompt (en el token
  sentinela `㈀`) y describe con palabras qué representa. Es la traducción de la señal interna a
  texto que un monitor grande (Gemini) puede leer.
- **Contracto con Gemini**: `monitor_cases.json` es exactamente lo que consume el
  `smoke_test_monitor.py` del monitor de Gemini. `probe_score` queda `None` porque se llena con
  el probe entrenado por `scripts/train_probe.py` (paso siguiente, no bloqueante para esta
  verificación).

## 7. Límites honestos (qué NO demuestra esto)

- No valida que la verbalización sea "correcta" ni que distinga bienes de maliciosos: solo
  verifica que carga, captura y verbaliza sin romperse.
- No corre el monitor de Gemini (depende de la API key del encargado).
- No reemplaza las métricas del experimento completo (PHR/BDR/etc.).
- El ruido del texto verbalizado puede variar entre corridas; lo importante es que muestre
  contenido coherente (no vacío ni error).

---

## Contrato de señales NLA → Gemini (para la reunión de integración)

El monitor de Gemini (`GeminiMonitor`) recibe ESTAS señales por canal. Este repo ya produce
todas las que están marcadas con *:

| Canal Gemini | Campo que consume | Fuente en este repo | Estado |
|--------------|-------------------|---------------------|--------|
| `observable` | `observable_transcript` | acción del agente, derivada del `<DECISION>` en `scripts/smoke_nla.py` * | ✅ |
| `cot` | `cot` | respuesta del agente (`_agent_response`) * | ✅ |
| `nla` | `nla_text` | `NlaMonitor.verbalize(activation)` (`src/nla_monitor_real.py`) * | ✅ |
| `hybrid` | `probe_score` | `scripts/train_probe.py` (logreg L20) | ⏳ pendiente correr probe |
| todos | `policy` | del escenario (`data/scenarios.yaml`) * | ✅ |
| — | `expected_action` | `ALLOW`/`BLOCK` según condición del escenario * | ✅ |

Pasos de la reunión (con el encargado de la API key):
1. `python -u scripts/train_probe.py` para llenar `probe_score`.
2. Re-correr `python -u scripts/smoke_nla.py` → `monitor_cases.json` completo.
3. En `feature/gemini-monitor-codex`: apuntar `smoke_test_monitor.py` a este `monitor_cases.json`
   (o copiarlo a `tests/fixtures/`) y correr sus 3 escenarios × 4 canales.
4. El merge a `main` lo hace Jhoan, como quedó definido con AGENTS.