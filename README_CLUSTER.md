# BUDGET-NLA en cluster (una GPU de varias)

El proyecto corre en **una sola GPU** a elección, en un cluster Linux con
8×64 GB. No requiere configuración manual: el script crea el entorno,
prepara `.env` y ejecuta toda la cadena (modelo live, NLA, Gemini,
resultados y figuras del paper).

## Requisitos
- Linux con `python3` (3.10+) y una GPU NVIDIA con **≥16 GB VRAM** (bf16).
- Internet para bajar Qwen (HuggingFace) y la API de Gemini.
- (Los 64 GB de RAM de la VM sobran; el modelo cabe en GPU.)

## Uso

```bash
git clone -b integration/nla-gemini-postrun https://github.com/AlexCode04/IA-Safety.git
cd IA-Safety
bash scripts/run_pipeline_gpu.sh <gpu>
```

- `<gpu>` es el índice de la GPU a usar (0..7), según `nvidia-smi -L`.
- La primera vez pide la `GEMINI_API_KEY` (se guarda en `.env`, que NO se
  commitea). También puede pre-escribirse en `.env` antes de correr.

## Qué hace el script (6 pasos, ~40 min en GPU)
1. `run_experiment.py --real` (24 trayectorias live + activaciones capa 20)
2. `export_monitor_cases.py`
3. preflight Gemini (3 casos) y verificado completo (96 llamadas)
4. `build_results.py` → `results/summary.json`
5. `generate_paper_figures.py` → `paper/generated_results.tex`

Log completo en `results/pipeline_gpu.log`. Reanudable: cada paso es
idempotente (Gemini continúa donde quedó; los pasos 2–6 reutilizan salidas
previas si existen).

## Salidas entregables
- `results/summary.json`, `results/metrics.csv`, `results/runs.jsonl`
- `paper/generated_results.tex` (macros empíricas reales del paper)