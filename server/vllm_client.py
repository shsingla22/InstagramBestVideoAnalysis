"""Client for the vLLM OpenAI-compatible API serving Qwen3-VL."""

import json
import logging

import httpx

from config import VLLM_HOST, VLLM_PORT, VLLM_MODEL_NAME, VIDEO_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)

VLLM_BASE_URL = f"http://{'127.0.0.1' if VLLM_HOST == '0.0.0.0' else VLLM_HOST}:{VLLM_PORT}"


async def check_vllm_health() -> dict:
    """Check if the vLLM server is up and which models are loaded."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(f"{VLLM_BASE_URL}/v1/models")
            resp.raise_for_status()
            return {"status": "healthy", "models": resp.json()}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


async def analyze_video_frames(base64_frames: list[str], custom_prompt: str | None = None) -> dict:
    """Send base64-encoded video frames to Qwen3-VL via the vLLM OpenAI-compatible API.

    Sends frames as individual images in a multi-image chat completion request.
    Returns the parsed JSON analysis or raw text on parse failure.
    """
    prompt = custom_prompt or VIDEO_ANALYSIS_PROMPT

    # Build multi-image content for the OpenAI vision API format
    content: list[dict] = []
    for b64 in base64_frames:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
        })
    content.append({"type": "text", "text": prompt})

    payload = {
        "model": VLLM_MODEL_NAME,
        "messages": [
            {"role": "user", "content": content},
        ],
        "max_tokens": 2048,
        "temperature": 0.2,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(f"{VLLM_BASE_URL}/v1/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()

    raw_text = data["choices"][0]["message"]["content"]
    return _parse_analysis(raw_text)


async def analyze_video_native(video_base64: str, custom_prompt: str | None = None) -> dict:
    """Send a full video as base64 to Qwen3-VL using vLLM's native video_url support.

    Requires vLLM >= 0.11.0. The server handles frame sampling internally
    (default: 2 fps with do_sample_frames=True).
    """
    prompt = custom_prompt or VIDEO_ANALYSIS_PROMPT

    content = [
        {
            "type": "video_url",
            "video_url": {"url": f"data:video/mp4;base64,{video_base64}"},
        },
        {"type": "text", "text": prompt},
    ]

    payload = {
        "model": VLLM_MODEL_NAME,
        "messages": [
            {"role": "user", "content": content},
        ],
        "max_tokens": 2048,
        "temperature": 0.2,
    }

    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(f"{VLLM_BASE_URL}/v1/chat/completions", json=payload)
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
