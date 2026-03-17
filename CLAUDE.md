# CLAUDE.md — Memory Notes for Instagram Reel Analyzer

## Project Overview
This project analyzes Instagram Reels using vision-language models to identify patterns that make reels go viral. The system is organized into **3 modules** covering GPU-local, paid-cloud, and free-cloud inference — all sharing the same FastAPI app, video processor, and analysis pipeline.

## 3-Module Architecture

### Module 1 — Local GPU (vLLM + Qwen3-VL)
- **Provider key**: `vllm`
- **Model**: `Qwen/Qwen3-VL-8B-Instruct` (configurable via `VLLM_MODEL_NAME`)
- **Requires**: GPU with >= 24 GB VRAM (RTX 4090, A100, A6000)
- **Inference server**: vLLM v0.11+ on port 8000, OpenAI-compatible API
- **Unique capability**: Native `video_url` input — vLLM samples frames internally at 2 fps, no OpenCV extraction needed
- **Also supports**: Frame-based multi-image input (same as cloud)
- **Key config**: `VLLM_HOST`, `VLLM_PORT`, `VLLM_GPU_MEMORY_UTIL`, `VLLM_MAX_MODEL_LEN`, `VLLM_TENSOR_PARALLEL_SIZE`
- **Start**: `./scripts/start_vllm.sh` then `./scripts/start_app.sh`
- **Systemd**: `sudo ./scripts/install_systemd.sh && sudo systemctl start vllm-qwen3vl reel-analyzer`
- **Tip**: Set `OMP_NUM_THREADS=1` to avoid CPU contention

### Module 2 — Paid Cloud APIs
- **Provider keys**: `fireworks`, `together`, `openrouter`, `dashscope`
- **Models**: Qwen3-VL-8B (Fireworks, OpenRouter, DashScope), Qwen3-VL-32B (Together)
- **Requires**: API key + payment/credits
- **Inference**: OpenAI-compatible chat completions via each provider's endpoint
- **DashScope bonus**: Also supports native `video_url` (like vLLM)
- **Start**: `export INFERENCE_PROVIDER=fireworks && export INFERENCE_API_KEY=... && ./scripts/start_app.sh`

### Module 3 — Free Cloud APIs (no GPU, no payment)
- **Provider keys**: `openrouter_free`, `groq`, `huggingface`
- **Models**:
  - OpenRouter Free: `qwen/qwen3-vl-235b-a22b-thinking` (Qwen3-VL 235B MoE, $0, 20 req/min, 200/day)
  - Groq: `meta-llama/llama-4-scout-17b-16e-instruct` (Llama 4 Scout, $0, 30 req/min, ~460 tok/s)
  - HuggingFace: `Qwen/Qwen2.5-VL-7B-Instruct` (free tier, rate-limited)
- **Requires**: Free account signup only — no credit card
- **Start**: `export INFERENCE_PROVIDER=openrouter_free && export INFERENCE_API_KEY=... && ./scripts/start_app.sh`
- **Note**: OpenRouter free model is a "Thinking" variant — outputs chain-of-thought before JSON answer

## Shared Components (all 3 modules)
- `config.py` — all settings, provider config, creator list, analysis prompt
- `server/app.py` — FastAPI routes (dashboard, upload, results API) on port 8080
- `server/inference_client.py` — unified client for all 8 providers (cloud + local)
- `server/video_processor.py` — frame extraction (OpenCV + PIL), resize to 384x384, base64 encoding
- `server/vllm_client.py` — legacy client (kept for reference; inference_client.py is primary)
- `templates/dashboard.html` — Jinja2 dashboard at `/`
- `.env.example` — template for all API keys and provider selection

## All Providers (quick reference)
| Provider | Module | Model ID | Cost | Video URL |
|----------|--------|----------|------|-----------|
| Local vLLM | 1 (GPU) | `Qwen/Qwen3-VL-8B-Instruct` | Free (GPU) | Yes |
| Fireworks AI | 2 (Paid) | `accounts/fireworks/models/qwen3-vl-8b-instruct` | ~$0.20/M | No |
| Together AI | 2 (Paid) | `Qwen/Qwen3-VL-32B-Instruct` | ~$0.50/M | No |
| OpenRouter | 2 (Paid) | `qwen/qwen3-vl-8b-instruct` | ~$0.08/M | No |
| DashScope | 2 (Paid) | `qwen3-vl-8b-instruct` | Pay-per-use | Yes |
| **OpenRouter Free** | 3 (Free) | `qwen/qwen3-vl-235b-a22b-thinking` | **$0** | No |
| **Groq** | 3 (Free) | `meta-llama/llama-4-scout-17b-16e-instruct` | **$0** | No |
| **HuggingFace** | 3 (Free) | `Qwen/Qwen2.5-VL-7B-Instruct` | **$0** | No |

## Testing
```bash
python3 -m pytest tests/ -v   # 22 tests, all pass
```

## Two Inference Paths
- `analyze_video_frames()` — works with ALL providers; OpenCV extracts 16 frames, base64-encodes, sends as multi-image chat completion
- `analyze_video_native()` — vLLM and DashScope only; sends full video as base64 video_url, model samples frames internally
