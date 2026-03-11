#!/usr/bin/env python3
"""Generate viral Instagram Reels using AI video generation models.

Reads the VIRAL_REELS_PLAYBOOK.md principles and generates short-form vertical
videos (9:16) using the best available AI video generation APIs.

Supported providers (via fal.ai unified API):
  - Kling 3.0 Pro — newest, multi-shot, $0.029/sec (CHEAPEST)
  - Kling 2.6 Pro — proven quality, $0.07/sec
  - Veo 3 — Google's best, highest quality, $0.40/sec
  - Veo 3.1 Fast — Google quality at lower cost, $0.10/sec
  - MiniMax Video 01 — fast generation, $0.10/sec
  - Wan 2.6 — open-source quality, $0.05/sec
  - Seedance 1.5 — ByteDance, great motion, $0.05/sec

Also supports OpenAI Sora 2 API and Runway Gen-4 API directly.

Usage:
  export FAL_KEY=your-fal-api-key        # Get from https://fal.ai/dashboard/keys
  python3 scripts/generate_reels.py       # Generate all 5 templates
  python3 scripts/generate_reels.py --template 1  # Generate specific template
  python3 scripts/generate_reels.py --provider sora --openai-key sk-...  # Use Sora
  python3 scripts/generate_reels.py --provider runway --runway-key ...   # Use Runway

Providers (via fal.ai):
  --provider kling3     Kling 3.0 Pro (default, cheapest, $0.029/sec)
  --provider kling26    Kling 2.6 Pro ($0.07/sec)
  --provider veo3       Google Veo 3 (highest quality, $0.40/sec)
  --provider veo31fast  Google Veo 3.1 Fast ($0.10/sec)
  --provider minimax    MiniMax Video 01 Live ($0.10/sec)
  --provider wan26      Wan 2.6 (open-source, $0.05/sec)
  --provider seedance   ByteDance Seedance 1.5 ($0.05/sec)

Direct API providers:
  --provider sora       OpenAI Sora 2 (requires --openai-key, $0.10/sec)
  --provider runway     Runway Gen-4 Turbo (requires --runway-key)
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DATA_DIR

GENERATED_DIR = DATA_DIR / "generated"
GENERATED_DIR.mkdir(exist_ok=True)

# ── Provider configurations ──────────────────────────────────────────────────
FAL_PROVIDERS = {
    "kling3": {
        "endpoint": "fal-ai/kling-video/v3/pro/text-to-video",
        "name": "Kling 3.0 Pro",
        "cost_per_sec": 0.029,
        "max_duration": "10",
        "supports_audio": True,
    },
    "kling26": {
        "endpoint": "fal-ai/kling-video/v2.6/pro/text-to-video",
        "name": "Kling 2.6 Pro",
        "cost_per_sec": 0.07,
        "max_duration": "10",
        "supports_audio": True,
    },
    "veo3": {
        "endpoint": "fal-ai/veo3",
        "name": "Google Veo 3",
        "cost_per_sec": 0.40,
        "max_duration": "8",
        "supports_audio": True,
    },
    "veo31fast": {
        "endpoint": "fal-ai/veo3/fast",
        "name": "Google Veo 3.1 Fast",
        "cost_per_sec": 0.10,
        "max_duration": "8",
        "supports_audio": False,
    },
    "minimax": {
        "endpoint": "fal-ai/minimax/video-01-live",
        "name": "MiniMax Video 01 Live",
        "cost_per_sec": 0.10,
        "max_duration": "6",
        "supports_audio": True,
    },
    "wan26": {
        "endpoint": "fal-ai/wan/v2.6/text-to-video",
        "name": "Wan 2.6 (Alibaba)",
        "cost_per_sec": 0.05,
        "max_duration": "10",
        "supports_audio": False,
    },
    "seedance": {
        "endpoint": "fal-ai/bytedance/seedance/v1.5/pro/text-to-video",
        "name": "ByteDance Seedance 1.5",
        "cost_per_sec": 0.05,
        "max_duration": "10",
        "supports_audio": True,
    },
}

# ── Viral Reel Templates (derived from VIRAL_REELS_PLAYBOOK.md) ─────────────
# Each template applies proven viral mechanics from our analysis.
REEL_TEMPLATES = [
    {
        "id": 1,
        "name": "Motivational Talking Head",
        "format": "talking_head",
        "duration": "5",
        "aspect_ratio": "9:16",
        "viral_mechanics": [
            "Direct eye contact (6.8/10 avg virality for face content)",
            "Animated expression (parasocial trigger)",
            "Bold text hook in frame 1",
            "Jump-cut pacing",
        ],
        "prompt": (
            "A confident young woman in her late 20s speaking directly to camera "
            "with animated hand gestures and passionate facial expressions. She has "
            "an energetic, inspiring presence. Clean solid dark navy blue background "
            "with soft professional studio lighting. She is mid-speech, leaning "
            "slightly forward with wide eyes as if sharing an important secret. "
            "Bold white text overlay at the top of the frame reads 'Stop waiting "
            "for the perfect moment'. Close-up head and shoulders framing, "
            "vertical 9:16 format. Natural skin tones, warm lighting. "
            "The energy is HIGH — she genuinely believes what she's saying."
        ),
    },
    {
        "id": 2,
        "name": "Satisfying Cooking Close-Up",
        "format": "cooking_asmr",
        "duration": "5",
        "aspect_ratio": "9:16",
        "viral_mechanics": [
            "Satisfying visual triggers (completion drive)",
            "ASMR-like quality",
            "Overhead angle (proven food format)",
            "Vivid colors (engagement boost)",
        ],
        "prompt": (
            "Overhead close-up shot of a beautiful pasta dish being plated in a "
            "bright, clean white kitchen. Golden spaghetti is being twirled with "
            "tongs and placed onto a pristine white plate. Rich red tomato sauce "
            "is drizzled in a circular motion. Fresh green basil leaves are placed "
            "on top. Steam rises from the hot pasta. Bright, even overhead lighting. "
            "The colors are vivid and saturated — golden pasta, deep red sauce, "
            "bright green herbs. Vertical 9:16 format. The movement is smooth and "
            "deliberate, almost meditative. The final frame shows the completed "
            "beautiful dish with a garnish of parmesan being grated on top."
        ),
    },
    {
        "id": 3,
        "name": "Before-After Room Transformation",
        "format": "transformation",
        "duration": "5",
        "aspect_ratio": "9:16",
        "viral_mechanics": [
            "Curiosity gap (show after first)",
            "Transformation = highest save rate",
            "Speed ramp editing",
            "Satisfying payoff",
        ],
        "prompt": (
            "A stunning, magazine-worthy modern living room reveal shot. The camera "
            "slowly pans across a beautifully decorated room with warm golden-hour "
            "sunlight streaming through large windows. Clean white walls, a plush "
            "cream sofa with colorful throw pillows, a stylish wooden coffee table "
            "with fresh flowers, and a gallery wall with modern art. The room glows "
            "with warm amber tones. Bold white text overlay reads 'I can't believe "
            "this is the same room'. Vertical 9:16 format. The scene feels aspirational "
            "and inviting — the kind of room that makes you want to save it for "
            "inspiration. Professional interior design photography quality."
        ),
    },
    {
        "id": 4,
        "name": "Couple Cozy Moment",
        "format": "relatable_couple",
        "duration": "5",
        "aspect_ratio": "9:16",
        "viral_mechanics": [
            "Universal relatability (7/10 virality)",
            "Tag-your-partner comment bait",
            "Warm intimate lighting",
            "Emotional empathy trigger",
        ],
        "prompt": (
            "A cozy couple moment in a warm bedroom at night. A young couple sits "
            "up in bed together — she is leaning her head on his shoulder while "
            "he wraps his arm around her. Warm amber bedside lamp lighting creates "
            "a soft, intimate glow. Cream colored blankets and pillows. Both are "
            "smiling gently with eyes closed, content and peaceful. The scene "
            "feels genuine and unposed — like a real candid moment captured. "
            "Vertical 9:16 format. Bold white text overlay at top reads "
            "'Every couple at 11pm'. The color palette is entirely warm — amber, "
            "cream, soft gold. No harsh lights. The mood is intimate, cozy, and "
            "universally relatable."
        ),
    },
    {
        "id": 5,
        "name": "Cinematic Golden-Hour Motivation",
        "format": "cinematic_motivation",
        "duration": "5",
        "aspect_ratio": "9:16",
        "viral_mechanics": [
            "Golden-hour palette (highest engagement colors)",
            "Silhouette with face visible",
            "Motivational text overlay",
            "Inspirational emotional trigger",
        ],
        "prompt": (
            "A dramatic golden-hour cinematic shot of a fit person standing on a "
            "hilltop overlooking a city skyline at sunset. They are silhouetted "
            "against a massive orange sun, but their face is partially visible "
            "in profile — determined expression, looking toward the horizon. "
            "The sky is a gradient from deep amber at the horizon to warm purple "
            "at the top. The city below is hazy and sprawling. Bold white text "
            "overlay reads 'Day one or one day — you decide'. Vertical 9:16 format. "
            "The person stands tall with confident posture, fists slightly clenched. "
            "Slow cinematic camera movement — slight upward tilt. The entire image "
            "glows with warm golden tones. Professional cinematography quality."
        ),
    },
]


def generate_with_fal(template: dict, provider_key: str) -> dict:
    """Generate a video using fal.ai API."""
    import fal_client

    provider = FAL_PROVIDERS[provider_key]
    endpoint = provider["endpoint"]

    print(f"  Provider: {provider['name']} ({endpoint})")
    print(f"  Estimated cost: ${provider['cost_per_sec'] * int(template['duration']):.2f}")

    input_params = {
        "prompt": template["prompt"],
        "duration": template["duration"],
        "aspect_ratio": template["aspect_ratio"],
    }

    if provider["supports_audio"]:
        input_params["generate_audio"] = True

    def on_queue_update(update):
        if hasattr(update, "logs") and update.logs:
            for log in update.logs:
                print(f"    [{log.message}]")

    start = time.time()
    result = fal_client.subscribe(
        endpoint,
        arguments=input_params,
        with_logs=True,
        on_queue_update=on_queue_update,
    )
    elapsed = time.time() - start

    return {
        "result": result,
        "elapsed_seconds": elapsed,
        "provider": provider["name"],
        "endpoint": endpoint,
    }


def generate_with_sora(template: dict, api_key: str) -> dict:
    """Generate a video using OpenAI Sora 2 API."""
    import httpx

    print(f"  Provider: OpenAI Sora 2")
    print(f"  Estimated cost: ${0.10 * int(template['duration']):.2f} (720p)")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Step 1: Create video generation job
    payload = {
        "model": "sora-2",
        "input": {
            "prompt": template["prompt"],
        },
        "size": "1080x1920",
        "seconds": int(template["duration"]),
    }

    start = time.time()

    resp = httpx.post(
        "https://api.openai.com/v1/videos",
        json=payload,
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    job = resp.json()
    video_id = job["id"]
    print(f"  Job created: {video_id}")

    # Step 2: Poll for completion
    for attempt in range(120):  # Max 10 minutes
        time.sleep(5)
        status_resp = httpx.get(
            f"https://api.openai.com/v1/videos/{video_id}",
            headers=headers,
            timeout=30,
        )
        status_resp.raise_for_status()
        status = status_resp.json()

        if status.get("status") == "completed":
            print(f"  Video completed!")
            break
        elif status.get("status") == "failed":
            raise RuntimeError(f"Sora generation failed: {status}")
        else:
            if attempt % 6 == 0:
                print(f"    Status: {status.get('status', 'unknown')}...")
    else:
        raise TimeoutError("Sora generation timed out after 10 minutes")

    # Step 3: Download video
    content_resp = httpx.get(
        f"https://api.openai.com/v1/videos/{video_id}/content",
        headers=headers,
        timeout=120,
    )
    content_resp.raise_for_status()

    elapsed = time.time() - start

    return {
        "result": {
            "video_bytes": content_resp.content,
            "video_id": video_id,
        },
        "elapsed_seconds": elapsed,
        "provider": "OpenAI Sora 2",
        "endpoint": "api.openai.com/v1/videos",
    }


def generate_with_runway(template: dict, api_key: str) -> dict:
    """Generate a video using Runway Gen-4 Turbo API."""
    import httpx

    print(f"  Provider: Runway Gen-4 Turbo")
    print(f"  Estimated cost: ~$0.31 per 5s clip")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Runway-Version": "2024-11-06",
    }

    payload = {
        "model": "gen4_turbo",
        "promptText": template["prompt"],
        "duration": int(template["duration"]),
        "ratio": "720:1280",  # 9:16 vertical
    }

    start = time.time()

    resp = httpx.post(
        "https://api.dev.runwayml.com/v1/text_to_video",
        json=payload,
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    task = resp.json()
    task_id = task["id"]
    print(f"  Task created: {task_id}")

    # Poll for completion
    for attempt in range(120):
        time.sleep(5)
        status_resp = httpx.get(
            f"https://api.dev.runwayml.com/v1/tasks/{task_id}",
            headers=headers,
            timeout=30,
        )
        status_resp.raise_for_status()
        status = status_resp.json()

        if status.get("status") == "SUCCEEDED":
            video_url = status.get("output", [None])[0]
            print(f"  Video completed!")
            elapsed = time.time() - start
            return {
                "result": {"video": {"url": video_url}},
                "elapsed_seconds": elapsed,
                "provider": "Runway Gen-4 Turbo",
                "endpoint": "api.dev.runwayml.com",
            }
        elif status.get("status") == "FAILED":
            raise RuntimeError(f"Runway generation failed: {status.get('failure', 'unknown')}")
        else:
            if attempt % 6 == 0:
                print(f"    Status: {status.get('status', 'unknown')}...")

    raise TimeoutError("Runway generation timed out after 10 minutes")


def download_video(url: str, output_path: Path) -> None:
    """Download a video from URL to local file."""
    import httpx

    print(f"  Downloading to {output_path.name}...")
    with httpx.stream("GET", url, timeout=120, follow_redirects=True) as resp:
        resp.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in resp.iter_bytes(chunk_size=8192):
                f.write(chunk)
    size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"  Downloaded: {size_mb:.1f} MB")


def main():
    parser = argparse.ArgumentParser(description="Generate viral Instagram Reels with AI")
    parser.add_argument("--template", type=int, choices=[1, 2, 3, 4, 5],
                        help="Generate a specific template (1-5). Default: all")
    parser.add_argument("--provider", default="kling3",
                        choices=list(FAL_PROVIDERS.keys()) + ["sora", "runway"],
                        help="Video generation provider (default: kling3)")
    parser.add_argument("--openai-key", default=os.environ.get("OPENAI_API_KEY", ""),
                        help="OpenAI API key (required for --provider sora)")
    parser.add_argument("--runway-key", default=os.environ.get("RUNWAYML_API_SECRET", ""),
                        help="Runway API key (required for --provider runway)")
    parser.add_argument("--list", action="store_true",
                        help="List available templates and exit")
    args = parser.parse_args()

    if args.list:
        print("\nAvailable Reel Templates:")
        print(f"{'─' * 70}")
        for t in REEL_TEMPLATES:
            print(f"  [{t['id']}] {t['name']} ({t['format']})")
            print(f"      Duration: {t['duration']}s | Aspect: {t['aspect_ratio']}")
            print(f"      Viral mechanics: {', '.join(t['viral_mechanics'][:2])}")
            print()

        print(f"\nAvailable Providers:")
        print(f"{'─' * 70}")
        print(f"  {'Provider':<12} {'Model':<28} {'Cost/sec':>10} {'API':<10}")
        print(f"  {'─'*12} {'─'*28} {'─'*10} {'─'*10}")
        for key, p in FAL_PROVIDERS.items():
            print(f"  {key:<12} {p['name']:<28} ${p['cost_per_sec']:<9.3f} fal.ai")
        print(f"  {'sora':<12} {'OpenAI Sora 2':<28} ${'0.100':<9} OpenAI")
        print(f"  {'runway':<12} {'Runway Gen-4 Turbo':<28} ${'0.062':<9} Runway")
        return

    # Validate API keys
    if args.provider == "sora":
        if not args.openai_key:
            print("ERROR: --openai-key required for Sora provider")
            print("  Usage: python3 scripts/generate_reels.py --provider sora --openai-key sk-...")
            sys.exit(1)
    elif args.provider == "runway":
        if not args.runway_key:
            print("ERROR: --runway-key required for Runway provider")
            print("  Usage: python3 scripts/generate_reels.py --provider runway --runway-key key-...")
            sys.exit(1)
    else:
        fal_key = os.environ.get("FAL_KEY", "")
        if not fal_key:
            print("ERROR: Set FAL_KEY environment variable")
            print("  1. Sign up at https://fal.ai (free signup, pay-per-use)")
            print("  2. Get API key from https://fal.ai/dashboard/keys")
            print("  3. export FAL_KEY=your-key-here")
            print()
            print("  Cost estimate for all 5 templates (5s each):")
            for key, p in FAL_PROVIDERS.items():
                total = p["cost_per_sec"] * 5 * 5
                print(f"    {key:<12}: ${total:.2f} total ({p['name']})")
            sys.exit(1)

    # Select templates to generate
    templates = REEL_TEMPLATES
    if args.template:
        templates = [t for t in REEL_TEMPLATES if t["id"] == args.template]

    direct_providers = {"sora": "OpenAI Sora 2", "runway": "Runway Gen-4 Turbo"}
    provider_name = FAL_PROVIDERS.get(args.provider, {}).get("name", direct_providers.get(args.provider, args.provider))

    print(f"\n{'=' * 70}")
    print(f"  VIRAL REEL GENERATOR")
    print(f"  Provider: {provider_name}")
    print(f"  Templates: {len(templates)}")
    print(f"  Output: {GENERATED_DIR}")
    print(f"{'=' * 70}")

    results = []

    for i, template in enumerate(templates):
        print(f"\n{'─' * 70}")
        print(f"  [{i + 1}/{len(templates)}] Generating: {template['name']}")
        print(f"  Format: {template['format']} | Duration: {template['duration']}s")
        print(f"  Viral mechanics: {', '.join(template['viral_mechanics'])}")
        print(f"{'─' * 70}")

        try:
            if args.provider == "sora":
                gen_result = generate_with_sora(template, args.openai_key)
                # Save Sora video directly from bytes
                output_path = GENERATED_DIR / f"reel_{template['id']}_{template['format']}.mp4"
                with open(output_path, "wb") as f:
                    f.write(gen_result["result"]["video_bytes"])
                video_url = f"local://{output_path}"
            elif args.provider == "runway":
                gen_result = generate_with_runway(template, args.runway_key)
                video_data = gen_result["result"]
                video_url = video_data.get("video", {}).get("url", "")
                output_path = GENERATED_DIR / f"reel_{template['id']}_{template['format']}.mp4"
                if video_url and video_url.startswith("http"):
                    download_video(video_url, output_path)
                else:
                    print(f"  WARNING: No video URL in Runway result.")
                    output_path = GENERATED_DIR / f"reel_{template['id']}_{template['format']}_result.json"
                    with open(output_path, "w") as f:
                        json.dump(gen_result["result"], f, indent=2)
            else:
                gen_result = generate_with_fal(template, args.provider)
                # Download video from fal result
                video_data = gen_result["result"]
                video_url = video_data.get("video", {}).get("url", "")
                if not video_url:
                    # Try alternate result formats
                    if isinstance(video_data, dict):
                        video_url = video_data.get("url", "") or video_data.get("output", {}).get("url", "")
                    print(f"  Result keys: {list(video_data.keys()) if isinstance(video_data, dict) else type(video_data)}")

                output_path = GENERATED_DIR / f"reel_{template['id']}_{template['format']}.mp4"
                if video_url and video_url.startswith("http"):
                    download_video(video_url, output_path)
                else:
                    print(f"  WARNING: No video URL in result. Raw result saved.")
                    output_path = GENERATED_DIR / f"reel_{template['id']}_{template['format']}_result.json"
                    with open(output_path, "w") as f:
                        json.dump(gen_result["result"] if isinstance(gen_result["result"], dict) else str(gen_result["result"]), f, indent=2)

            result_entry = {
                "template_id": template["id"],
                "template_name": template["name"],
                "format": template["format"],
                "provider": gen_result["provider"],
                "elapsed_seconds": gen_result["elapsed_seconds"],
                "video_url": video_url if isinstance(video_url, str) else str(video_url),
                "output_file": str(output_path),
                "viral_mechanics": template["viral_mechanics"],
                "status": "success",
            }
            results.append(result_entry)

            print(f"\n  SUCCESS: Generated in {gen_result['elapsed_seconds']:.1f}s")
            print(f"  Output: {output_path}")

        except Exception as e:
            print(f"\n  ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "template_id": template["id"],
                "template_name": template["name"],
                "status": "error",
                "error": str(e),
            })

        # Rate limit between generations
        if i < len(templates) - 1:
            print(f"\n  [waiting 5s between generations...]")
            time.sleep(5)

    # Save generation results
    results_path = GENERATED_DIR / "generation_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

    # Summary
    successful = [r for r in results if r.get("status") == "success"]
    print(f"\n{'=' * 70}")
    print(f"  GENERATION COMPLETE: {len(successful)}/{len(results)} videos")
    print(f"  Results: {results_path}")
    print(f"{'=' * 70}")

    if successful:
        total_cost = sum(
            FAL_PROVIDERS.get(args.provider, {}).get("cost_per_sec", 0.10) * 5
            for _ in successful
        )
        print(f"\n  Estimated total cost: ${total_cost:.2f}")
        print(f"\n  Generated videos:")
        for r in successful:
            print(f"    [{r['template_id']}] {r['template_name']} — {r['output_file']}")

    print(f"\n  To analyze these with the expert prompt:")
    print(f"    export INFERENCE_API_KEY=your-key")
    print(f"    python3 scripts/run_analysis.py")


if __name__ == "__main__":
    main()
