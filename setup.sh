#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

VENV_DIR=".venv"
PYTHON="${PYTHON:-python3}"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "error: $PYTHON not found" >&2
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "[setup] creating venv in $VENV_DIR"
    "$PYTHON" -m venv "$VENV_DIR"
else
    echo "[setup] reusing existing venv in $VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

echo "[setup] installing requirements"
pip install -r requirements.txt

if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "warning: ffmpeg not found in PATH (required by py/live.py)" >&2
fi

echo "[setup] done. activate with: source $VENV_DIR/bin/activate"
echo "[setup] run pipeline with: $VENV_DIR/bin/python py/live.py"
