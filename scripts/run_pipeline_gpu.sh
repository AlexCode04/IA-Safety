#!/usr/bin/env bash
# Reproducible BUDGET-NLA pipeline for a 64 GiB cluster node.
# Usage:
#   bash scripts/run_pipeline_gpu.sh demo
#   bash scripts/run_pipeline_gpu.sh real [gpu-index|auto]
# Backward compatible: bash scripts/run_pipeline_gpu.sh 0

set -euo pipefail
export PYTHONUNBUFFERED=1
export TOKENIZERS_PARALLELISM=false
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

FIRST="${1:-demo}"
if [[ "$FIRST" =~ ^[0-9]+$ ]]; then
    MODE="real"
    GPU_ID="$FIRST"
else
    MODE="$FIRST"
    GPU_ID="${2:-auto}"
fi
if [[ "$MODE" != "demo" && "$MODE" != "real" ]]; then
    echo "Usage: bash scripts/run_pipeline_gpu.sh [demo|real] [gpu-index|auto]"
    exit 2
fi

if [[ "$MODE" == "real" ]]; then
    if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi -L >/dev/null 2>&1; then
        if [[ "$GPU_ID" == "auto" ]]; then GPU_ID="0"; fi
        if ! nvidia-smi -L | grep -qE "^GPU ${GPU_ID}:"; then
            echo "ERROR: GPU $GPU_ID does not exist."
            nvidia-smi -L
            exit 1
        fi
        export CUDA_VISIBLE_DEVICES="$GPU_ID"
        export BUDGET_NLA_DEVICE=cuda
        nvidia-smi --id="$GPU_ID" --query-gpu=name,memory.total --format=csv,noheader
    else
        export BUDGET_NLA_DEVICE=cpu
        AVAILABLE_KIB="$(awk '/MemAvailable/ {print $2}' /proc/meminfo)"
        if (( AVAILABLE_KIB < 45 * 1024 * 1024 )); then
            echo "ERROR: CPU mode needs about 45 GiB available RAM; use a GPU node."
            exit 1
        fi
        echo "WARNING: CPU-only real mode fits a 64 GiB RAM node but can be slow."
    fi
fi

if [[ ! -d ".venv" ]]; then python3 -m venv .venv; fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
if [[ "$MODE" == "real" ]]; then
    python -m pip install -r requirements-nla.txt -r requirements-paper.txt
else
    python -m pip install -r requirements.txt -r requirements-paper.txt
fi

mkdir -p results
LOGFILE="results/pipeline_${MODE}.log"

run_step() {
    local label="$1"
    shift
    echo "==== $label ====" | tee -a "$LOGFILE"
    "$@" 2>&1 | tee -a "$LOGFILE"
}

if [[ "$MODE" == "demo" ]]; then
    run_step "[1/4] deterministic mock trajectories" \
        python scripts/run_experiment.py --reset-output
    run_step "[2/4] aggregate synthetic results" \
        python scripts/build_results.py
    run_step "[3/4] figures and bilingual result macros" \
        python scripts/generate_paper_figures.py --allow-mock
else
    if [[ ! -f ".env" ]]; then cp .env.example .env; fi
    if [[ -z "${GEMINI_API_KEY:-}" ]] && ! grep -qE '^GEMINI_API_KEY=.+$' .env; then
        read -r -s -p "GEMINI_API_KEY (not saved by this script): " GEMINI_API_KEY
        echo
        if [[ -z "$GEMINI_API_KEY" ]]; then
            echo "ERROR: GEMINI_API_KEY is required for real mode."
            exit 1
        fi
        export GEMINI_API_KEY
    fi
    run_step "[1/6] real Qwen + activation + NLA + probe" \
        python scripts/run_experiment.py --real --reset-output
    run_step "[2/6] frozen hand-off contract" \
        python scripts/export_monitor_cases.py
    run_step "[3/6] Gemini preflight (separate output)" \
        python scripts/run_gemini_monitor.py \
          --limit 3 --output results/gemini_preflight.jsonl
    run_step "[4/6] complete resumable Gemini evaluation" \
        python scripts/run_gemini_monitor.py
    run_step "[5/6] Gemini-integrated metrics" \
        python scripts/build_results.py
    run_step "[6/6] figures and bilingual result macros" \
        python scripts/generate_paper_figures.py
fi

run_step "[4/4] unit tests" python -m pytest -q

if command -v pdflatex >/dev/null 2>&1 && command -v bibtex >/dev/null 2>&1; then
    (
      cd paper
      for DOC in main_en main_es; do
        pdflatex -interaction=nonstopmode -halt-on-error "${DOC}.tex"
        bibtex "$DOC"
        pdflatex -interaction=nonstopmode -halt-on-error "${DOC}.tex"
        pdflatex -interaction=nonstopmode -halt-on-error "${DOC}.tex"
      done
    ) | tee -a "$LOGFILE"
else
    echo "LaTeX not installed; upload paper/ to Overleaf to compile both versions." | tee -a "$LOGFILE"
fi

echo "==== Complete ($MODE) ===="
echo "Dashboard: streamlit run app/dashboard.py"
echo "English:   paper/main_en.tex"
echo "Spanish:   paper/main_es.tex"
echo "Log:       $LOGFILE"
