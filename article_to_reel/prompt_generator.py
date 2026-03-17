"""Use an LLM to generate viral video prompts from article content + playbook."""

import json
import os
import re
from pathlib import Path

import httpx

# Playbook path
PLAYBOOK_PATH = Path(__file__).resolve().parent.parent / "VIRAL_REELS_PLAYBOOK.md"


def load_playbook() -> str:
    """Load the viral reels playbook."""
    return PLAYBOOK_PATH.read_text()


# The meta-prompt: instructs the LLM to be a viral reel creative director
SYSTEM_PROMPT = """You are a world-class Instagram Reels creative director who specializes in
turning written articles into viral short-form video concepts.

You have deep expertise in:
- Viral video mechanics (hooks, pacing, emotional triggers, completion psychology)
- AI video generation prompt engineering (Veo 3, Kling, Sora, Runway, etc.)
- Instagram algorithm optimization (saves, shares, watch-through, replays)
- Visual storytelling and cinematography for 9:16 vertical format

Your job: Take an article and convert its BEST story elements into a viral reel concept
that maximizes engagement. You are NOT making a summary video — you are extracting the
most compelling narrative kernel and turning it into a scroll-stopping reel."""

GENERATION_PROMPT_TEMPLATE = """## VIRAL REELS PLAYBOOK (your rulebook)
{playbook}

---

## ARTICLE TO CONVERT
**Title**: {title}
**Category**: {category}

{article_body}

---

## YOUR TASK

Create a viral Instagram Reel concept based on this article. Follow these steps:

### Step 1: Extract the Viral Kernel
Identify the single most compelling story element from the article — the moment, fact, or
transformation that would make someone stop scrolling. This is NOT a summary. Pick ONE
angle that has the highest emotional/curiosity payload.

### Step 2: Choose the Best Viral Format
From the playbook's 10 proven formats, select the ONE format that best serves this kernel.
Justify your choice.

### Step 3: Apply All 5 Non-Negotiable Rules
Ensure your concept has: (1) 1-second hook, (2) face forward or compelling visual,
(3) complete narrative arc, (4) psychological trigger, (5) engagement CTA.

### Step 4: Write the Video Generation Prompt
Write a detailed, production-ready prompt for an AI video generation model.
The prompt must specify exact visual details for every second of the video.

### Step 5: Self-Critique and Improve
Score your concept against the playbook's 10 success metrics. If any score below 7,
revise. Aim for 8+ on at least 7 metrics.

---

Respond in this EXACT JSON format:
{{
  "article_title": "<original article title>",
  "viral_kernel": {{
    "core_idea": "<the single most compelling element — 1-2 sentences>",
    "why_viral": "<why this specific angle will stop scrolls — be specific about psychology>",
    "emotional_trigger": "<primary emotion: humor/awe/curiosity/nostalgia/inspiration/satisfaction>"
  }},
  "format_choice": {{
    "format_name": "<from the 10 playbook formats>",
    "format_number": <1-10>,
    "justification": "<why this format serves this kernel best>"
  }},
  "reel_concept": {{
    "title": "<catchy reel title for internal reference>",
    "hook_text": "<the bold text overlay for frame 1 — must create curiosity gap>",
    "hook_type": "<pattern_interrupt/curiosity_gap/direct_address/transformation_tease/mid_action_start/shock_value/text_hook>",
    "duration_seconds": <7-30>,
    "narrative_arc": "<setup_punchline/problem_solution/before_after/tension_release/curiosity_reveal>",
    "cta": "<specific call to action>",
    "share_trigger": "<why would someone DM this to a friend?>",
    "save_trigger": "<why would someone bookmark this?>",
    "target_audience": "<who will this resonate with most?>"
  }},
  "video_prompt": {{
    "main_prompt": "<complete, detailed AI video generation prompt — specify every visual detail, camera angle, lighting, color palette, movement, text overlays, pacing, and transitions. Be specific about what happens every 2-3 seconds>",
    "style_keywords": "<comma-separated style keywords for the model>",
    "negative_prompt": "<what to avoid>",
    "technical_spec": {{
      "resolution": "1080x1920",
      "aspect_ratio": "9:16",
      "duration": "<seconds>",
      "fps": 30,
      "format": "mp4"
    }}
  }},
  "virality_scorecard": {{
    "hook_strength": {{"score": <1-10>, "note": "<why>"}},
    "face_or_compelling_visual": {{"score": <1-10>, "note": "<why>"}},
    "narrative_arc": {{"score": <1-10>, "note": "<why>"}},
    "emotional_trigger": {{"score": <1-10>, "note": "<why>"}},
    "completion_pull": {{"score": <1-10>, "note": "<why>"}},
    "share_impulse": {{"score": <1-10>, "note": "<why>"}},
    "save_impulse": {{"score": <1-10>, "note": "<why>"}},
    "mute_friendly": {{"score": <1-10>, "note": "<why>"}},
    "text_hook_present": {{"score": <1-10>, "note": "<why>"}},
    "cta_strength": {{"score": <1-10>, "note": "<why>"}},
    "overall_virality": <1-10>
  }},
  "iteration_notes": "<what you considered and rejected, and why this final concept is strongest>"
}}

IMPORTANT: Think deeply. The best viral reels are NOT summaries — they extract ONE
powerful moment and deliver it with maximum emotional impact in minimum time."""


