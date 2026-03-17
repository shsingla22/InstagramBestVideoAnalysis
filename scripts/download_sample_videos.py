#!/usr/bin/env python3
"""Download free sample videos from Mixkit representing different creator styles.

Mixkit provides royalty-free videos with no API key or signup required.
Each video is chosen to match the content style of a top Instagram creator.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import VIDEOS_DIR

import httpx

# Mixkit free videos - each chosen to match a creator's content style
# Format: https://assets.mixkit.co/videos/{id}/{id}-720.mp4
SAMPLE_VIDEOS = [
    {
        "creator": "khaby_lame",
        "style": "Comedy/Reaction",
        "description": "Man with exaggerated surprised expression - comedy reaction style",
        "url": "https://assets.mixkit.co/videos/34563/34563-720.mp4",
    },
    {
        "creator": "zachking",
        "style": "Magic/Visual Effects",
        "description": "Creative visual effects and colorful light painting",
        "url": "https://assets.mixkit.co/videos/34110/34110-720.mp4",
    },
    {
        "creator": "therock",
        "style": "Fitness/Lifestyle",
        "description": "Intense gym workout with weights and determination",
        "url": "https://assets.mixkit.co/videos/18530/18530-720.mp4",
    },
    {
        "creator": "charlidamelio",
        "style": "Dance/Lifestyle",
        "description": "Woman dancing with energetic moves in neon lights",
        "url": "https://assets.mixkit.co/videos/34011/34011-720.mp4",
    },
    {
        "creator": "mrbeast",
        "style": "Entertainment/Stunts",
        "description": "Group of friends celebrating and having fun together",
        "url": "https://assets.mixkit.co/videos/3205/3205-720.mp4",
    },
    {
        "creator": "willsmith",
        "style": "Comedy/Lifestyle",
        "description": "Man talking to camera with animated personality",
        "url": "https://assets.mixkit.co/videos/42382/42382-720.mp4",
    },
    {
        "creator": "garyvee",
        "style": "Business/Motivation",
        "description": "Entrepreneur giving a passionate speech at event",
        "url": "https://assets.mixkit.co/videos/32842/32842-720.mp4",
    },
    {
        "creator": "jasonderulo",
        "style": "Music/Performance",
        "description": "Live music performance with stage lighting",
        "url": "https://assets.mixkit.co/videos/510/510-720.mp4",
    },
    {
        "creator": "dudeperfect",
        "style": "Sports/Tricks",
        "description": "Basketball player making an amazing trick shot",
        "url": "https://assets.mixkit.co/videos/1170/1170-720.mp4",
    },
    {
        "creator": "natgeo",
        "style": "Nature/Documentary",
        "description": "Stunning wildlife in natural habitat with cinematic quality",
        "url": "https://assets.mixkit.co/videos/28389/28389-720.mp4",
    },
]


def download_video(url: str, filepath: str) -> bool:
    """Download a video file with streaming."""
    try:
        with httpx.Client(verify=False, timeout=120, follow_redirects=True) as client:
            with client.stream("GET", url) as resp:
                resp.raise_for_status()
                with open(filepath, "wb") as f:
                    for chunk in resp.iter_bytes(65536):
                        f.write(chunk)
        return True
    except Exception as e:
        print(f"  [error] {e}")
        if os.path.exists(filepath):
            os.unlink(filepath)
        return False


def main():
    print(f"Downloading {len(SAMPLE_VIDEOS)} sample videos to {VIDEOS_DIR}")
    print("=" * 60)

    success = 0
    for i, video in enumerate(SAMPLE_VIDEOS):
        filename = f"{video['creator']}_{i}.mp4"
        filepath = VIDEOS_DIR / filename
        print(f"\n[{i+1}/{len(SAMPLE_VIDEOS)}] {video['creator']} ({video['style']})")
        print(f"  {video['description']}")

        if filepath.exists() and filepath.stat().st_size > 10000:
            print(f"  [skip] Already downloaded ({filepath.stat().st_size / 1024 / 1024:.1f} MB)")
            success += 1
            continue

        print(f"  [download] {filename}...")
        if download_video(video["url"], str(filepath)):
            size_mb = filepath.stat().st_size / (1024 * 1024)
            print(f"  [ok] {filename} ({size_mb:.1f} MB)")
            success += 1
        else:
            print(f"  [fail] Could not download")

    print(f"\n{'=' * 60}")
    print(f"Downloaded {success}/{len(SAMPLE_VIDEOS)} videos successfully")


if __name__ == "__main__":
    main()
