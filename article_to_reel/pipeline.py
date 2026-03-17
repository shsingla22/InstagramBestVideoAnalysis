#!/usr/bin/env python3
"""Article-to-Reel Pipeline: Convert articles into viral Instagram Reels.

This is the main entry point for the article_to_reel module. It orchestrates:
1. Scraping an article from TheRidersGangContent website
2. Using an LLM + the VIRAL_REELS_PLAYBOOK.md to generate a viral reel concept
3. Saving the per-article prompt file
4. Optionally generating the video with an AI video model

Usage:
  # Generate prompt only (no video generation):
  python3 -m article_to_reel.pipeline --url <article-url>

  # Generate prompt + video:
  python3 -m article_to_reel.pipeline --url <article-url> --generate --video-provider veo3

  # Use a pre-built prompt file:
  python3 -m article_to_reel.pipeline --prompt-file article_to_reel/prompts/the-cafe-racer.json --generate

  # List all articles from the website:
  python3 -m article_to_reel.pipeline --list-articles

  # Process all articles (prompt generation only):
  python3 -m article_to_reel.pipeline --all

Examples:
  # Café Racer article with Veo 3:
  export GOOGLE_API_KEY=your-key
  python3 -m article_to_reel.pipeline \\
    --url https://shsingla22.github.io/TheRidersGangContent/articles/the-cafe-racer-how-coffee-gave-birth-to-motorcycle-culture.html \\
    --generate --video-provider veo3

  # Use free LTX (no API key needed) for video:
  python3 -m article_to_reel.pipeline \\
    --prompt-file article_to_reel/prompts/the-cafe-racer-how-coffee-gave-birth-to-motorcycle-culture.json \\
    --generate --video-provider ltx
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from article_to_reel.article_scraper import fetch_article, scrape_index, SITE_BASE
from article_to_reel.prompt_generator import generate_reel_prompt
from article_to_reel.video_generator import generate_video, OUTPUT_DIR

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
PROMPTS_DIR.mkdir(exist_ok=True)


def list_articles():
    """List all available articles from the website."""
    print("\n  Fetching articles from TheRidersGangContent...")
    articles = scrape_index()

    if not articles:
        print("  No articles found. The website may have changed structure.")
        print(f"  Check: {SITE_BASE}/#articles")
        return []

    print(f"\n  Found {len(articles)} articles:\n")
    for i, a in enumerate(articles, 1):
        title = a.get("title", "Untitled")
        cat = a.get("category", "")
        url = a.get("url", "")
        print(f"  [{i:2d}] {title}")
        if cat:
            print(f"       Category: {cat}")
        print(f"       URL: {url}")
        print()

    return articles


def process_article(url: str, title: str = "", category: str = "",
                    llm_provider: str = "", llm_api_key: str = "",
                    iterate: bool = True) -> dict:
    """Process a single article: scrape → LLM prompt generation → save."""
    print(f"\n{'=' * 70}")
    print(f"  ARTICLE-TO-REEL PIPELINE")
    print(f"{'=' * 70}")

    # Step 1: Scrape article
    print(f"\n  [Step 1] Scraping article...")
    article = fetch_article(url, title=title, category=category)
    print(f"  Title: {article.title}")
    print(f"  Category: {article.category}")
    print(f"  Body: {len(article.body)} chars")

    if len(article.body) < 100:
        print("  WARNING: Article body is very short. The website may require JavaScript.")
        print("  Trying to proceed with available content...")

    # Step 2: Generate reel prompt via LLM
    print(f"\n  [Step 2] Generating viral reel concept via LLM...")
    if not llm_provider:
        llm_provider = os.getenv("PROMPT_LLM_PROVIDER", "openrouter_free")
    if not llm_api_key:
        llm_api_key = os.getenv("PROMPT_LLM_API_KEY", os.getenv("INFERENCE_API_KEY", ""))

    if not llm_api_key:
        print("\n  ERROR: No LLM API key set.")
        print("  Set one of:")
        print("    export PROMPT_LLM_API_KEY=your-key  # For the prompt LLM")
        print("    export INFERENCE_API_KEY=your-key    # Fallback")
        print("\n  Free options:")
        print("    - OpenRouter: https://openrouter.ai (free tier)")
        print("    - Groq: https://console.groq.com (free tier)")
        sys.exit(1)

    concept = generate_reel_prompt(
        article_title=article.title,
        article_body=article.body,
        category=article.category,
        provider=llm_provider,
        api_key=llm_api_key,
        iterate=iterate,
    )

    # Step 3: Save prompt file
    prompt_path = PROMPTS_DIR / article.prompt_filename
    with open(prompt_path, "w") as f:
        json.dump(concept, f, indent=2)
    print(f"\n  Prompt saved: {prompt_path}")

    # Print summary
    scorecard = concept.get("virality_scorecard", {})
    overall = scorecard.get("overall_virality", "?")
    hook = concept.get("reel_concept", {}).get("hook_text", "?")
    fmt = concept.get("format_choice", {}).get("format_name", "?")

    print(f"\n{'─' * 70}")
    print(f"  REEL CONCEPT SUMMARY")
    print(f"{'─' * 70}")
    print(f"  Hook: \"{hook}\"")
    print(f"  Format: {fmt}")
    print(f"  Duration: {concept.get('reel_concept', {}).get('duration_seconds', '?')}s")
    print(f"  Virality Score: {overall}/10")
    print(f"  Emotional Trigger: {concept.get('viral_kernel', {}).get('emotional_trigger', '?')}")
    print(f"{'─' * 70}")

    return concept


def generate_from_prompt_file(prompt_path: str, video_provider: str = "ltx") -> dict:
    """Generate a video from an existing prompt file."""
    with open(prompt_path) as f:
        concept = json.load(f)

    video_prompt = concept.get("video_prompt", {})
    main_prompt = video_prompt.get("main_prompt", "")
    duration = int(video_prompt.get("technical_spec", {}).get("duration", "5"))
    slug = Path(prompt_path).stem

    if not main_prompt:
        print("  ERROR: No video prompt found in the prompt file.")
        sys.exit(1)

    print(f"\n  [Video] Generating with {video_provider}...")
    print(f"  Prompt: {main_prompt[:100]}...")
    print(f"  Duration: {duration}s")

    result = generate_video(
        prompt=main_prompt,
        slug=slug,
        provider=video_provider,
        duration=duration,
    )

    if result.get("local_path"):
        print(f"\n  Video saved: {result['local_path']}")
        print(f"  Generation time: {result['elapsed']:.0f}s")
    else:
        print(f"\n  WARNING: No video was generated.")

    return result


def main():
    all_video_providers = ["veo3", "ltx", "cogvideo5b", "cogvideo2b",
                           "kling3", "kling26", "veo3_fal", "minimax", "wan26", "seedance"]

    parser = argparse.ArgumentParser(
        description="Convert articles into viral Instagram Reel concepts and videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List articles:
  python3 -m article_to_reel.pipeline --list-articles

  # Generate reel concept for an article:
  python3 -m article_to_reel.pipeline --url <article-url>

  # Generate concept + video:
  python3 -m article_to_reel.pipeline --url <article-url> --generate --video-provider veo3

  # Generate video from existing prompt file:
  python3 -m article_to_reel.pipeline --prompt-file <path> --generate --video-provider ltx
""",
    )
    parser.add_argument("--url", help="Article URL to process")
    parser.add_argument("--title", default="", help="Article title (auto-detected if omitted)")
    parser.add_argument("--category", default="", help="Article category")
    parser.add_argument("--prompt-file", help="Use existing prompt file instead of generating")
    parser.add_argument("--list-articles", action="store_true", help="List all available articles")
    parser.add_argument("--all", action="store_true", help="Process all articles (prompts only)")
    parser.add_argument("--generate", action="store_true", help="Also generate the video")
    parser.add_argument("--video-provider", default="ltx", choices=all_video_providers,
                        help="Video generation provider (default: ltx — free)")
    parser.add_argument("--llm-provider", default="",
                        help="LLM provider for prompt generation (default: openrouter_free)")
    parser.add_argument("--no-iterate", action="store_true",
                        help="Skip the refinement iteration pass")
    args = parser.parse_args()

    if args.list_articles:
        list_articles()
        return

    if args.prompt_file:
        if not args.generate:
            # Just display the prompt file
            with open(args.prompt_file) as f:
                concept = json.load(f)
            print(json.dumps(concept, indent=2))
            return
        generate_from_prompt_file(args.prompt_file, args.video_provider)
        return

    if args.all:
        print("  Fetching all articles...")
        articles = scrape_index()
        for a in articles:
            try:
                process_article(
                    url=a["url"],
                    title=a.get("title", ""),
                    category=a.get("category", ""),
                    llm_provider=args.llm_provider,
                    iterate=not args.no_iterate,
                )
            except Exception as e:
                print(f"  ERROR processing {a.get('title', a['url'])}: {e}")
        return

    if not args.url:
        parser.print_help()
        print("\n  ERROR: Provide --url, --prompt-file, --list-articles, or --all")
        sys.exit(1)

    concept = process_article(
        url=args.url,
        title=args.title,
        category=args.category,
        llm_provider=args.llm_provider,
        iterate=not args.no_iterate,
    )

    if args.generate:
        slug = Path(PROMPTS_DIR / "temp").stem
        # Find the saved prompt file
        prompt_files = sorted(PROMPTS_DIR.glob("*.json"), key=os.path.getmtime, reverse=True)
        if prompt_files:
            generate_from_prompt_file(str(prompt_files[0]), args.video_provider)

    print(f"\n{'=' * 70}")
    print(f"  DONE")
    print(f"  Prompts: {PROMPTS_DIR}")
    print(f"  Videos:  {OUTPUT_DIR}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
