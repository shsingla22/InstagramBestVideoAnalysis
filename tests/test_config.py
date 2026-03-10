"""Tests for configuration module."""

import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (
    BASE_DIR,
    DATA_DIR,
    INFERENCE_PROVIDER,
    INSTAGRAM_CREATORS,
    PROVIDERS,
    RESULTS_DIR,
    VIDEOS_DIR,
    VIDEO_ANALYSIS_PROMPT,
    get_provider_config,
)


def test_directories_exist():
    assert DATA_DIR.exists()
    assert VIDEOS_DIR.exists()
    assert RESULTS_DIR.exists()


def test_provider_config():
    cfg = get_provider_config()
    assert "base_url" in cfg
    assert "model" in cfg
    assert "api_key" in cfg
    assert "supports_video_url" in cfg


def test_all_providers_defined():
    for name in ("vllm", "fireworks", "together", "openrouter", "dashscope"):
        assert name in PROVIDERS


def test_creators_list():
    assert len(INSTAGRAM_CREATORS) >= 10
    for c in INSTAGRAM_CREATORS:
        assert "handle" in c
        assert "niche" in c
        assert c["handle"].startswith("@")


def test_analysis_prompt_contains_json_keys():
    assert "virality_score" in VIDEO_ANALYSIS_PROMPT
    assert "hook_type" in VIDEO_ANALYSIS_PROMPT
    assert "emotional_trigger" in VIDEO_ANALYSIS_PROMPT
