# Instagram Reel Analyzer

Analyze Instagram Reels with **Qwen3-VL** (vision-language model) to discover what makes content go viral. Works **100% free** with cloud APIs — no GPU, no payment required.

## Features

- Upload any video reel for AI-powered virality analysis
- Structured JSON output: hook type, emotional trigger, pacing, virality score, and more
- Web dashboard with stats, creator tracking, and result history
- **7 inference backends** including 2 free-tier options
- systemd services for production deployment
- 22 unit tests covering all components

## Quick Start (Free — no GPU, no payment)

```bash
pip install -r requirements.txt

# Option A: OpenRouter free tier (sign up at https://openrouter.ai)
export INFERENCE_PROVIDER=openrouter_free
export INFERENCE_API_KEY=your-openrouter-key

# Option B: HuggingFace free tier (sign up at https://huggingface.co)
# export INFERENCE_PROVIDER=huggingface
# export HF_TOKEN=hf_your_token

./scripts/start_app.sh   # Dashboard at http://localhost:8080
```

## Quick Start (Paid cloud — higher limits)

```bash
export INFERENCE_PROVIDER=fireworks   # or: together, openrouter, dashscope
export INFERENCE_API_KEY=your-key-here
./scripts/start_app.sh
```

## Quick Start (Local vLLM — GPU)

```bash
./scripts/setup.sh
export INFERENCE_PROVIDER=vllm
./scripts/start_vllm.sh     # Requires GPU with >= 24GB VRAM
./scripts/start_app.sh
```

## Supported Providers

| Provider | Model | Cost | Rate Limits |
|----------|-------|------|-------------|
| **OpenRouter Free** | qwen3-vl-235b | **$0** | 20 req/min, 200/day |
| **HuggingFace** | qwen2.5-vl-7b | **$0** | Rate-limited |
| Fireworks AI | qwen3-vl-8b | ~$0.20/M tokens | High |
| Together AI | qwen3-vl-32b | ~$0.50/M input | High |
| OpenRouter | qwen3-vl-8b | ~$0.08/M input | High |
| DashScope | qwen3-vl-8b | Pay-per-use | High |
| Local vLLM | qwen3-vl-8b | Free (needs GPU) | Unlimited |

## Documentation

- [Full Report](REPORT.md) — viral patterns research, architecture, API reference
- [Memory Notes](CLAUDE.md) — development notes and quick reference
- [.env.example](.env.example) — configuration template

## Testing

```bash
python3 -m pytest tests/ -v   # 22 tests
```
