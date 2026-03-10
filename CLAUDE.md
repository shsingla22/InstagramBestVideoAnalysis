# CLAUDE.md — Memory Notes for Instagram Reel Analyzer

## Project Overview
This project analyzes Instagram Reels using Qwen3-VL (a vision-language model) to identify patterns that make reels go viral. Supports both local GPU (vLLM) and cloud API inference.

## Architecture
- **Inference**: Pluggable backend — Fireworks AI, Together AI, OpenRouter, DashScope, or local vLLM
- **FastAPI** app on port 8080 handles uploads, calls inference API, persists JSON results
- **Dashboard** at `/` shows stats, creator list, and analysis history
- Video frames extracted with OpenCV, resized to 384x384, base64-encoded, sent as multi-image chat completions

## Key Files
- `config.py` — all settings, provider config, creator list, analysis prompt
- `server/app.py` — FastAPI routes (dashboard, upload, results API)
- `server/inference_client.py` — unified client for all providers (cloud + local)
- `server/video_processor.py` — frame extraction (OpenCV + PIL)
- `server/vllm_client.py` — legacy client (kept for reference; inference_client.py is primary)
- `templates/dashboard.html` — Jinja2 dashboard
- `.env.example` — template for API keys and provider selection

## Running (Free — no GPU, no payment)
```bash
cp .env.example .env
# Sign up at https://openrouter.ai (free), paste API key:
export INFERENCE_PROVIDER=openrouter_free
export INFERENCE_API_KEY=your-openrouter-key
./scripts/start_app.sh       # web dashboard at http://localhost:8080
```

## Running (Paid cloud — higher limits)
```bash
export INFERENCE_PROVIDER=fireworks   # or: together, openrouter, dashscope
export INFERENCE_API_KEY=your-key
./scripts/start_app.sh
```

## Running (Local vLLM — needs GPU)
```bash
export INFERENCE_PROVIDER=vllm
./scripts/start_vllm.sh      # needs GPU with >= 24 GB VRAM
./scripts/start_app.sh
```

## All Providers
| Provider | Model ID | Cost | Video URL |
|----------|----------|------|-----------|
| **OpenRouter Free** | `qwen/qwen3-vl-235b-a22b-thinking:free` | **$0** | No |
| **Groq** | `meta-llama/llama-4-scout-17b-16e-instruct` | **$0** | No |
| **HuggingFace** | `Qwen/Qwen2.5-VL-7B-Instruct` | **$0** | No |
| Fireworks AI | `accounts/fireworks/models/qwen3-vl-8b-instruct` | Paid | No |
| Together AI | `Qwen/Qwen3-VL-32B-Instruct` | Paid | No |
| OpenRouter | `qwen/qwen3-vl-8b-instruct` | Paid | No |
| DashScope | `qwen3-vl-8b-instruct` | Paid | Yes |
| Local vLLM | `Qwen/Qwen3-VL-8B-Instruct` | Free (GPU) | Yes |

## Testing
```bash
python3 -m pytest tests/ -v   # 22 tests, all pass
```

## Model Notes
- Qwen3-VL-8B-Instruct needs ~20-24 GB VRAM at fp16 (local only)
- Available sizes: 2B, 4B, 8B, 32B (dense) + 30B-A3B, 235B-A22B (MoE)
- Two inference paths: `analyze_video_frames()` (works everywhere) and `analyze_video_native()` (vLLM/DashScope only)
- Set `OMP_NUM_THREADS=1` to avoid CPU contention with local vLLM

## Systemd (local deployment)
```bash
sudo ./scripts/install_systemd.sh
sudo systemctl start vllm-qwen3vl reel-analyzer
```
