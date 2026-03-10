"""Unified inference client for Qwen3-VL via cloud APIs or local vLLM.

Supports: Fireworks AI, Together AI, OpenRouter, Alibaba DashScope, local vLLM.
All providers use the OpenAI-compatible chat completions format.
"""

import json
import logging

import httpx

from config import INFERENCE_PROVIDER, VIDEO_ANALYSIS_PROMPT, get_provider_config

logger = logging.getLogger(__name__)


def _get_headers() -> dict:
    """Build auth headers for the active provider."""
    cfg = get_provider_config()
    headers = {"Content-Type": "application/json"}
    if cfg["api_key"]:
        headers["Authorization"] = f"Bearer {cfg['api_key']}"
    return headers


def _get_base_url() -> str:
    return get_provider_config()["base_url"]


def _get_model() -> str:
    return get_provider_config()["model"]


async def check_health() -> dict:
    """Check if the inference backend is reachable."""
    cfg = get_provider_config()
    base_url = cfg["base_url"]
    headers = _get_headers()

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(f"{base_url}/models", headers=headers)
            resp.raise_for_status()
            return {
                "status": "healthy",
                "provider": INFERENCE_PROVIDER,
                "model": cfg["model"],
                "models": resp.json(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": INFERENCE_PROVIDER,
                "model": cfg["model"],
                "error": str(e),
            }


async def analyze_video_frames(base64_frames: list[str], custom_prompt: str | None = None) -> dict:
    """Send base64-encoded video frames as multi-image chat completion.

    Works with ALL providers (cloud and local). Each frame is sent as a
    separate image_url in the message content.
    """
    prompt = custom_prompt or VIDEO_ANALYSIS_PROMPT

    content: list[dict] = []
    for b64 in base64_frames:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
        })
    content.append({"type": "text", "text": prompt})

    payload = {
        "model": _get_model(),
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 2048,
        "temperature": 0.2,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{_get_base_url()}/chat/completions",
            json=payload,
            headers=_get_headers(),
        )
        resp.raise_for_status()
        data = resp.json()

    raw_text = data["choices"][0]["message"]["content"]
    return _parse_analysis(raw_text)


async def analyze_video_native(video_base64: str, custom_prompt: str | None = None) -> dict:
    """Send a full video as base64 using the video_url content type.

    Only supported by vLLM (>=0.11.0) and Alibaba DashScope.
    Falls back to frame-based analysis if the provider doesn't support it.
    """
    cfg = get_provider_config()
    if not cfg["supports_video_url"]:
        raise NotImplementedError(
            f"Provider '{INFERENCE_PROVIDER}' does not support native video_url. "
            "Use analyze_video_frames() instead."
        )

    prompt = custom_prompt or VIDEO_ANALYSIS_PROMPT

    content = [
        {
            "type": "video_url",
            "video_url": {"url": f"data:video/mp4;base64,{video_base64}"},
        },
        {"type": "text", "text": prompt},
    ]

    payload = {
        "model": _get_model(),
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 2048,
        "temperature": 0.2,
    }

    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(
            f"{_get_base_url()}/chat/completions",
            json=payload,
            headers=_get_headers(),
        )
        resp.raise_for_status()
        data = resp.json()

    raw_text = data["choices"][0]["message"]["content"]
    return _parse_analysis(raw_text)


def _parse_analysis(raw_text: str) -> dict:
    """Try to parse model output as JSON."""
    try:
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        analysis = json.loads(cleaned)
        return {"status": "success", "analysis": analysis, "raw": raw_text}
    except json.JSONDecodeError:
        logger.warning("Model returned non-JSON response: %s", raw_text[:200])
        return {"status": "partial", "analysis": None, "raw": raw_text}
