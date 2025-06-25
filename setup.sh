#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="kariyer-asistani"
VENV_DIR="${PROJECT_NAME}-env"
DEV_MODE="${DEV_MODE:-false}"

echo "🔧 [1/5] Creating Python virtual env → ${VENV_DIR}"
python -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"

echo "⬆️ [2/5] Upgrading pip/setuptools/wheel"
python -m pip install --upgrade --quiet pip setuptools wheel

echo "📦 [3/5] Installing runtime deps"
python -m pip install --requirement requirements.txt --quiet

if [[ "${DEV_MODE}" == "true" ]]; then
  echo "🛠️ [3b] Installing dev dependencies"
  python -m pip install --editable ".[dev]" --quiet

  echo "🏃 [3c] Warm-up: initial code quality check"
  if command -v ruff >/dev/null; then
    echo "  - Running Ruff format..."
    ruff format src main.py tree_generator.py --quiet
    echo "  - Running Ruff check..."
    ruff check src main.py tree_generator.py --quiet --fix
  fi

  if command -v mypy >/dev/null; then
    echo "  - Running MyPy check..."
    mypy src main.py tree_generator.py --config-file=pyproject.toml --quiet || true
  fi
fi

echo "🔐 [4/5] Writing placeholder .env"
cat > .env <<'EOF'
GEMINI_API_KEY=REPLACE_ME
PROJECT_NAME="Akıllı Kariyer Asistanı"
LOG_LEVEL="INFO"
EOF

echo "📜 [5/5] Environment summary"
python -m pip list | grep -E "(google-generativeai|chromadb|jobspy|pandas)" || true
echo "VENV   : ${VENV_DIR}"
echo "DEV    : ${DEV_MODE}"
echo "STATUS : ✅ Environment ready"
