"""Article-to-Reel: Convert blog articles into viral Instagram Reel concepts.

This module scrapes articles from TheRidersGangContent website, uses an LLM
to synthesize article content with the VIRAL_REELS_PLAYBOOK.md knowledge base,
and produces optimized video generation prompts + generates videos.

Completely independent module — does not depend on the main analysis pipeline.
"""
