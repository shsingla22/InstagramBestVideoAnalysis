"""Scrape articles from TheRidersGangContent website."""

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path

import httpx
from bs4 import BeautifulSoup


SITE_BASE = "https://shsingla22.github.io/TheRidersGangContent"
ARTICLES_URL = f"{SITE_BASE}/#articles"


@dataclass
class Article:
    """A scraped article with its content."""
    title: str
    slug: str
    url: str
    category: str
    read_time: str
    teaser: str
    body: str  # Full article text

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def prompt_filename(self) -> str:
        return f"{self.slug}.json"


def _slugify(title: str) -> str:
    """Convert a title to a URL-safe slug."""
    slug = title.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug)
    return slug.strip('-')


def _extract_article_links(html: str) -> list[dict]:
    """Extract article links from the index page."""
    soup = BeautifulSoup(html, "html.parser")
    articles = []

    for card in soup.select("article, .article-card, .post-card, a[href*='articles/']"):
        link = card.get("href") if card.name == "a" else None
        if not link:
            a_tag = card.find("a", href=True)
            if a_tag:
                link = a_tag["href"]
        if not link or "articles/" not in link:
            continue

        title_el = card.find(["h2", "h3", "h4", ".title"])
        title = title_el.get_text(strip=True) if title_el else ""

        cat_el = card.find(class_=re.compile(r"category|tag|badge"))
        category = cat_el.get_text(strip=True) if cat_el else ""

        time_el = card.find(class_=re.compile(r"time|read|duration"))
        read_time = time_el.get_text(strip=True) if time_el else ""

        teaser_el = card.find("p")
        teaser = teaser_el.get_text(strip=True) if teaser_el else ""

        if not link.startswith("http"):
            link = f"{SITE_BASE}/{link.lstrip('/')}"

        articles.append({
            "title": title,
            "url": link,
            "category": category,
            "read_time": read_time,
            "teaser": teaser,
        })

    return articles


def _extract_article_body(html: str) -> str:
    """Extract the main body text from an article page."""
    soup = BeautifulSoup(html, "html.parser")

    # Try common article containers
    for selector in ["article", ".article-content", ".post-content", "main", ".content"]:
        container = soup.select_one(selector)
        if container:
            # Remove nav, header, footer, script, style
            for tag in container.find_all(["nav", "header", "footer", "script", "style", "aside"]):
                tag.decompose()
            paragraphs = container.find_all(["p", "h1", "h2", "h3", "h4", "blockquote", "li"])
            text_parts = []
            for p in paragraphs:
                txt = p.get_text(strip=True)
                if txt:
                    prefix = ""
                    if p.name in ("h1", "h2", "h3", "h4"):
                        prefix = "## " if p.name in ("h1", "h2") else "### "
                    elif p.name == "blockquote":
                        prefix = "> "
                    elif p.name == "li":
                        prefix = "- "
                    text_parts.append(f"{prefix}{txt}")
            return "\n\n".join(text_parts)

    # Fallback: get all paragraph text
    return "\n\n".join(p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True))


def scrape_article(url: str) -> str:
    """Scrape a single article's body text."""
    resp = httpx.get(url, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    return _extract_article_body(resp.text)


def scrape_index() -> list[dict]:
    """Scrape the article index page for all article links."""
    resp = httpx.get(ARTICLES_URL, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    return _extract_article_links(resp.text)


def fetch_article(url: str, title: str = "", category: str = "",
                  read_time: str = "", teaser: str = "") -> Article:
    """Fetch and parse a complete article."""
    body = scrape_article(url)
    if not title:
        title = url.split("/")[-1].replace(".html", "").replace("-", " ").title()
    slug = _slugify(title)
    return Article(
        title=title,
        slug=slug,
        url=url,
        category=category,
        read_time=read_time,
        teaser=teaser,
        body=body,
    )
