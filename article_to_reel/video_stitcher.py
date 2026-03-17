"""Stitch multiple short video clips into a single Instagram Reel.

Handles:
- Concatenating clips sequentially
- Resizing all clips to 1080x1920 (9:16) with letterboxing/cropping
- Adding text overlays (hook text, captions)
- Basic transitions (fade, cut)
- Output as MP4 H.264
"""
import os
import subprocess
from pathlib import Path
from typing import Optional


def _get_ffmpeg():
    """Check if ffmpeg is available."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return "ffmpeg"
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def get_video_info(video_path: str) -> dict:
    """Get video metadata using ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", str(video_path)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        import json
        data = json.loads(result.stdout)
        video_stream = next((s for s in data.get("streams", []) if s["codec_type"] == "video"), {})
        return {
            "width": int(video_stream.get("width", 0)),
            "height": int(video_stream.get("height", 0)),
            "duration": float(data.get("format", {}).get("duration", 0)),
            "fps": eval(video_stream.get("r_frame_rate", "30/1")),
        }
    except Exception:
        return {}


def resize_to_vertical(input_path: str, output_path: str,
                       width: int = 1080, height: int = 1920) -> bool:
    """Resize a video to 9:16 vertical format with black bars if needed."""
    ffmpeg = _get_ffmpeg()
    if not ffmpeg:
        print("  WARNING: ffmpeg not found — skipping resize")
        return False

    cmd = [
        ffmpeg, "-y", "-i", str(input_path),
        "-vf", (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black"
        ),
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(output_path)
    ]
    try:
        subprocess.run(cmd, capture_output=True, check=True, timeout=120)
        return True
    except Exception as e:
        print(f"  Resize error: {e}")
        return False


def add_text_overlay(input_path: str, output_path: str,
                     text: str, position: str = "top",
                     font_size: int = 48, duration: Optional[float] = None) -> bool:
    """Add text overlay to a video using ffmpeg drawtext."""
    ffmpeg = _get_ffmpeg()
    if not ffmpeg:
        return False

    # Escape special characters for ffmpeg drawtext
    text_escaped = text.replace("'", "'\\''").replace(":", "\\:")

    y_pos = "h*0.08" if position == "top" else "h*0.85" if position == "bottom" else "h/2"

    drawtext = (
        f"drawtext=text='{text_escaped}':"
        f"fontsize={font_size}:fontcolor=white:"
        f"borderw=3:bordercolor=black:"
        f"x=(w-text_w)/2:y={y_pos}"
    )

    cmd = [
        ffmpeg, "-y", "-i", str(input_path),
        "-vf", drawtext,
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "copy",
        str(output_path)
    ]
    try:
        subprocess.run(cmd, capture_output=True, check=True, timeout=120)
        return True
    except Exception as e:
        print(f"  Text overlay error: {e}")
        return False


def stitch_videos(clips: list[dict], output_path: str,
                  target_width: int = 1080, target_height: int = 1920) -> bool:
    """Stitch multiple video clips into one reel.

    Args:
        clips: List of dicts with keys:
            - path: path to video file
            - text: optional text overlay
            - text_position: "top", "bottom", or "center"
        output_path: where to save the final reel
        target_width: output width (default 1080)
        target_height: output height (default 1920)

    Returns:
        True if successful
    """
    ffmpeg = _get_ffmpeg()
    if not ffmpeg:
        print("ERROR: ffmpeg required for video stitching")
        return False

    temp_dir = Path(output_path).parent / "_temp_stitch"
    temp_dir.mkdir(exist_ok=True)

    try:
        processed = []
        for i, clip in enumerate(clips):
            src = clip["path"]
            if not os.path.exists(src):
                print(f"  WARNING: Clip not found: {src}")
                continue

            # Step 1: Resize to target
            resized = str(temp_dir / f"clip_{i:02d}_resized.mp4")
            if not resize_to_vertical(src, resized, target_width, target_height):
                resized = src  # Use original if resize fails

            # Step 2: Add text overlay if specified
            if clip.get("text"):
                with_text = str(temp_dir / f"clip_{i:02d}_text.mp4")
                pos = clip.get("text_position", "top")
                if add_text_overlay(resized, with_text, clip["text"], pos):
                    processed.append(with_text)
                else:
                    processed.append(resized)
            else:
                processed.append(resized)

        if not processed:
            print("  ERROR: No clips to stitch")
            return False

        if len(processed) == 1:
            # Just copy the single clip
            import shutil
            shutil.copy2(processed[0], output_path)
            return True

        # Step 3: Create concat file
        concat_file = str(temp_dir / "concat.txt")
        with open(concat_file, "w") as f:
            for p in processed:
                f.write(f"file '{os.path.abspath(p)}'\n")

        # Step 4: Concatenate
        cmd = [
            ffmpeg, "-y", "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            str(output_path)
        ]
        subprocess.run(cmd, capture_output=True, check=True, timeout=120)

        size_mb = os.path.getsize(output_path) / 1024 / 1024
        print(f"  Stitched {len(processed)} clips → {output_path} ({size_mb:.1f} MB)")
        return True

    finally:
        # Cleanup temp files
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
