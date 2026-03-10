"""Tests for the video processor module."""

import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _create_test_video(path: str, frames: int = 30, fps: float = 30.0):
    """Create a minimal test video with solid-color frames."""
    import cv2
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(path, fourcc, fps, (320, 240))
    for i in range(frames):
        color = ((i * 8) % 256, (i * 4) % 256, (255 - i * 3) % 256)
        frame = np.full((240, 320, 3), color, dtype=np.uint8)
        writer.write(frame)
    writer.release()


@pytest.fixture
def test_video(tmp_path):
    path = str(tmp_path / "test.mp4")
    _create_test_video(path, frames=60, fps=30.0)
    return path


def test_extract_frames(test_video):
    from server.video_processor import extract_frames
    frames = extract_frames(test_video, max_frames=8)
    assert len(frames) == 8
    # Each frame should be a PIL Image at the configured size
    from config import FRAME_RESIZE
    for f in frames:
        assert f.size == FRAME_RESIZE


def test_extract_all_frames_short_video(tmp_path):
    path = str(tmp_path / "short.mp4")
    _create_test_video(path, frames=5, fps=30.0)
    from server.video_processor import extract_frames
    frames = extract_frames(path, max_frames=16)
    assert len(frames) == 5


def test_frames_to_base64(test_video):
    from server.video_processor import extract_frames, frames_to_base64
    frames = extract_frames(test_video, max_frames=4)
    encoded = frames_to_base64(frames)
    assert len(encoded) == 4
    import base64
    for b64 in encoded:
        data = base64.b64decode(b64)
        assert data[:2] == b"\xff\xd8"  # JPEG magic bytes


def test_get_video_metadata(test_video):
    from server.video_processor import get_video_metadata
    meta = get_video_metadata(test_video)
    assert meta["total_frames"] == 60
    assert meta["width"] == 320
    assert meta["height"] == 240
    assert meta["duration_seconds"] > 0
    assert meta["file_size_mb"] > 0


def test_invalid_video():
    from server.video_processor import extract_frames
    with pytest.raises(ValueError, match="Cannot open"):
        extract_frames("/nonexistent/video.mp4")
