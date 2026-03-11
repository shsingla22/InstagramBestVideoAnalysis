"""Central configuration for the Instagram Video Analysis project."""

import os
from pathlib import Path

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
VIDEOS_DIR = DATA_DIR / "videos"
RESULTS_DIR = DATA_DIR / "results"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
VIDEOS_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# --- Inference provider ---
# Set INFERENCE_PROVIDER to switch between local vLLM and cloud APIs.
# Options: "vllm", "fireworks", "together", "openrouter", "dashscope",
#          "openrouter_free", "huggingface", "groq"
# FREE options (no payment required):
#   "openrouter_free" — $0 Qwen3-VL-235B via OpenRouter (20 req/min, 200/day)
#   "huggingface"     — free tier via HuggingFace Inference API
#   "groq"            — free Llama 4 Scout vision (very fast, 30 req/min)
INFERENCE_PROVIDER = os.getenv("INFERENCE_PROVIDER", "openrouter_free")

# Cloud API key (used by all cloud providers)
INFERENCE_API_KEY = os.getenv("INFERENCE_API_KEY", "")

# Provider-specific configuration
PROVIDERS = {
    "vllm": {
        "base_url": os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1"),
        "model": os.getenv("VLLM_MODEL_NAME", "Qwen/Qwen3-VL-8B-Instruct"),
        "api_key": "EMPTY",
        "supports_video_url": True,
    },
    "fireworks": {
        "base_url": "https://api.fireworks.ai/inference/v1",
        "model": os.getenv("FIREWORKS_MODEL", "accounts/fireworks/models/qwen3-vl-8b-instruct"),
        "api_key": os.getenv("INFERENCE_API_KEY", ""),
        "supports_video_url": False,
    },
    "together": {
        "base_url": "https://api.together.xyz/v1",
        "model": os.getenv("TOGETHER_MODEL", "Qwen/Qwen3-VL-32B-Instruct"),
        "api_key": os.getenv("INFERENCE_API_KEY", ""),
        "supports_video_url": False,
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": os.getenv("OPENROUTER_MODEL", "qwen/qwen3-vl-8b-instruct"),
        "api_key": os.getenv("INFERENCE_API_KEY", ""),
        "supports_video_url": False,
    },
    "dashscope": {
        "base_url": os.getenv("DASHSCOPE_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"),
        "model": os.getenv("DASHSCOPE_MODEL", "qwen3-vl-8b-instruct"),
        "api_key": os.getenv("INFERENCE_API_KEY", ""),
        "supports_video_url": True,
    },
    # ── Free providers ──────────────────────────────────────────────
    "openrouter_free": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": os.getenv("OPENROUTER_FREE_MODEL", "qwen/qwen3-vl-235b-a22b-thinking"),
        "api_key": os.getenv("INFERENCE_API_KEY", ""),
        "supports_video_url": False,
    },
    "huggingface": {
        "base_url": "https://router.huggingface.co/v1",
        "model": os.getenv("HF_MODEL", "Qwen/Qwen2.5-VL-7B-Instruct"),
        "api_key": os.getenv("HF_TOKEN", os.getenv("INFERENCE_API_KEY", "")),
        "supports_video_url": False,
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "model": os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct"),
        "api_key": os.getenv("GROQ_API_KEY", os.getenv("INFERENCE_API_KEY", "")),
        "supports_video_url": False,
    },
}


def get_provider_config() -> dict:
    """Return the active provider's configuration."""
    provider = PROVIDERS.get(INFERENCE_PROVIDER)
    if not provider:
        raise ValueError(f"Unknown provider: {INFERENCE_PROVIDER}. Choose from: {list(PROVIDERS.keys())}")
    return provider


# --- vLLM local server (only used when INFERENCE_PROVIDER=vllm) ---
VLLM_HOST = os.getenv("VLLM_HOST", "0.0.0.0")
VLLM_PORT = int(os.getenv("VLLM_PORT", "8000"))
VLLM_GPU_MEMORY_UTILIZATION = float(os.getenv("VLLM_GPU_MEMORY_UTIL", "0.85"))
VLLM_MAX_MODEL_LEN = int(os.getenv("VLLM_MAX_MODEL_LEN", "4096"))
VLLM_TENSOR_PARALLEL_SIZE = int(os.getenv("VLLM_TENSOR_PARALLEL_SIZE", "1"))

