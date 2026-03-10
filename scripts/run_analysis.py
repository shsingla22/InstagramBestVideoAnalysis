#!/usr/bin/env python3
"""Run Qwen3-VL analysis on all downloaded sample videos via OpenRouter Free."""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("INFERENCE_PROVIDER", "openrouter_free")

from config import VIDEOS_DIR, RESULTS_DIR
from server.video_processor import extract_frames, frames_to_base64
from server.inference_client import analyze_video_frames

CREATOR_INFO = {
    "khaby_lame_0": {"creator": "@khaby.lame", "style": "Comedy/Reaction", "niche": "comedy"},
    "zachking_1": {"creator": "@zachking", "style": "Magic/Visual Effects", "niche": "magic"},
    "therock_2": {"creator": "@therock", "style": "Fitness/Lifestyle", "niche": "fitness"},
    "charlidamelio_3": {"creator": "@charlidamelio", "style": "Dance/Lifestyle", "niche": "dance"},
    "mrbeast_4": {"creator": "@mrbeast", "style": "Entertainment/Stunts", "niche": "entertainment"},
    "willsmith_5": {"creator": "@willsmith", "style": "Comedy/Lifestyle", "niche": "comedy"},
    "garyvee_6": {"creator": "@garyvee", "style": "Business/Motivation", "niche": "business"},
    "jasonderulo_7": {"creator": "@jasonderulo", "style": "Music/Performance", "niche": "music"},
    "dudeperfect_8": {"creator": "@dudeperfect", "style": "Sports/Tricks", "niche": "sports"},
    "natgeo_9": {"creator": "@natgeo", "style": "Nature/Documentary", "niche": "nature"},
}


async def analyze_video(video_path: Path) -> dict:
    """Extract frames and run Qwen3-VL analysis on a single video."""
    frames = extract_frames(str(video_path), max_frames=16)
    if not frames:
        return {"status": "error", "error": "No frames extracted"}

    b64_frames = frames_to_base64(frames)
    result = await analyze_video_frames(b64_frames)
    return result


async def main():
    api_key = os.environ.get("INFERENCE_API_KEY", "")
    if not api_key:
        print("ERROR: Set INFERENCE_API_KEY environment variable")
        sys.exit(1)

    videos = sorted(VIDEOS_DIR.glob("*.mp4"))
    print(f"\n{'='*70}")
    print(f"  Qwen3-VL Reel Analysis — OpenRouter Free (235B MoE)")
    print(f"  Videos: {len(videos)}")
    print(f"{'='*70}")

    all_results = []

    for i, video_path in enumerate(videos):
        stem = video_path.stem
        info = CREATOR_INFO.get(stem, {"creator": stem, "style": "Unknown", "niche": "unknown"})

        print(f"\n[{i+1}/{len(videos)}] {info['creator']} ({info['style']})")
        print(f"  File: {video_path.name} ({video_path.stat().st_size / 1024 / 1024:.1f} MB)")

        try:
            print(f"  Extracting frames...")
            result = await analyze_video(video_path)

            result["creator"] = info["creator"]
            result["style"] = info["style"]
            result["niche"] = info["niche"]
            result["filename"] = video_path.name

            # Save individual result
            result_path = RESULTS_DIR / f"{stem}_result.json"
            with open(result_path, "w") as f:
                json.dump(result, f, indent=2)

            if result.get("status") == "success":
                a = result["analysis"]
                print(f"  Virality: {a.get('virality_score', '?')}/10")
                print(f"  Hook: {a.get('hook_type', '?')} (strength: {a.get('hook_strength', '?')}/10)")
                print(f"  Emotion: {a.get('emotional_trigger', '?')}")
                print(f"  Format: {a.get('content_format', '?')}")
                print(f"  Pacing: {a.get('pacing', '?')}")
            else:
                print(f"  Status: {result.get('status', 'unknown')}")
                print(f"  Raw: {result.get('raw', '')[:200]}")

            all_results.append(result)

        except Exception as e:
            print(f"  ERROR: {e}")
            all_results.append({
                "creator": info["creator"],
                "style": info["style"],
                "status": "error",
                "error": str(e),
            })

        # Rate limit pause for free tier
        if i < len(videos) - 1:
            print(f"  [waiting 8s for rate limit...]")
            time.sleep(8)

    # Save combined results
    combined_path = RESULTS_DIR / "all_results.json"
    with open(combined_path, "w") as f:
        json.dump(all_results, f, indent=2)

    # Print summary
    successful = [r for r in all_results if r.get("status") == "success"]
    print(f"\n{'='*70}")
    print(f"  ANALYSIS COMPLETE: {len(successful)}/{len(all_results)} videos analyzed")
    print(f"  Results saved to: {combined_path}")
    print(f"{'='*70}")

    if successful:
        print(f"\n  {'Creator':<20} {'Virality':>8} {'Hook':>8} {'Emotion':<15} {'Format':<20}")
        print(f"  {'-'*20} {'-'*8} {'-'*8} {'-'*15} {'-'*20}")
        for r in successful:
            a = r["analysis"]
            print(f"  {r['creator']:<20} {a.get('virality_score', '?'):>8} "
                  f"{a.get('hook_strength', '?'):>8} {a.get('emotional_trigger', '?'):<15} "
                  f"{a.get('content_format', '?'):<20}")


if __name__ == "__main__":
    asyncio.run(main())
