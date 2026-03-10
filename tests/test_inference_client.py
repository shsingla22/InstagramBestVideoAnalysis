"""Tests for the inference client module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server.inference_client import _parse_analysis


def test_parse_valid_json():
    raw = '{"virality_score": 8, "hook_type": "pattern interrupt"}'
    result = _parse_analysis(raw)
    assert result["status"] == "success"
    assert result["analysis"]["virality_score"] == 8


def test_parse_json_with_code_fences():
    raw = '```json\n{"virality_score": 5}\n```'
    result = _parse_analysis(raw)
    assert result["status"] == "success"
    assert result["analysis"]["virality_score"] == 5


def test_parse_invalid_json():
    raw = "This is not JSON at all"
    result = _parse_analysis(raw)
    assert result["status"] == "partial"
    assert result["analysis"] is None
    assert result["raw"] == raw


def test_parse_empty_string():
    result = _parse_analysis("")
    assert result["status"] == "partial"
