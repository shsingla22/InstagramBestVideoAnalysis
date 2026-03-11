#!/usr/bin/env python3
"""Run expert-level Qwen3-VL video analysis on all downloaded sample videos.

Produces deep analysis covering cinematography, psychology, platform optimization,
and actionable improvements — far beyond simple virality scoring.
"""

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

# Creator metadata for the 10 pre-downloaded videos
CREATOR_INFO = {
    "khaby_lame_0": {
        "creator": "@khaby.lame",
        "style": "Comedy/Reaction",
        "niche": "comedy",
        "followers_at_time": "162M",
        "category": "famous_baseline",
    },
    "zachking_1": {
        "creator": "@zachking",
        "style": "Magic/Visual Effects",
        "niche": "magic",
        "followers_at_time": "79M",
        "category": "famous_baseline",
    },
    "therock_2": {
        "creator": "@therock",
        "style": "Fitness/Lifestyle",
        "niche": "fitness",
        "followers_at_time": "400M",
        "category": "famous_baseline",
    },
    "charlidamelio_3": {
        "creator": "@charlidamelio",
        "style": "Dance/Lifestyle",
        "niche": "dance",
        "followers_at_time": "56M",
        "category": "famous_baseline",
    },
    "mrbeast_4": {
        "creator": "@mrbeast",
        "style": "Entertainment/Stunts",
        "niche": "entertainment",
        "followers_at_time": "48M",
        "category": "famous_baseline",
    },
    "willsmith_5": {
        "creator": "@willsmith",
        "style": "Comedy/Lifestyle",
        "niche": "comedy",
        "followers_at_time": "75M",
        "category": "famous_baseline",
    },
    "garyvee_6": {
        "creator": "@garyvee",
        "style": "Business/Motivation",
        "niche": "business",
        "followers_at_time": "20M",
        "category": "famous_baseline",
    },
    "jasonderulo_7": {
        "creator": "@jasonderulo",
        "style": "Music/Performance",
        "niche": "music",
        "followers_at_time": "62M",
        "category": "famous_baseline",
    },
    "dudeperfect_8": {
        "creator": "@dudeperfect",
        "style": "Sports/Tricks",
        "niche": "sports",
        "followers_at_time": "22M",
        "category": "famous_baseline",
    },
    "natgeo_9": {
        "creator": "@natgeo",
        "style": "Nature/Documentary",
        "niche": "nature",
        "followers_at_time": "284M",
        "category": "famous_baseline",
    },
}


async def analyze_video(video_path: Path) -> dict:
    """Extract frames and run expert-level analysis on a single video."""
    frames = extract_frames(str(video_path), max_frames=16)
    if not frames:
        return {"status": "error", "error": "No frames extracted"}

    b64_frames = frames_to_base64(frames)
    result = await analyze_video_frames(b64_frames)
    return result