def _call_llm(system: str, user: str, provider: str = "", api_key: str = "",
              model: str = "") -> str:
    """Call an OpenAI-compatible LLM API."""
    # Provider configs (reusing project patterns)
    providers = {
        "openrouter_free": {
            "base_url": "https://openrouter.ai/api/v1",
            "model": "qwen/qwen3-vl-235b-a22b-thinking",
        },
        "openrouter": {
            "base_url": "https://openrouter.ai/api/v1",
            "model": "qwen/qwen3-vl-8b-instruct",
        },
        "groq": {
            "base_url": "https://api.groq.com/openai/v1",
            "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        },
        "together": {
            "base_url": "https://api.together.xyz/v1",
            "model": "Qwen/Qwen3-VL-32B-Instruct",
        },
        "fireworks": {
            "base_url": "https://api.fireworks.ai/inference/v1",
            "model": "accounts/fireworks/models/qwen3-vl-8b-instruct",
        },
        "openai": {
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o",
        },
        "anthropic_openai": {
            "base_url": "https://api.anthropic.com/v1",
            "model": "claude-sonnet-4-6",
        },
    }

    if not provider:
        provider = os.getenv("PROMPT_LLM_PROVIDER", "openrouter_free")
    if not api_key:
        api_key = os.getenv("PROMPT_LLM_API_KEY", os.getenv("INFERENCE_API_KEY", ""))

    cfg = providers.get(provider, providers["openrouter_free"])
    base_url = cfg["base_url"]
    if not model:
        model = cfg["model"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Add OpenRouter-specific headers
    if "openrouter" in base_url:
        headers["HTTP-Referer"] = "https://github.com/shsingla22/InstagramBestVideoAnalysis"
        headers["X-Title"] = "Article-to-Reel Generator"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": 8192,
        "temperature": 0.7,
    }

    resp = httpx.post(
        f"{base_url}/chat/completions",
        json=payload,
        headers=headers,
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response, handling thinking tags and markdown."""
    # Remove thinking blocks (Qwen3 thinking models)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

    # Try to find JSON block in markdown code fence
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if json_match:
        text = json_match.group(1)
    else:
        # Try to find raw JSON object
        brace_match = re.search(r'\{.*\}', text, re.DOTALL)
        if brace_match:
            text = brace_match.group(0)

    return json.loads(text)


def generate_reel_prompt(article_title: str, article_body: str,
                         category: str = "", provider: str = "",
                         api_key: str = "", iterate: bool = True) -> dict:
    """Generate a viral reel prompt from article content.

    Args:
        article_title: The article title
        article_body: Full article text
        category: Article category/niche
        provider: LLM provider key
        api_key: API key for the provider
        iterate: If True, do a second pass to improve the concept

    Returns:
        dict with the complete reel concept and video prompt
    """
    playbook = load_playbook()

    user_prompt = GENERATION_PROMPT_TEMPLATE.format(
        playbook=playbook,
        title=article_title,
        category=category or "General",
        article_body=article_body,
    )

    print("  [1/2] Generating initial reel concept...")
    raw_response = _call_llm(SYSTEM_PROMPT, user_prompt, provider=provider, api_key=api_key)
    concept = _extract_json(raw_response)

    if not iterate:
        return concept

    # Iteration pass: self-critique and improve
    scores = concept.get("virality_scorecard", {})
    overall = scores.get("overall_virality", 0)
    weak_areas = []
    for metric, data in scores.items():
        if metric == "overall_virality":
            continue
        if isinstance(data, dict) and data.get("score", 10) < 7:
            weak_areas.append(f"- {metric}: {data.get('score')}/10 — {data.get('note', '')}")

    if overall >= 8 and not weak_areas:
        print(f"  First pass scored {overall}/10 — strong concept, keeping it.")
        return concept

    print(f"  First pass scored {overall}/10 with {len(weak_areas)} weak areas. Iterating...")

    iteration_prompt = f"""## PREVIOUS CONCEPT (needs improvement)
{json.dumps(concept, indent=2)}

## WEAK AREAS TO FIX
{chr(10).join(weak_areas) if weak_areas else "Overall score below 8 — make the concept more compelling."}

## YOUR TASK
Improve this reel concept. Focus on:
1. Making the hook MORE scroll-stopping (the first frame must be irresistible)
2. Strengthening the emotional payload (make it hit HARDER)
3. Improving share-ability (why would someone DM this?)
4. Making the video prompt more specific and vivid for AI generation

Keep the same JSON format. Make it significantly better — don't just tweak, reimagine
the weak parts while keeping what works."""

    print("  [2/2] Refining concept...")
    refined_response = _call_llm(SYSTEM_PROMPT, iteration_prompt, provider=provider, api_key=api_key)
    refined = _extract_json(refined_response)

    refined_overall = refined.get("virality_scorecard", {}).get("overall_virality", 0)
    if refined_overall >= overall:
        print(f"  Refined: {overall}/10 → {refined_overall}/10")
        return refined
    else:
        print(f"  Refined scored {refined_overall}/10 (worse). Keeping original ({overall}/10).")
        return concept
