"""Generate videos from reel prompts using the same providers as generate_reels.py."""

import json
import os
import shutil
import time
from pathlib import Path

# Output directory
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "article_reels"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _get_hf_client(space: str):
    """Create a Gradio client with optional HuggingFace token."""
    from gradio_client import Client

    hf_token = os.environ.get("HF_TOKEN", "")
    if hf_token:
        return Client(space, hf_token=hf_token)
    return Client(space)


def _extract_video_path(result) -> str | None:
    """Extract video file path from Gradio result."""
    if isinstance(result, tuple):
        for item in result:
            if isinstance(item, dict) and "video" in item:
                return item["video"]
            elif isinstance(item, str) and item.endswith(".mp4"):
                return item
    elif isinstance(result, dict) and "video" in result:
        return result["video"]
    elif isinstance(result, str) and result.endswith(".mp4"):
        return result
    return None


def generate_with_veo3(prompt: str, slug: str, duration: int = 8) -> dict:
    """Generate with Google Veo 3 (FREE — best quality)."""
    from google import genai
    from google.genai import types

    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY not set.\n"
            "  Get a FREE key: https://aistudio.google.com/apikey"
        )

    client = genai.Client(api_key=api_key)

    start = time.time()
    print("  Submitting to Veo 3...")
    operation = client.models.generate_videos(
        model="veo-3.0-generate-preview",
        prompt=prompt,
        config=types.GenerateVideosConfig(
            aspect_ratio="9:16",
            number_of_videos=1,
        ),
    )

    print("  Generating (1-3 minutes)...")
    poll_count = 0
    while not operation.done:
        time.sleep(10)
        operation = client.operations.get(operation)
        poll_count += 1
        if poll_count % 6 == 0:
            print(f"    Still generating... ({poll_count * 10}s)")

    elapsed = time.time() - start
    video_path = None

    if operation.result and operation.result.generated_videos:
        video = operation.result.generated_videos[0]
        output_path = OUTPUT_DIR / f"{slug}_veo3.mp4"
        client.files.download(file=video.video, download_path=str(output_path))
        video_path = str(output_path)
        size_mb = output_path.stat().st_size / 1024 / 1024
        print(f"  Generated: {size_mb:.1f} MB in {elapsed:.0f}s")
    else:
        print(f"  WARNING: Veo 3 returned no video.")

    return {"local_path": video_path, "elapsed": elapsed, "provider": "veo3"}


def generate_with_ltx(prompt: str, slug: str, duration: int = 5) -> dict:
    """Generate with LTX Video Distilled (FREE — no API key)."""
    client = _get_hf_client("Lightricks/ltx-video-distilled")

    start = time.time()
    result = client.predict(
        prompt=prompt,
        negative_prompt="worst quality, inconsistent motion, blurry, jittery, distorted, watermark",
        input_image_filepath=None,
        input_video_filepath=None,
        height_ui=768,
        width_ui=432,
        mode="text-to-video",
        duration_ui=min(duration, 5),
        ui_frames_to_use=9,
        seed_ui=42,
        randomize_seed=True,
        ui_guidance_scale=1,
        improve_texture_flag=True,
        api_name="/text_to_video",
    )
    elapsed = time.time() - start

    video_path = _extract_video_path(result)
    if video_path:
        output_path = OUTPUT_DIR / f"{slug}_ltx.mp4"
        shutil.copy2(video_path, str(output_path))
        video_path = str(output_path)

    return {"local_path": video_path, "elapsed": elapsed, "provider": "ltx"}