def print_expert_summary(result: dict, info: dict):
    """Print a rich summary of the expert analysis."""
    if result.get("status") != "success":
        print(f"  Status: {result.get('status', 'unknown')}")
        if result.get("raw"):
            print(f"  Raw (first 300 chars): {result['raw'][:300]}")
        return

    a = result["analysis"]

    # Hook analysis
    hook = a.get("hook_analysis", {})
    print(f"\n  HOOK ANALYSIS:")
    print(f"    Type: {hook.get('hook_type', 'N/A')}")
    print(f"    Strength: {hook.get('hook_strength', 'N/A')}/10")
    print(f"    First Frame: {hook.get('first_frame_impression', 'N/A')}")
    print(f"    Thumb-Stop: {hook.get('thumb_stop_rate_estimate', 'N/A')}")

    # Visual
    vis = a.get("visual_cinematography", {})
    print(f"\n  CINEMATOGRAPHY:")
    print(f"    Camera: {vis.get('camera_movement', 'N/A')} | Lighting: {vis.get('lighting_style', 'N/A')}")
    print(f"    Colors: {vis.get('color_palette', 'N/A')}")
    print(f"    Production: {vis.get('production_value', 'N/A')} | Quality: {vis.get('visual_quality_score', 'N/A')}/10")

    # Editing
    edit = a.get("editing_and_pacing", {})
    print(f"\n  EDITING:")
    print(f"    Style: {edit.get('editing_style', 'N/A')} | Pacing: {edit.get('pacing', 'N/A')}")
    print(f"    Scene changes: {edit.get('scene_changes_count', 'N/A')} | Avg shot: {edit.get('average_shot_duration_seconds', 'N/A')}s")

    # Content
    content = a.get("content_structure", {})
    print(f"\n  CONTENT:")
    print(f"    Format: {content.get('content_format', 'N/A')}")
    print(f"    Narrative: {content.get('narrative_arc', 'N/A')}")
    print(f"    Rewatch: {content.get('rewatch_value', 'N/A')} | Completion: {content.get('completion_likelihood', 'N/A')}")

    # Psychology
    psych = a.get("psychological_triggers", {})
    print(f"\n  PSYCHOLOGY:")
    print(f"    Primary emotion: {psych.get('primary_emotion', 'N/A')}")
    print(f"    Share trigger: {psych.get('share_trigger', 'N/A')}")
    print(f"    Save trigger: {psych.get('save_trigger', 'N/A')}")
    print(f"    Comment bait: {psych.get('comment_bait', 'N/A')}")
    biases = psych.get("cognitive_bias_exploited", [])
    if biases:
        print(f"    Biases exploited: {', '.join(biases)}")

    # Virality
    viral = a.get("virality_assessment", {})
    print(f"\n  VIRALITY VERDICT:")
    print(f"    Score: {viral.get('virality_score', 'N/A')}/10")
    print(f"    Ceiling: {viral.get('virality_ceiling', 'N/A')}")
    factors = viral.get("virality_factors", [])
    for f in factors[:3]:
        print(f"    + {f}")
    blockers = viral.get("virality_blockers", [])
    for b in blockers[:2]:
        print(f"    - {b}")

    # Top improvements
    improvements = a.get("actionable_improvements", [])
    if improvements:
        print(f"\n  TOP IMPROVEMENTS:")
        for imp in improvements[:3]:
            if isinstance(imp, dict):
                print(f"    [{imp.get('priority', '?').upper()}] {imp.get('area', '?')}: {imp.get('specific_fix', 'N/A')}")
            else:
                print(f"    - {imp}")

    # Expert summary
    summary = a.get("expert_summary", "")
    if summary:
        print(f"\n  EXPERT VERDICT:")
        # Word-wrap at ~80 chars
        words = summary.split()
        line = "    "
        for w in words:
            if len(line) + len(w) + 1 > 85:
                print(line)
                line = "    " + w
            else:
                line += " " + w if line.strip() else "    " + w
        if line.strip():
            print(line)


