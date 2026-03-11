#!/usr/bin/env python3
"""Batch-download Instagram reels and analyze them with Qwen3-VL via OpenRouter Free.

Usage:
    export INFERENCE_PROVIDER=openrouter_free
    export INFERENCE_API_KEY=sk-or-v1-...
    python3 scripts/batch_analyze.py
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import VIDEOS_DIR, RESULTS_DIR, INSTAGRAM_COOKIES_FILE, INSTAGRAM_COOKIES_FROM_BROWSER
from server.video_processor import extract_frames, frames_to_base64
from server.inference_client import analyze_video_frames

# Top 10 creators with known viral reel URLs
REELS = []  # Will be populated from a JSON file or command-line


def load_reels(path: str) -> list[dict]:
    """Load reel list from JSON file."""
    with open(path) as f:
        return json.load(f)


def download_reel(url: str, creator: str, index: int) -> str | None:
    """Download a reel using yt-dlp. Returns path to downloaded file or None."""
    output_path = VIDEOS_DIR / f"{creator}_{index}.mp4"
    if output_path.exists():
        print(f"  [skip] Already downloaded: {output_path.name}")
        return str(output_path)

    cmd = [
        "yt-dlp",
        "--no-check-certificates",
        "-f", "mp4/best[ext=mp4]/best",
        "-o", str(output_path),
        "--no-playlist",
        "--socket-timeout", "30",
        "--retries", "3",
    ]

    # Add Instagram authentication via cookies
    if INSTAGRAM_COOKIES_FILE and Path(INSTAGRAM_COOKIES_FILE).exists():
        cmd.extend(["--cookies", INSTAGRAM_COOKIES_FILE])
    elif INSTAGRAM_COOKIES_FROM_BROWSER:
        cmd.extend(["--cookies-from-browser", INSTAGRAM_COOKIES_FROM_BROWSER])

    cmd.append(url)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0 and output_path.exists():
            size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"  [ok] Downloaded {output_path.name} ({size_mb:.1f} MB)")
            return str(output_path)
        else:
            print(f"  [fail] yt-dlp error: {result.stderr[:200]}")
            return None
    except subprocess.TimeoutExpired:
        print(f"  [fail] Download timed out for {url}")
        return None
    except Exception as e:
        print(f"  [fail] {e}")
        return None


async def analyze_single(video_path: str, creator: str, reel_info: dict) -> dict:
    """Extract frames and run analysis on a single video."""
    print(f"  [analyze] Extracting frames from {Path(video_path).name}...")
    frames = extract_frames(video_path, max_frames=16)
    if not frames:
        return {"status": "error", "error": "No frames extracted"}

    b64_frames = frames_to_base64(frames)
    print(f"  [analyze] Sending {len(b64_frames)} frames to Qwen3-VL...")

    result = await analyze_video_frames(b64_frames)
    result["creator"] = creator
    result["url"] = reel_info.get("url", "")
    result["description"] = reel_info.get("description", "")

    # Save individual result
    result_path = RESULTS_DIR / f"{creator}_{reel_info.get('index', 0)}_result.json"
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"  [saved] {result_path.name}")

    return result


async def main():
    reels_file = Path(__file__).parent.parent / "data" / "reels_to_analyze.json"
    if not reels_file.exists():
        print(f"ERROR: {reels_file} not found. Create it first.")
        sys.exit(1)

    reels = load_reels(str(reels_file))
    print(f"\n{'='*60}")
    print(f"Instagram Reel Batch Analysis")
    print(f"Provider: {os.getenv('INFERENCE_PROVIDER', 'openrouter_free')}")
    print(f"Reels to analyze: {len(reels)}")
    print(f"{'='*60}\n")

    results = []

    for i, reel in enumerate(reels):
        creator = reel["creator"]
        url = reel["url"]
        reel["index"] = i

        print(f"\n[{i+1}/{len(reels)}] {creator}: {reel.get('description', '')}")
        print(f"  URL: {url}")

        # Download
        video_path = download_reel(url, creator, i)
        if not video_path:
            results.append({
                "creator": creator,
                "url": url,
                "status": "download_failed",
            })
            continue

        # Analyze
        try:
            result = await analyze_single(video_path, creator, reel)
            results.append(result)

            if result.get("status") == "success":
                a = result["analysis"]
                print(f"  [result] Virality: {a.get('virality_score', '?')}/10 "
                      f"| Hook: {a.get('hook_type', '?')} "
                      f"| Emotion: {a.get('emotional_trigger', '?')}")
            else:
                print(f"  [result] Partial/failed: {result.get('raw', '')[:100]}")

        except Exception as e:
            print(f"  [error] Analysis failed: {e}")
            results.append({
                "creator": creator,
                "url": url,
                "status": "analysis_failed",
                "error": str(e),
            })

        # Rate limit: be nice to free tier
        if i < len(reels) - 1:
            print("  [wait] Rate limit pause (5s)...")
            time.sleep(5)

    # Save combined results
    combined_path = RESULTS_DIR / "batch_results.json"
    with open(combined_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n{'='*60}")
    print(f"Done! {len([r for r in results if r.get('status') == 'success'])}/{len(reels)} analyzed successfully")
    print(f"Results saved to {combined_path}")
    print(f"{'='*60}")

    return results


if __name__ == "__main__":
    asyncio.run(main())
