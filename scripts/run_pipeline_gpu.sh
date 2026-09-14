#!/usr/bin/env bash
# Pipeline BUDGET-NLA completo en una GPU del cluster.
# Uso:  bash scripts/run_pipeline_gpu.sh <gpu-index>
#  <gpu-index> = índice de la GPU (0..N-1) según `nvidia-smi -L`.
#
# Ejecuta en orden: run_experiment (live real) -> export casos ->
# preflight Gemini -> Gemini full -> build_results -> paper figures.
# Incluye el setup de entorno (.venv, deps) y crea .env si hace falta.

set -euo pipefail

export PYTHONUNBUFFERED=1
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

GPU_ID="${1:-}"
if [[ -z "$GPU_ID" ]]; then
    echo "Uso: bash scripts/run_pipeline_gpu.sh <gpu-index>"
    echo "  <gpu-index> = índice de la GPU a usar (ver 'nvidia-smi -L')."
    exit 2
fi

if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "ERROR: nvidia-smi no encontrado. ¿Este nodo tiene GPU NVIDIA?"
    exit 1
fi

if ! nvidia-smi -L | grep -qE "^GPU ${GPU_ID}:"; then
    echo "ERROR: GPU index ${GPU_ID} no existe. GPUs disponibles:"
    nvidia-smi -L
    exit 1
fi

export CUDA_VISIBLE_DEVICES="$GPU_ID"
GPU_NAME="$(nvidia-smi --id="$GPU_ID" --query-gpu=name --format=csv,noheader | head -1)"
echo "==== Usando GPU ${GPU_ID}: ${GPU_NAME} (CUDA_VISIBLE_DEVICES=${GPU_ID}) ===="

ENV_FILE=".env"
if [[ ! -f "$ENV_FILE" ]]; then
    if [[ ! -f ".env.example" ]]; then
        echo "ERROR: falta .env.example. ¿El repo está incompleto?"
        exit 1
    fi
    cp .env.example "$ENV_FILE"
    echo "Creado .env desde .env.example"
fi

# Asegurar el modo real: MOCK_MODE=false en runtime (run_experiment usa --real, pero los
# artefactos de Gemini/paper leen esta variable).
sed -i 's/^MOCK_MODE=.*/MOCK_MODE=false/' "$ENV_FILE"

# Si no hay API key, pedirla una vez (no se commitea a git).
if ! grep -qE '^GEMINI_API_KEY=.+' "$ENV_FILE"; then
    echo "Falta GEMINI_API_KEY en ${ENV_FILE}."
    echo -n "Pegá la API key y presioná Enter: "
    read -r -s _KEY
    echo
    if [[ -z "$_KEY" ]]; then
        echo "ERROR: no se ingresó API key."
        exit 1
    fi
    sed -i "s/^GEMINI_API_KEY=.*/GEMINI_API_KEY=${_KEY}/" "$ENV_FILE"
    unset _KEY
fi

if [[ ! -d ".venv" ]]; then
    echo "==== Creando entorno virtual .venv ===="
    python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==== Instalando dependencias ===="
pip install --upgrade pip >/dev/null
pip install -r requirements-nla.txt -r requirements-paper.txt

RESULTS_DIR="results"
mkdir -p "$RESULTS_DIR"
LOGFILE="$RESULTS_DIR/pipeline_gpu.log"
echo "==== Log: $LOGFILE ===="

run_step() {
    local label="$1"
    shift
    echo
    echo "##############################"
    echo "#### $label"
    echo "##############################"
    "$@" 2>&1 | tee -a "$LOGFILE"
}

run_step "[1/6] run_experiment --real (live, trae 24 trayectorias + activaciones)" \
    python scripts/run_experiment.py --real --reset-output

run_step "[2/6] export_monitor_cases (crea casos para Gemini)" \
    python scripts/export_monitor_cases.py

run_step "[3/6] Gemini preflight (limit 3, verifica API key)" \
    python scripts/run_gemini_monitor.py --limit 3 --overwrite

run_step "[4/6] Gemini full (96 veredictos)" \
    python scripts/run_gemini_monitor.py --overwrite

run_step "[5/6] build_results (summary.json)" \
    python scripts/build_results.py

run_step "[6/6] generate_paper_figures (macros LaTeX reales)" \
    python scripts/generate_paper_figures.py

echo
echo "==== Pipeline completo ====="
echo "Resultados:  results/metrics.csv, results/runs.jsonl, results/summary.json"
echo "Macros:      paper/generated_results.tex (empírico real)"
echo "Log:         $LOGFILE"