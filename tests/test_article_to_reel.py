"""Tests for the article_to_reel module."""

import json
from pathlib import Path

import pytest

# Module paths
MODULE_DIR = Path(__file__).resolve().parent.parent / "article_to_reel"
PROMPTS_DIR = MODULE_DIR / "prompts"
PLAYBOOK_PATH = Path(__file__).resolve().parent.parent / "VIRAL_REELS_PLAYBOOK.md"


class TestModuleStructure:
    """Verify the module has all required files."""

    def test_module_init_exists(self):
        assert (MODULE_DIR / "__init__.py").exists()

    def test_module_main_exists(self):
        assert (MODULE_DIR / "__main__.py").exists()

    def test_pipeline_exists(self):
        assert (MODULE_DIR / "pipeline.py").exists()

    def test_article_scraper_exists(self):
        assert (MODULE_DIR / "article_scraper.py").exists()

    def test_prompt_generator_exists(self):
        assert (MODULE_DIR / "prompt_generator.py").exists()

    def test_video_generator_exists(self):
        assert (MODULE_DIR / "video_generator.py").exists()

    def test_prompts_directory_exists(self):
        assert PROMPTS_DIR.exists()
        assert PROMPTS_DIR.is_dir()


class TestPromptFiles:
    """Validate the per-article prompt files."""

    def test_cafe_racer_prompt_exists(self):
        path = PROMPTS_DIR / "the-cafe-racer-how-coffee-gave-birth-to-motorcycle-culture.json"
        assert path.exists()

    def test_cafe_racer_prompt_valid_json(self):
        path = PROMPTS_DIR / "the-cafe-racer-how-coffee-gave-birth-to-motorcycle-culture.json"
        with open(path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_cafe_racer_prompt_has_required_fields(self):
        path = PROMPTS_DIR / "the-cafe-racer-how-coffee-gave-birth-to-motorcycle-culture.json"
        with open(path) as f:
            data = json.load(f)

        required_top = ["article_title", "viral_kernel", "format_choice",
                        "reel_concept", "video_prompt", "virality_scorecard"]
        for field in required_top:
            assert field in data, f"Missing top-level field: {field}"

    def test_cafe_racer_viral_kernel(self):
        path = PROMPTS_DIR / "the-cafe-racer-how-coffee-gave-birth-to-motorcycle-culture.json"
        with open(path) as f:
            data = json.load(f)

        kernel = data["viral_kernel"]
        assert "core_idea" in kernel
        assert "why_viral" in kernel
        assert "emotional_trigger" in kernel
        assert kernel["emotional_trigger"] in [
            "humor", "awe", "curiosity", "nostalgia", "inspiration", "satisfaction"
        ]

    def test_cafe_racer_video_prompt_complete(self):
        path = PROMPTS_DIR / "the-cafe-racer-how-coffee-gave-birth-to-motorcycle-culture.json"
        with open(path) as f:
            data = json.load(f)

        vp = data["video_prompt"]
        assert "main_prompt" in vp
        assert len(vp["main_prompt"]) > 200, "Video prompt should be detailed"
        assert "style_keywords" in vp
        assert "negative_prompt" in vp
        assert "technical_spec" in vp
        assert vp["technical_spec"]["aspect_ratio"] == "9:16"

    def test_cafe_racer_virality_scores(self):
        path = PROMPTS_DIR / "the-cafe-racer-how-coffee-gave-birth-to-motorcycle-culture.json"
        with open(path) as f:
            data = json.load(f)

        scorecard = data["virality_scorecard"]
        assert "overall_virality" in scorecard
        assert scorecard["overall_virality"] >= 7, "Overall virality should be 7+"

        # At least 6 metrics should be 7+
        scores_7plus = 0
        for key, val in scorecard.items():
            if key == "overall_virality":
                continue
            if isinstance(val, dict) and val.get("score", 0) >= 7:
                scores_7plus += 1
        assert scores_7plus >= 6, f"Only {scores_7plus} metrics scored 7+ (need 6+)"

    def test_cafe_racer_has_short_form_prompt(self):
        path = PROMPTS_DIR / "the-cafe-racer-how-coffee-gave-birth-to-motorcycle-culture.json"
        with open(path) as f:
            data = json.load(f)

        assert "short_form_prompt" in data
        sfp = data["short_form_prompt"]
        assert "main_prompt" in sfp
        assert len(sfp["main_prompt"]) > 100

    def test_cafe_racer_has_hook_text(self):
        path = PROMPTS_DIR / "the-cafe-racer-how-coffee-gave-birth-to-motorcycle-culture.json"
        with open(path) as f:
            data = json.load(f)

        hook = data["reel_concept"]["hook_text"]
        assert len(hook) > 0
        assert len(hook.split()) <= 10, "Hook text should be concise (<=10 words)"


class TestPromptGenerator:
    """Test the prompt generator module imports and config."""

    def test_load_playbook(self):
        from article_to_reel.prompt_generator import load_playbook
        playbook = load_playbook()
        assert len(playbook) > 1000
        assert "Viral Instagram Reels Playbook" in playbook

    def test_system_prompt_exists(self):
        from article_to_reel.prompt_generator import SYSTEM_PROMPT
        assert len(SYSTEM_PROMPT) > 100
        assert "creative director" in SYSTEM_PROMPT.lower()

    def test_generation_prompt_template(self):
        from article_to_reel.prompt_generator import GENERATION_PROMPT_TEMPLATE
        assert "{playbook}" in GENERATION_PROMPT_TEMPLATE
        assert "{title}" in GENERATION_PROMPT_TEMPLATE
        assert "{article_body}" in GENERATION_PROMPT_TEMPLATE

    def test_extract_json_from_markdown(self):
        from article_to_reel.prompt_generator import _extract_json
        text = '```json\n{"key": "value"}\n```'
        result = _extract_json(text)
        assert result == {"key": "value"}

    def test_extract_json_from_thinking(self):
        from article_to_reel.prompt_generator import _extract_json
        text = '<think>reasoning here</think>\n{"key": "value"}'
        result = _extract_json(text)
        assert result == {"key": "value"}

    def test_extract_json_raw(self):
        from article_to_reel.prompt_generator import _extract_json
        text = 'Here is the result: {"key": "value"} done.'
        result = _extract_json(text)
        assert result == {"key": "value"}


class TestVideoGenerator:
    """Test video generator module configuration."""

    def test_providers_defined(self):
        from article_to_reel.video_generator import PROVIDERS, FAL_PROVIDER_KEYS
        assert len(PROVIDERS) >= 4  # veo3, ltx, cogvideo5b, cogvideo2b
        assert len(FAL_PROVIDER_KEYS) >= 4

    def test_output_dir_exists(self):
        from article_to_reel.video_generator import OUTPUT_DIR
        assert OUTPUT_DIR.exists()


class TestArticleScraper:
    """Test scraper utilities (no network calls)."""

    def test_slugify(self):
        from article_to_reel.article_scraper import _slugify
        assert _slugify("The Café Racer: How Coffee Gave Birth") == "the-caf-racer-how-coffee-gave-birth"

    def test_article_dataclass(self):
        from article_to_reel.article_scraper import Article
        a = Article(
            title="Test",
            slug="test",
            url="https://example.com",
            category="Test",
            read_time="5 min",
            teaser="A test",
            body="Body text",
        )
        d = a.to_dict()
        assert d["title"] == "Test"
        assert a.prompt_filename == "test.json"
