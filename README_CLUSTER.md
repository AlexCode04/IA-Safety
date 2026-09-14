# BUDGET-NLA en un nodo de 64 GB

El repositorio ofrece dos rutas separadas y claramente rotuladas:

- `demo`: genera 24 trayectorias deterministas con monitores mock. Sirve para
  validar el contrato, el dashboard, las tablas y la maquetación del paper. No
  constituye evidencia de seguridad de Qwen, NLA o Gemini.
- `real`: carga Qwen2.5-7B, captura la activación de la capa 20, ejecuta el
  adaptador NLA, el probe LOTO y los 96 juicios aislados de Gemini.

## Requisitos

- Linux y Python 3.10 o posterior.
- Para `demo`: CPU y aproximadamente 4 GB de RAM.
- Para `real` con GPU: NVIDIA con CUDA; 20 GB de VRAM o más es lo
  recomendable. Si la VRAM es menor, `accelerate` puede descargar capas a RAM.
- Para `real` sin GPU: el cargador BF16 cabe en un nodo de 64 GiB de RAM,
  pero la generación puede ser lenta.
- Internet para descargar los checkpoints de Hugging Face y llamar a Gemini.
- `GEMINI_API_KEY` para la ruta real. Nunca se guarda ni se sube al repo.

## Entrega inmediata con datos sintéticos

```bash
git clone -b integration/bilingual-mock-delivery https://github.com/AlexCode04/IA-Safety.git
cd IA-Safety
bash scripts/run_pipeline_gpu.sh demo
streamlit run app/dashboard.py
```

La interfaz conserva el dashboard actual y muestra una advertencia visible de
“demostración sintética/mock”. Las dos versiones del artículo quedan en
`paper/main_en.tex` y `paper/main_es.tex`.

## Corrida real en el clúster

```bash
bash scripts/run_pipeline_gpu.sh real auto
```

También se puede fijar una GPU:

```bash
bash scripts/run_pipeline_gpu.sh real 0
```

Por compatibilidad, `bash scripts/run_pipeline_gpu.sh 0` equivale a
`real 0`.

El script:

1. comprueba GPU o al menos 45 GiB de RAM disponible para CPU;
2. instala dependencias en `.venv`;
3. ejecuta Qwen, el corte preacción, NLA y probe;
4. exporta `results/monitor_cases.json`;
5. hace un preflight Gemini separado y luego continúa las llamadas pendientes;
6. rehace las métricas usando los veredictos Gemini para Observable, CoT y NLA;
7. genera figuras y compila ambos documentos si LaTeX está instalado;
8. corre la suite de pruebas.

## Salidas

- `results/runs.jsonl`: trayectorias canónicas.
- `results/gemini_verdicts.jsonl`: juicios externos reanudables.
- `results/summary.json`: métricas, procedencia y alertas efectivas.
- `paper/generated_results.tex`: macros compartidas por ambos idiomas.
- `paper/main_en.pdf` y `paper/main_es.pdf` cuando existe LaTeX.
- `results/pipeline_demo.log` o `results/pipeline_real.log`.

El agregador bloquea por defecto una corrida real incompleta: no permite que el
paper use silenciosamente el `alert=False` provisional del NLA antes de
que Gemini evalúe su verbalización.
