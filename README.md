# Instagram Reel Analyzer

Analyze Instagram Reels with **Qwen3-VL** (vision-language model) served via **vLLM** to discover what makes content go viral.

## Features

- Upload any video reel for AI-powered virality analysis
- Structured JSON output: hook type, emotional trigger, pacing, virality score, and more
- Web dashboard with stats, creator tracking, and result history
- systemd services for production deployment
- 17 unit tests covering all components

## Quick Start

```bash
./scripts/setup.sh          # Install dependencies
./scripts/start_vllm.sh     # Start vLLM (requires GPU with >= 24GB VRAM)
./scripts/start_app.sh      # Start web dashboard at http://localhost:8080
```

## Architecture

- **vLLM** serves Qwen3-VL-8B-Instruct on port 8000
- **FastAPI** app on port 8080 handles uploads and renders dashboard
- **OpenCV** extracts 16 frames per video, encoded as base64 for the vision model

## Documentation

- [Full Report](REPORT.md) — viral patterns research, architecture, API reference
- [Memory Notes](CLAUDE.md) — development notes and quick reference

## Testing

```bash
python3 -m pytest tests/ -v
```
