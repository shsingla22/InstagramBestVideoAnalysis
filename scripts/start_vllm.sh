#!/usr/bin/env bash
# Launch vLLM serving Qwen3-VL for video analysis.
# Usage: ./scripts/start_vllm.sh [model_name] [gpu_count]
set -euo pipefail

MODEL="${1:-Qwen/Qwen3-VL-8B-Instruct}"
TP="${2:-1}"
PORT="${VLLM_PORT:-8000}"
GPU_UTIL="${VLLM_GPU_MEMORY_UTIL:-0.85}"
MAX_LEN="${VLLM_MAX_MODEL_LEN:-4096}"

echo "=== Starting vLLM ==="
echo "Model:  $MODEL"
echo "Port:   $PORT"
echo "TP:     $TP"
echo "GPU %:  $GPU_UTIL"

export OMP_NUM_THREADS=1  # Avoid CPU contention with vLLM

exec vllm serve "$MODEL" \
    --port "$PORT" \
    --host 0.0.0.0 \
    --tensor-parallel-size "$TP" \
    --gpu-memory-utilization "$GPU_UTIL" \
    --max-model-len "$MAX_LEN" \
    --trust-remote-code \
    --dtype auto
