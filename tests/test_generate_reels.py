"""Tests for the reel generation script."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scripts.generate_reels import REEL_TEMPLATES, FAL_PROVIDERS


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
