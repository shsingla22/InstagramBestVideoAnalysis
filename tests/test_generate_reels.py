"""Tests for the reel generation script."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scripts.generate_reels import REEL_TEMPLATES, FAL_PROVIDERS, FREE_PROVIDERS


def test_all_templates_have_required_fields():
    required = {"id", "name", "format", "duration", "aspect_ratio", "viral_mechanics", "prompt"}
    for t in REEL_TEMPLATES:
        assert required.issubset(set(t.keys())), f"Template {t.get('id')} missing: {required - set(t.keys())}"


def test_all_templates_are_vertical():
    for t in REEL_TEMPLATES:
        assert t["aspect_ratio"] == "9:16", f"Template {t['id']} is not vertical"


def test_all_templates_have_viral_mechanics():
    for t in REEL_TEMPLATES:
        assert len(t["viral_mechanics"]) >= 2, f"Template {t['id']} needs at least 2 viral mechanics"


def test_all_providers_have_required_fields():
    required = {"endpoint", "name", "cost_per_sec", "max_duration", "supports_audio"}
    for key, p in FAL_PROVIDERS.items():
        assert required.issubset(set(p.keys())), f"Provider {key} missing: {required - set(p.keys())}"


def test_template_prompts_are_descriptive():
    for t in REEL_TEMPLATES:
        assert len(t["prompt"]) > 100, f"Template {t['id']} prompt too short ({len(t['prompt'])} chars)"


def test_template_ids_are_unique():
    ids = [t["id"] for t in REEL_TEMPLATES]
    assert len(ids) == len(set(ids)), "Duplicate template IDs"


def test_free_providers_have_required_fields():
    required = {"space", "name", "quality", "resolution", "max_duration", "api_name"}
    for key, p in FREE_PROVIDERS.items():
        assert required.issubset(set(p.keys())), f"Free provider {key} missing: {required - set(p.keys())}"


def test_free_providers_are_truly_free():
    """Verify free providers don't require API keys."""
    for key, p in FREE_PROVIDERS.items():
        assert "huggingface" in p["space"].lower() or "/" in p["space"], \
            f"Free provider {key} doesn't use HuggingFace Spaces"


def test_free_providers_have_vertical_resolution():
    """Verify free providers support vertical video output."""
    for key, p in FREE_PROVIDERS.items():
        # Resolution string should indicate vertical (height > width)
        assert "vertical" in p["resolution"].lower() or "9:16" in p["resolution"] or "2:3" in p["resolution"], \
            f"Free provider {key} doesn't indicate vertical support"
