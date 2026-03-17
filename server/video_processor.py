"""Extract and preprocess frames from video files for Qwen3-VL inference."""

import base64
import io
import logging
from pathlib import Path

import cv2
from PIL import Image

from config import FRAME_RESIZE, MAX_FRAMES_PER_VIDEO

logger = logging.getLogger(__name__)


def extract_frames(video_path: str | Path, max_frames: int = MAX_FRAMES_PER_VIDEO) -> list[Image.Image]:
    """Extract evenly-spaced frames from a video file.

    Returns a list of PIL Images resized to FRAME_RESIZE.
    """
    video_path = str(video_path)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    duration = total_frames / fps

    if total_frames <= 0:
        raise ValueError(f"Video has no frames: {video_path}")

    # Pick evenly spaced frame indices
    if total_frames <= max_frames:
        indices = list(range(total_frames))
    else:
        step = total_frames / max_frames
        indices = [int(step * i) for i in range(max_frames)]

    frames: list[Image.Image] = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue
        # BGR -> RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb).resize(FRAME_RESIZE, Image.LANCZOS)
        frames.append(img)

    cap.release()
    logger.info("Extracted %d frames from %s (%.1fs @ %.1f fps)", len(frames), video_path, duration, fps)
    return frames


def frames_to_base64(frames: list[Image.Image]) -> list[str]:
    """Convert PIL Images to base64-encoded JPEG strings."""
    encoded: list[str] = []
    for frame in frames:
        buf = io.BytesIO()
        frame.save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        encoded.append(b64)
    return encoded


def get_video_metadata(video_path: str | Path) -> dict:
    """Return basic metadata about a video file."""
    video_path = str(video_path)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / fps if fps > 0 else 0
    cap.release()

    return {
        "total_frames": total_frames,
        "fps": round(fps, 2),
        "width": width,
        "height": height,
        "duration_seconds": round(duration, 2),
        "file_size_mb": round(Path(video_path).stat().st_size / (1024 * 1024), 2),
    }