# --- Application server ---
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8080"))

# --- Video processing ---
MAX_FRAMES_PER_VIDEO = int(os.getenv("MAX_FRAMES_PER_VIDEO", "16"))
FRAME_RESIZE = (384, 384)  # Qwen3-VL optimal input size
MAX_VIDEO_SIZE_MB = int(os.getenv("MAX_VIDEO_SIZE_MB", "100"))

# --- Instagram authentication (for yt-dlp downloads) ---
# Option 1: Path to Netscape-format cookies.txt exported from browser
#   Export with a browser extension like "Get cookies.txt LOCALLY"
INSTAGRAM_COOKIES_FILE = os.getenv("INSTAGRAM_COOKIES_FILE", "")
# Option 2: Let yt-dlp extract cookies directly from a browser
#   Values: "chrome", "firefox", "edge", "safari", "opera", "brave"
INSTAGRAM_COOKIES_FROM_BROWSER = os.getenv("INSTAGRAM_COOKIES_FROM_BROWSER", "")

# --- Instagram creators to analyze ---
# Two categories: famous influencers (baseline) and non-famous viral creators (study targets)
INSTAGRAM_CREATORS_FAMOUS = [
    {"handle": "@khaby.lame", "niche": "comedy/reaction", "followers": "162M"},
    {"handle": "@zachking", "niche": "magic/visual-effects", "followers": "79M"},
    {"handle": "@therock", "niche": "fitness/lifestyle", "followers": "400M"},
    {"handle": "@kingjames", "niche": "sports/lifestyle", "followers": "159M"},
    {"handle": "@charlidamelio", "niche": "dance/lifestyle", "followers": "56M"},
    {"handle": "@addisonre", "niche": "dance/comedy", "followers": "40M"},
    {"handle": "@willsmith", "niche": "comedy/lifestyle", "followers": "75M"},
    {"handle": "@mrbeast", "niche": "entertainment/stunts", "followers": "48M"},
    {"handle": "@garyvee", "niche": "business/motivation", "followers": "20M"},
    {"handle": "@emmachamberlain", "niche": "lifestyle/humor", "followers": "16M"},
    {"handle": "@jasonderulo", "niche": "music/comedy", "followers": "62M"},
    {"handle": "@bfranklinfit", "niche": "fitness/transformation", "followers": "5M"},
    {"handle": "@dude.perfect", "niche": "sports/tricks", "followers": "22M"},
    {"handle": "@spencerx", "niche": "beatbox/music", "followers": "25M"},
    {"handle": "@natgeo", "niche": "nature/documentary", "followers": "284M"},
]

# Non-famous creators whose reels went viral organically (the real study subjects)
# These are creators who had small followings when their content exploded
INSTAGRAM_CREATORS_VIRAL_UNKNOWNS = [
    {"handle": "@joolieannie", "niche": "comedy/lifestyle", "followers": "~2M", "viral_moment": "Very Demure Very Mindful - 54.8M views from zero following", "why_interesting": "Single catchphrase created cultural phenomenon, Dictionary.com word of the year"},
    {"handle": "@emilymariko", "niche": "food/lifestyle", "followers": "~13M", "viral_moment": "Salmon rice bowl - 57M views, was unknown before", "why_interesting": "Silent cooking video with no text overlays went mega-viral through pure ASMR satisfaction"},
    {"handle": "@djlemay2", "niche": "food/entertainment", "followers": "~465K", "viral_moment": "Ice cream tricks at Cold Stone - 8M views day one", "why_interesting": "Turned minimum-wage job content into ice cream shop empire"},
    {"handle": "@kelseyinlondon", "niche": "travel/lifestyle", "followers": "~753K", "viral_moment": "Travel guides format - grew 300K from Reels alone", "why_interesting": "Proves systematic Reels format can build audience from scratch"},
    {"handle": "@thepotatosauraus", "niche": "music/reaction", "followers": "~500K", "viral_moment": "Music reaction videos that work on mute", "why_interesting": "Cracked mute-friendly format with text-first approach"},
    {"handle": "@junyuanofficial", "niche": "lifestyle/dating", "followers": "~200K", "viral_moment": "Street interview format - millions of views within weeks", "why_interesting": "Cross-posted from TikTok, got recognized in streets within 5 weeks"},
    {"handle": "@catchnicecream", "niche": "food/entertainment", "followers": "~1.5M", "viral_moment": "Ice cream catching tricks", "why_interesting": "Satisfying visual format that's endlessly rewatchable"},
    {"handle": "@coop_formula", "niche": "sports/education", "followers": "~50K", "viral_moment": "Learning F1 from scratch - curious learner bias", "why_interesting": "Proves you don't need expertise, just authentic learning journey"},
    {"handle": "@nancytyagi", "niche": "fashion/DIY", "followers": "~3M", "viral_moment": "Fabric-to-dress transformation videos", "why_interesting": "Shows entire creation process, before-after transformation format"},
    {"handle": "@leanbeefpatty", "niche": "fitness/lifestyle", "followers": "~6M", "viral_moment": "Breaking feminine fitness stereotypes", "why_interesting": "Authenticity + challenging norms = massive organic growth"},
]

