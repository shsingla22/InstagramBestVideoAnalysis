#!/usr/bin/env bash
# One-shot setup: install dependencies, create dirs, verify GPU.
set -euo pipefail

echo "=== Instagram Reel Analyzer Setup ==="
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# 1. Python venv
if [ ! -d "venv" ]; then
    echo "[1/4] Creating virtual environment..."
    python3 -m venv venv
else
    echo "[1/4] Virtual environment exists."
fi

source venv/bin/activate

# 2. Install deps
echo "[2/4] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 3. Create directories
echo "[3/4] Creating data directories..."
mkdir -p data/videos data/results

# 4. GPU check
echo "[4/4] Checking GPU availability..."
if command -v nvidia-smi &>/dev/null; then
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    echo "GPU detected. Ready to run vLLM."
else
    echo "WARNING: No GPU detected. vLLM requires a CUDA-capable GPU."
    echo "  Recommended: NVIDIA GPU with >= 24 GB VRAM for Qwen3-VL-8B"
    echo "  The web dashboard will still work; vLLM just won't be reachable."
fi

echo ""
echo "=== Setup complete ==="
echo "Start vLLM:      ./scripts/start_vllm.sh"
echo "Start dashboard:  ./scripts/start_app.sh"
echo "Open browser:     http://localhost:8080"
