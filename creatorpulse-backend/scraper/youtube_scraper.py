from typing import List
import requests
from bs4 import BeautifulSoup
from .rss_scraper import fetch_from_rss
from .news_item import NewsItem

def _get_channel_id(channel_url: str) -> str | None:
    """Extracts the YouTube channel ID from a channel URL."""
    try:
        resp = requests.get(channel_url, timeout=10)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        meta_tag = soup.find("meta", property="og:url")
        if meta_tag and meta_tag.get("content"):
            content_url = meta_tag.get("content", "")
            if "/channel/" in content_url:
                return content_url.split("/channel/")[-1]
    except Exception:
        return None
    return None

def fetch_from_youtube(channel_urls: List[str]) -> List[NewsItem]:
    """Fetches recent videos from YouTube channels as NewsItems."""
    rss_urls = []
    for url in channel_urls:
        channel_id = _get_channel_id(url)
        if channel_id:
            rss_urls.append(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
    
    if not rss_urls:
        return []

    return fetch_from_rss(rss_urls, max_items_per_feed=20)