# Combined list for backward compatibility
INSTAGRAM_CREATORS = INSTAGRAM_CREATORS_FAMOUS + [
    {"handle": c["handle"], "niche": c["niche"], "followers": c["followers"]}
    for c in INSTAGRAM_CREATORS_VIRAL_UNKNOWNS
]

# --- Analysis prompt ---
VIDEO_ANALYSIS_PROMPT = """You are a world-class video strategist and Instagram Reels analyst with 10+ years
of experience studying viral content mechanics. You have deep expertise in cinematography,
behavioral psychology, platform algorithms, and audience retention science.

Analyze this video frame-by-frame with extreme detail. Provide a structured JSON response
covering ALL of the following dimensions:

{
  "hook_analysis": {
    "hook_type": "<specific technique: pattern interrupt, curiosity gap, shock value, mid-action start, direct address, text hook, visual spectacle, question, controversy, or transformation tease>",
    "hook_description": "<describe exactly what happens in the first 1-3 seconds and WHY it stops the scroll>",
    "hook_strength": "<1-10, with justification>",
    "first_frame_impression": "<what does the very first frame communicate before any motion? Would you stop scrolling?>",
    "thumb_stop_rate_estimate": "<low/medium/high/very_high — how likely is this to stop thumbs in the feed?>"
  },

  "visual_cinematography": {
    "camera_angles": ["<list all angles used: eye-level, low-angle, high-angle, bird's-eye, dutch-angle, close-up, extreme-close-up, wide-shot, medium-shot>"],
    "camera_movement": "<static, handheld, tracking, dolly, pan, tilt, zoom, drone, or combination>",
    "lighting_style": "<natural, studio, golden-hour, neon, dramatic-shadows, flat, backlit, ring-light, mixed>",
    "color_palette": "<describe dominant colors and color grading: warm, cool, desaturated, vibrant, moody, pastel, high-contrast>",
    "composition_technique": "<rule-of-thirds, centered-subject, leading-lines, symmetry, depth-of-field, negative-space>",
    "visual_quality_score": "<1-10>",
    "production_value": "<DIY-phone, semi-professional, professional, cinematic>"
  },

  "editing_and_pacing": {
    "editing_style": "<jump-cuts, match-cuts, smooth-transitions, whip-pans, freeze-frames, speed-ramps, split-screen, before-after, montage, raw-unedited, or combination>",
    "pacing": "<slow/medium/fast/variable — describe the rhythm>",
    "average_shot_duration_seconds": "<estimate average time per shot/cut>",
    "scene_changes_count": "<integer>",
    "transition_types": ["<list specific transitions used: cut, dissolve, swipe, zoom-in, morph, etc.>"],
    "rhythm_sync_to_audio": "<true/false — do cuts align with beats or audio cues?>",
    "use_of_speed": "<normal, slow-motion, time-lapse, speed-ramp, or combination>"
  },

  "content_structure": {
    "content_format": "<tutorial, transformation, POV, storytime, trend-participation, comedy-skit, reaction, day-in-life, before-after, challenge, educational, aesthetic-loop, motivational-speech, product-review, behind-the-scenes, other>",
    "narrative_arc": "<describe the storytelling structure: setup-punchline, problem-solution, tension-release, curiosity-reveal, build-up-payoff, no-arc-aesthetic-only>",
    "duration_estimate_seconds": "<integer>",
    "content_density": "<how much information/action per second: sparse, moderate, dense, overwhelming>",
    "rewatch_value": "<low/medium/high — would viewers watch this again? Why?>",
    "completion_likelihood": "<low/medium/high — will viewers watch to the end? What keeps them or loses them?>"
  },

  "audio_indicators": {
    "audio_type_likely": "<trending-sound, original-audio, voiceover, music-only, ASMR, dialogue, ambient, silent>",
    "text_overlays_present": "<true/false>",
    "text_overlay_purpose": "<hook-text, captions, labels, call-to-action, punchline, storytelling, or N/A>",
    "mute_friendly": "<true/false — does the video work without sound based on visuals alone?>"
  },

  "subject_and_performance": {
    "face_presence": "<true/false>",
    "face_prominence": "<not-present, background, partial, centered-focus, extreme-close-up>",
    "eye_contact_with_camera": "<true/false — does the subject look directly at viewer?>",
    "body_language_energy": "<calm, neutral, energetic, chaotic, dramatic, intimate>",
    "authenticity_feel": "<polished-influencer, raw-authentic, scripted-natural, obviously-staged, candid-moment>",
    "relatability_score": "<1-10 — how relatable is the subject/situation to average viewer?>"
  },

  "psychological_triggers": {
    "primary_emotion": "<humor, awe, curiosity, nostalgia, inspiration, fear, surprise, satisfaction, envy, empathy, anger, joy>",
    "secondary_emotions": ["<list any additional emotions triggered>"],
    "cognitive_bias_exploited": ["<list applicable: curiosity-gap, social-proof, FOMO, loss-aversion, bandwagon, authority, reciprocity, novelty-bias, completion-drive, none>"],
    "share_trigger": "<what would make someone share this? Identity-signal, useful-info, emotional-resonance, humor, controversy, wow-factor, relatability>",
    "save_trigger": "<what would make someone save this? Reference-value, aspirational, tutorial, recipe, checklist, aesthetic-inspiration, none>",
    "comment_bait": "<what would drive comments? Debate-question, fill-in-blank, tag-someone, hot-take, relatable-experience, none>"
  },

  "platform_optimization": {
    "vertical_format_usage": "<proper 9:16, letterboxed, square-cropped, horizontal-in-vertical>",
    "loop_potential": "<does the ending connect back to the beginning for seamless looping? true/false>",
    "algorithm_signals": ["<list factors that help algorithmic distribution: high-retention, shares, saves, comments, watch-time, replay>"],
    "trend_participation": "<is this following a current trend, audio, or format? Describe or say original>",
    "niche_category": "<specific niche this fits into for algorithmic categorization>",
    "crosspost_potential": "<would this work on TikTok/YouTube-Shorts/Facebook-Reels? Why or why not?>"
  },

  "virality_assessment": {
    "virality_score": "<1-10 with detailed justification>",
    "virality_ceiling": "<what's the realistic max reach: niche-only, moderate-spread, mass-viral, culture-defining>",
    "virality_factors": [
      "<factor 1 with explanation>",
      "<factor 2 with explanation>",
      "<factor 3 with explanation>"
    ],
    "virality_blockers": [
      "<what prevents this from going MORE viral — be brutally honest>"
    ],
    "comparable_viral_content": "<what successful viral content does this remind you of and why?>"
  },

  "actionable_improvements": [
    {
      "priority": "<high/medium/low>",
      "area": "<hook, editing, audio, storytelling, visual, CTA, format>",
      "current_issue": "<what's wrong or suboptimal>",
      "specific_fix": "<exactly what to change and how>",
      "expected_impact": "<what improvement this would drive: retention, shares, saves, reach>"
    }
  ],

  "expert_summary": "<4-6 sentence expert analysis covering: what this video does well, what makes it work (or not), the psychological mechanics behind its appeal, and a professional verdict on its viral potential. Be specific and reference actual techniques observed.>"
}

CRITICAL INSTRUCTIONS:
- Analyze the ACTUAL video frames provided. Do not make up content that isn't visible.
- Be brutally honest — do not inflate scores. A 10/10 virality score should be reserved for once-in-a-year viral phenomena.
- Reference specific frames when describing what you see.
- Consider this from the perspective of a viewer scrolling Instagram at 11pm — would this stop THEIR thumb?
- Respond ONLY with valid JSON. No extra text before or after the JSON."""
