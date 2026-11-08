#!/usr/bin/env bash
# One-shot setup for a fresh machine (macOS or Linux).
# Prereqs: git, Python 3.12+, and Ollama (https://ollama.com/download).
set -euo pipefail
cd "$(dirname "$0")"

MODEL="$(grep -E '^\s*model:' config.yaml | head -1 | sed 's/.*model:[[:space:]]*//; s/[[:space:]]*#.*//')"

# 1. Python environment
PY="${PYTHON:-python3.12}"
command -v "$PY" >/dev/null || PY=python3
"$PY" -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt

# 2. Local model server
if ! curl -sf localhost:11434/api/version >/dev/null 2>&1; then
  echo "Ollama server is not running. Start it in another shell with:  ollama serve"
  echo "Then re-run this script, or pull the model yourself:  ollama pull $MODEL"
else
  ollama pull "$MODEL"
fi

# 3. Smoke test (no LLM needed)
.venv/bin/python -m pytest -q
echo
echo "Ready. Reproduce the analysis from committed data:"
echo "  PYTHONPATH=src .venv/bin/python analysis/analyze.py main"
echo "Re-run the full collection (needs the model + ~4h on a 16GB machine):"
echo "  PYTHONPATH=src .venv/bin/python -m delivery.run --split main --sessions 3 --session 1"
