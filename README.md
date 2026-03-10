# Instagram Reel Analyzer

Analyze Instagram Reels with **Qwen3-VL** (vision-language model) to discover what makes content go viral. Works with **cloud APIs** (no GPU needed) or **local vLLM**.

## Features

- Upload any video reel for AI-powered virality analysis
- Structured JSON output: hook type, emotional trigger, pacing, virality score, and more
- Web dashboard with stats, creator tracking, and result history
- **5 inference backends**: Fireworks AI, Together AI, OpenRouter, Alibaba DashScope, local vLLM
- systemd services for production deployment
- 22 unit tests covering all components

## Quick Start (Cloud — no GPU)

```bash
pip install -r requirements.txt

# Set your provider and API key
export INFERENCE_PROVIDER=fireworks   # or: together, openrouter, dashscope
export INFERENCE_API_KEY=your-key-here

./scripts/start_app.sh   # Dashboard at http://localhost:8080
```

## Quick Start (Local vLLM — GPU)

```bash
./scripts/setup.sh
export INFERENCE_PROVIDER=vllm
./scripts/start_vllm.sh     # Requires GPU with >= 24GB VRAM
./scripts/start_app.sh      # Dashboard at http://localhost:8080
```

## Supported Providers

| Provider | Model | GPU Required | Pricing |
|----------|-------|-------------|---------|
| Fireworks AI | qwen3-vl-8b | No | ~$0.20/M tokens |
| Together AI | qwen3-vl-32b | No | ~$0.50/M input |
| OpenRouter | qwen3-vl-8b | No | ~$0.08/M input |
| DashScope | qwen3-vl-8b | No | Pay-per-use |
| Local vLLM | qwen3-vl-8b | Yes (24GB+) | Free |

## Documentation

- [Full Report](REPORT.md) — viral patterns research, architecture, API reference
- [Memory Notes](CLAUDE.md) — development notes and quick reference
- [.env.example](.env.example) — configuration template

## Testing

```bash
python3 -m pytest tests/ -v   # 22 tests
```