async def main():
    api_key = os.environ.get("INFERENCE_API_KEY", "")
    if not api_key:
        print("ERROR: Set INFERENCE_API_KEY environment variable")
        print("  For free analysis: export INFERENCE_PROVIDER=openrouter_free")
        print("  Get key at: https://openrouter.ai (free signup)")
        sys.exit(1)

    videos = sorted(VIDEOS_DIR.glob("*.mp4"))
    provider = os.environ.get("INFERENCE_PROVIDER", "openrouter_free")

    print(f"\n{'='*80}")
    print(f"  EXPERT VIDEO ANALYSIS — Instagram Reel Virality Deep Dive")
    print(f"  Provider: {provider}")
    print(f"  Videos: {len(videos)}")
    print(f"  Analysis depth: Expert (cinematography, psychology, platform optimization)")
    print(f"{'='*80}")

    all_results = []

    for i, video_path in enumerate(videos):
        stem = video_path.stem
        info = CREATOR_INFO.get(stem, {
            "creator": stem,
            "style": "Unknown",
            "niche": "unknown",
            "followers_at_time": "unknown",
            "category": "unknown",
        })

        print(f"\n{'─'*80}")
        print(f"  [{i+1}/{len(videos)}] {info['creator']} ({info['style']})")
        print(f"  File: {video_path.name} ({video_path.stat().st_size / 1024 / 1024:.1f} MB)")
        print(f"  Category: {info.get('category', 'unknown')} | Followers: {info.get('followers_at_time', '?')}")
        print(f"{'─'*80}")

        try:
            print(f"  Extracting 16 frames...")
            result = await analyze_video(video_path)

            result["creator"] = info["creator"]
            result["style"] = info["style"]
            result["niche"] = info["niche"]
            result["category"] = info.get("category", "unknown")
            result["followers_at_time"] = info.get("followers_at_time", "unknown")
            result["filename"] = video_path.name

            # Save individual result
            result_path = RESULTS_DIR / f"{stem}_result.json"
            with open(result_path, "w") as f:
                json.dump(result, f, indent=2)

            print_expert_summary(result, info)
            all_results.append(result)

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            all_results.append({
                "creator": info["creator"],
                "style": info["style"],
                "status": "error",
                "error": str(e),
            })

        # Rate limit pause for free tier
        if i < len(videos) - 1:
            wait = 10 if provider in ("openrouter_free", "huggingface", "groq") else 2
            print(f"\n  [waiting {wait}s for rate limit...]")
            time.sleep(wait)

    # Save combined results
    combined_path = RESULTS_DIR / "all_results.json"
    with open(combined_path, "w") as f:
        json.dump(all_results, f, indent=2)

    # Print comparison table
    successful = [r for r in all_results if r.get("status") == "success"]
    print(f"\n{'='*80}")
    print(f"  ANALYSIS COMPLETE: {len(successful)}/{len(all_results)} videos analyzed")
    print(f"  Results saved to: {combined_path}")
    print(f"{'='*80}")

    if successful:
        print(f"\n  VIRALITY RANKING:")
        print(f"  {'#':<4} {'Creator':<18} {'Score':>6} {'Hook':>6} {'Emotion':<14} {'Format':<18} {'Ceiling':<16}")
        print(f"  {'─'*4} {'─'*18} {'─'*6} {'─'*6} {'─'*14} {'─'*18} {'─'*16}")

        # Sort by virality score descending
        ranked = sorted(successful, key=lambda r: (
            r.get("analysis", {}).get("virality_assessment", {}).get("virality_score", 0)
            if isinstance(r.get("analysis", {}).get("virality_assessment", {}).get("virality_score", 0), (int, float))
            else 0
        ), reverse=True)

        for rank, r in enumerate(ranked, 1):
            a = r.get("analysis", {})
            viral = a.get("virality_assessment", {})
            hook = a.get("hook_analysis", {})
            psych = a.get("psychological_triggers", {})
            content = a.get("content_structure", {})
            print(
                f"  {rank:<4} {r['creator']:<18} "
                f"{viral.get('virality_score', '?'):>6} "
                f"{hook.get('hook_strength', '?'):>6} "
                f"{psych.get('primary_emotion', '?'):<14} "
                f"{content.get('content_format', '?'):<18} "
                f"{viral.get('virality_ceiling', '?'):<16}"
            )

        # Cross-video insights
        print(f"\n  CROSS-VIDEO INSIGHTS:")
        emotions = [r["analysis"].get("psychological_triggers", {}).get("primary_emotion", "")
                     for r in successful if r.get("analysis")]
        formats = [r["analysis"].get("content_structure", {}).get("content_format", "")
                    for r in successful if r.get("analysis")]
        print(f"    Most common emotion: {max(set(emotions), key=emotions.count) if emotions else 'N/A'}")
        print(f"    Most common format: {max(set(formats), key=formats.count) if formats else 'N/A'}")

        scores = [r["analysis"].get("virality_assessment", {}).get("virality_score", 0)
                   for r in successful
                   if isinstance(r.get("analysis", {}).get("virality_assessment", {}).get("virality_score", 0), (int, float))]
        if scores:
            print(f"    Avg virality score: {sum(scores)/len(scores):.1f}/10")
            print(f"    Score range: {min(scores)}-{max(scores)}/10")


if __name__ == "__main__":
    asyncio.run(main())
