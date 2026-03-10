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

# --- vLLM / Qwen3-VL ---
VLLM_MODEL_NAME = os.getenv("VLLM_MODEL_NAME", "Qwen/Qwen3-VL-8B-Instruct")
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

# --- Instagram creators to analyze ---
# Top creators known for viral reels across niches
INSTAGRAM_CREATORS = [
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

# --- Analysis prompt ---
VIDEO_ANALYSIS_PROMPT = """You are an expert social media analyst specializing in Instagram Reels virality.

Analyze this video and provide a structured JSON response with the following fields:

{
  "hook_type": "<how the video grabs attention in the first 1-3 seconds>",
  "hook_strength": <1-10>,
  "content_format": "<e.g., tutorial, transformation, POV, storytime, trend, comedy skit, etc.>",
  "pacing": "<slow/medium/fast/variable>",
  "visual_quality": <1-10>,
  "editing_style": "<e.g., jump cuts, smooth transitions, raw/unedited, text overlays, etc.>",
  "emotional_trigger": "<primary emotion: humor, awe, curiosity, nostalgia, inspiration, etc.>",
  "text_overlays": <true/false>,
  "face_presence": <true/false>,
  "scene_changes": <count of distinct scene changes>,
  "duration_estimate_seconds": <estimated duration>,
  "trending_elements": ["<list of trending elements spotted>"],
  "virality_score": <1-10>,
  "virality_reasons": ["<list of reasons this could go viral>"],
  "improvement_suggestions": ["<list of suggestions to improve virality>"],
  "summary": "<brief 2-3 sentence summary of the content and what makes it engaging>"
}

Respond ONLY with valid JSON. No extra text."""