def generate_with_cogvideo(prompt: str, slug: str, model: str = "5b") -> dict:
    """Generate with CogVideoX (FREE — no API key)."""
    spaces = {
        "5b": "THUDM/CogVideoX-5B-Space",
        "2b": "zai-org/CogVideoX-2B-Space",
    }
    space = spaces.get(model, spaces["5b"])
    client = _get_hf_client(space)

    start = time.time()
    if model == "2b":
        # CogVideoX-2B supports prompt enhancement
        try:
            enhanced = client.predict(prompt=prompt, api_name="/enhance_prompt_func")
            if enhanced and len(enhanced) > 20:
                prompt = enhanced
        except Exception:
            pass
        result = client.predict(
            prompt=prompt, num_inference_steps=50, guidance_scale=6.0,
            api_name="/generate",
        )
    else:
        result = client.predict(
            prompt=prompt, image_input=None, video_input=None,
            api_name="/generate",
        )
    elapsed = time.time() - start

    video_path = _extract_video_path(result)
    if video_path:
        output_path = OUTPUT_DIR / f"{slug}_cogvideo{model}.mp4"
        shutil.copy2(video_path, str(output_path))
        video_path = str(output_path)

    return {"local_path": video_path, "elapsed": elapsed, "provider": f"cogvideo{model}"}


def generate_with_fal(prompt: str, slug: str, duration: int = 5,
                      fal_provider: str = "kling3") -> dict:
    """Generate with fal.ai paid providers."""
    import fal_client

    endpoints = {
        "kling3": "fal-ai/kling-video/v3/pro/text-to-video",
        "kling26": "fal-ai/kling-video/v2.6/pro/text-to-video",
        "veo3_fal": "fal-ai/veo3",
        "minimax": "fal-ai/minimax/video-01-live",
        "wan26": "fal-ai/wan/v2.6/text-to-video",
        "seedance": "fal-ai/bytedance/seedance/v1.5/pro/text-to-video",
    }
    endpoint = endpoints.get(fal_provider, endpoints["kling3"])

    start = time.time()
    result = fal_client.subscribe(
        endpoint,
        arguments={
            "prompt": prompt,
            "duration": str(duration),
            "aspect_ratio": "9:16",
            "generate_audio": True,
        },
        with_logs=True,
    )
    elapsed = time.time() - start

    # Download video
    video_url = None
    if isinstance(result, dict):
        video_data = result.get("video", result.get("output", {}))
        if isinstance(video_data, dict):
            video_url = video_data.get("url")
        elif isinstance(video_data, str):
            video_url = video_data

    video_path = None
    if video_url:
        import httpx
        output_path = OUTPUT_DIR / f"{slug}_{fal_provider}.mp4"
        with httpx.stream("GET", video_url, timeout=120, follow_redirects=True) as resp:
            resp.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in resp.iter_bytes(8192):
                    f.write(chunk)
        video_path = str(output_path)

    return {"local_path": video_path, "elapsed": elapsed, "provider": fal_provider}


# Provider dispatch
PROVIDERS = {
    "veo3": generate_with_veo3,
    "ltx": generate_with_ltx,
    "cogvideo5b": lambda p, s, **kw: generate_with_cogvideo(p, s, model="5b"),
    "cogvideo2b": lambda p, s, **kw: generate_with_cogvideo(p, s, model="2b"),
}

FAL_PROVIDER_KEYS = ["kling3", "kling26", "veo3_fal", "minimax", "wan26", "seedance"]


def generate_video(prompt: str, slug: str, provider: str = "ltx",
                   duration: int = 5) -> dict:
    """Generate a video using the specified provider.

    Args:
        prompt: The video generation prompt
        slug: Article slug (used for output filename)
        provider: Video provider key
        duration: Target duration in seconds

    Returns:
        dict with local_path, elapsed, provider
    """
    if provider in PROVIDERS:
        return PROVIDERS[provider](prompt, slug, duration=duration)
    elif provider in FAL_PROVIDER_KEYS:
        return generate_with_fal(prompt, slug, duration=duration, fal_provider=provider)
    else:
        raise ValueError(f"Unknown provider: {provider}. Available: {list(PROVIDERS.keys()) + FAL_PROVIDER_KEYS}")
