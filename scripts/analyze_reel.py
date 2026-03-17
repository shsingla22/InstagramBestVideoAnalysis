#!/usr/bin/env python3
"""Analyze a generated reel using multiple inference providers in parallel.

Usage:
  python3 scripts/analyze_reel.py <video_path> [--providers provider1,provider2,...]

Runs analysis with up to 3 providers simultaneously and produces a merged report.
"""
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server.video_processor import extract_frames, frames_to_base64, get_video_metadata
from server.inference_client import analyze_video_frames
import config


async def analyze_with_provider(b64_frames: list[str], provider: str, api_key: str = "") -> dict:
    """Run analysis with a specific provider."""
    # Temporarily override config
    original_provider = config.INFERENCE_PROVIDER
    original_key = config.INFERENCE_API_KEY

    config.INFERENCE_PROVIDER = provider
    if api_key:
        config.INFERENCE_API_KEY = api_key
    elif provider == "groq":
        config.INFERENCE_API_KEY = os.getenv("GROQ_API_KEY", os.getenv("INFERENCE_API_KEY", ""))
    elif provider == "huggingface":
        config.INFERENCE_API_KEY = os.getenv("HF_TOKEN", os.getenv("INFERENCE_API_KEY", ""))
    else:
        config.INFERENCE_API_KEY = os.getenv("INFERENCE_API_KEY", "")

    # Reload provider config
    try:
        result = await analyze_video_frames(b64_frames)
        result["_provider"] = provider
        return result
    except Exception as e:
        return {"status": "error", "error": str(e), "_provider": provider}
    finally:
        config.INFERENCE_PROVIDER = original_provider
        config.INFERENCE_API_KEY = original_key


async def parallel_analysis(video_path: str, providers: list[str] = None) -> dict:
    """Analyze a video with multiple providers in parallel."""
    if not providers:
        providers = ["openrouter_free", "groq"]

    print(f"\n{'=' * 70}")
    print(f"  PARALLEL REEL ANALYSIS")
    print(f"  Video: {video_path}")
    print(f"  Providers: {', '.join(providers)}")
    print(f"{'=' * 70}")

    # Step 1: Extract frames
    print(f"\n  [1/3] Extracting frames...")
    metadata = get_video_metadata(video_path)
    print(f"  Metadata: {metadata.get('width', '?')}x{metadata.get('height', '?')}, "
          f"{metadata.get('duration_seconds', '?'):.1f}s, {metadata.get('fps', '?'):.0f}fps")

    frames = extract_frames(video_path, max_frames=16)
    if not frames:
        return {"status": "error", "error": "No frames extracted"}
    print(f"  Extracted {len(frames)} frames")

    b64_frames = frames_to_base64(frames)
    print(f"  Encoded {len(b64_frames)} base64 frames")

    # Step 2: Launch parallel analysis
    print(f"\n  [2/3] Launching {len(providers)} parallel analyses...")
    tasks = [analyze_with_provider(b64_frames, p) for p in providers]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Step 3: Collect results
    print(f"\n  [3/3] Collecting results...")
    analyses = {}
    for r in results:
        if isinstance(r, Exception):
            print(f"  ERROR: {r}")
            continue
        provider = r.get("_provider", "unknown")
        status = r.get("status", "unknown")
        print(f"  {provider}: {status}")
        if status == "success":
            analyses[provider] = r.get("analysis", r)
        else:
            print(f"    Error: {r.get('error', 'unknown')[:200]}")

    return {
        "video_path": video_path,
        "metadata": metadata,
        "num_frames": len(frames),
        "analyses": analyses,
        "providers_used": providers,
        "providers_succeeded": list(analyses.keys()),
    }


def print_analysis_summary(report: dict):
    """Print a human-readable summary of the analysis."""
    print(f"\n{'=' * 70}")
    print(f"  ANALYSIS REPORT")
    print(f"{'=' * 70}")

    for provider, analysis in report.get("analyses", {}).items():
        print(f"\n{'─' * 70}")
        print(f"  Provider: {provider}")
        print(f"{'─' * 70}")

        # Virality
        va = analysis.get("virality_assessment", {})
        print(f"  Virality Score: {va.get('virality_score', '?')}/10")
        print(f"  Virality Ceiling: {va.get('virality_ceiling', '?')}")

        # Hook
        ha = analysis.get("hook_analysis", {})
        print(f"  Hook Strength: {ha.get('hook_strength', '?')}/10 ({ha.get('hook_type', '?')})")
        print(f"  Thumb-Stop Rate: {ha.get('thumb_stop_rate_estimate', '?')}")

        # Visual
        vc = analysis.get("visual_cinematography", {})
        print(f"  Visual Quality: {vc.get('visual_quality_score', '?')}/10")
        print(f"  Production Value: {vc.get('production_value', '?')}")
        print(f"  Color Palette: {vc.get('color_palette', '?')}")

        # Structure
        cs = analysis.get("content_structure", {})
        print(f"  Format: {cs.get('content_format', '?')}")
        print(f"  Narrative Arc: {cs.get('narrative_arc', '?')}")
        print(f"  Completion Likelihood: {cs.get('completion_likelihood', '?')}")
        print(f"  Rewatch Value: {cs.get('rewatch_value', '?')}")

        # Psychology
        pt = analysis.get("psychological_triggers", {})
        print(f"  Primary Emotion: {pt.get('primary_emotion', '?')}")
        print(f"  Share Trigger: {pt.get('share_trigger', '?')}")
        print(f"  Save Trigger: {pt.get('save_trigger', '?')}")

        # Improvements
        improvements = analysis.get("actionable_improvements", [])
        if improvements:
            print(f"\n  TOP IMPROVEMENTS:")
            for imp in improvements[:3]:
                if isinstance(imp, dict):
                    print(f"    [{imp.get('priority', '?')}] {imp.get('area', '?')}: {imp.get('specific_fix', '?')[:100]}")

        # Expert summary
        summary = analysis.get("expert_summary", "")
        if summary:
            print(f"\n  EXPERT SUMMARY:")
            # Word-wrap at ~80 chars
            words = summary.split()
            line = "    "
            for w in words:
                if len(line) + len(w) > 78:
                    print(line)
                    line = "    "
                line += w + " "
            if line.strip():
                print(line)


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Analyze a reel with multiple providers")
    parser.add_argument("video_path", help="Path to the video file")
    parser.add_argument("--providers", default="openrouter_free,groq",
                        help="Comma-separated list of providers")
    parser.add_argument("--output", help="Save JSON report to this path")
    args = parser.parse_args()

    providers = [p.strip() for p in args.providers.split(",")]

    report = await parallel_analysis(args.video_path, providers)
    print_analysis_summary(report)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n  Report saved: {args.output}")

    return report


if __name__ == "__main__":
    asyncio.run(main())
