# CLAUDE.md — Memory Notes for Instagram Reel Analyzer

## Project Overview
This project analyzes Instagram Reels using Qwen3-VL (a vision-language model) served via vLLM to identify patterns that make reels go viral.

## Architecture
- **vLLM** serves `Qwen/Qwen3-VL-8B-Instruct` on port 8000 (OpenAI-compatible API)
- **FastAPI** app on port 8080 handles uploads, calls vLLM, persists JSON results
- **Dashboard** at `/` shows stats, creator list, and analysis history
- Video frames are extracted with OpenCV, resized to 384x384, base64-encoded, sent as multi-image chat completions

## Key Files
- `config.py` — all settings, creator list, analysis prompt
- `server/app.py` — FastAPI routes (dashboard, upload, results API)
- `server/video_processor.py` — frame extraction (OpenCV + PIL)
- `server/vllm_client.py` — async client for vLLM OpenAI API
- `templates/dashboard.html` — Jinja2 dashboard
- `scripts/start_vllm.sh` — launch vLLM
- `scripts/start_app.sh` — launch FastAPI
- `scripts/systemd/` — systemd unit files for both services

## Running
```bash
./scripts/setup.sh          # install deps
./scripts/start_vllm.sh     # needs GPU with >= 24 GB VRAM
./scripts/start_app.sh      # web dashboard
```

## Testing
```bash
python3 -m pytest tests/ -v   # 17 tests, all pass
```

## Model Notes
- Qwen3-VL-8B-Instruct needs ~20-24 GB VRAM at fp16
- Available sizes: 2B, 4B, 8B, 32B (dense) + 30B-A3B, 235B-A22B (MoE)
- All have -Instruct, -Thinking, -FP8, -GGUF variants
- vLLM >= 0.11.0 required (native `video_url` support + frame-based)
- `qwen-vl-utils==0.0.14` needed alongside vLLM
- Two inference paths in vllm_client.py: `analyze_video_frames()` (manual frames) and `analyze_video_native()` (video_url)
- The analysis prompt outputs structured JSON with virality scoring
- Set `OMP_NUM_THREADS=1` to avoid CPU contention with vLLM

## Systemd
```bash
sudo ./scripts/install_systemd.sh
sudo systemctl start vllm-qwen3vl reel-analyzer
```
