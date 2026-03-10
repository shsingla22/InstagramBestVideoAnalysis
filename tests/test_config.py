"""Tests for configuration module."""

import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (
    BASE_DIR,
    DATA_DIR,
    INSTAGRAM_CREATORS,
    RESULTS_DIR,
    VIDEOS_DIR,
    VLLM_MODEL_NAME,
    VIDEO_ANALYSIS_PROMPT,
)


def test_directories_exist():
    assert DATA_DIR.exists()
    assert VIDEOS_DIR.exists()
    assert RESULTS_DIR.exists()


def test_model_name():
    assert "Qwen" in VLLM_MODEL_NAME


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
