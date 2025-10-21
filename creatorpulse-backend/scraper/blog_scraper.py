from typing import List
from datetime import datetime, timedelta, timezone
from .rss_scraper import fetch_from_rss
from .news_item import NewsItem

def _is_from_yesterday(dt: datetime) -> bool:
    """Checks if a datetime is from yesterday."""
    if not dt:
        return False
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    return dt.year == yesterday.year and dt.month == yesterday.month and dt.day == yesterday.day

def fetch_from_blog(blog_urls: List[str]) -> List[NewsItem]:
    """
    Fetches recent articles from blogs.
    First attempts to find an RSS feed, then falls back to HTML scraping.
    """
    all_items = []
    for url in blog_urls:
        # 1. Attempt to find RSS feed
        rss_url = url.rstrip('/') + '/feed'
        rss_items = fetch_from_rss([rss_url])
        
        if rss_items:
            yesterdays_items = [item for item in rss_items if _is_from_yesterday(item.published_at)]
            all_items.extend(yesterdays_items)
            continue

        # 2. Fallback to HTML scraping (placeholder)
        # TODO: Implement HTML scraping to find article links and content
        
    return all_items
