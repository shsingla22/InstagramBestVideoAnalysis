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


def test_parse_thinking_model_output():
    """Test parsing output from thinking models that include <think> blocks."""
    raw = '<think>\nLet me analyze this video carefully...\nThe hook seems strong.\n</think>\n{"virality_score": 7, "hook_type": "curiosity gap"}'
    result = _parse_analysis(raw)
    assert result["status"] == "success"
    assert result["analysis"]["virality_score"] == 7
    assert result["analysis"]["hook_type"] == "curiosity gap"


def test_parse_json_with_surrounding_text():
    """Test parsing JSON embedded in surrounding text."""
    raw = 'Here is my analysis:\n{"virality_score": 6}\nEnd of analysis.'
    result = _parse_analysis(raw)
    assert result["status"] == "success"
    assert result["analysis"]["virality_score"] == 6


def test_parse_nested_json():
    """Test parsing deeply nested JSON like the expert analysis format."""
    raw = '{"hook_analysis": {"hook_type": "pattern interrupt", "hook_strength": 8}, "virality_assessment": {"virality_score": 7}}'
    result = _parse_analysis(raw)
    assert result["status"] == "success"
    assert result["analysis"]["hook_analysis"]["hook_type"] == "pattern interrupt"
    assert result["analysis"]["virality_assessment"]["virality_score"] == 7
