from typing import List
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime, timezone
from .news_item import NewsItem

def fetch_from_other(urls: List[str]) -> List[NewsItem]:
    """
    Performs a generic HTML scrape of a URL, extracting the title and first paragraph.
    """
    items = []
    for url in urls:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                continue
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            title = soup.title.string if soup.title else "Untitled"
            
            first_paragraph = ""
            for p in soup.find_all('p'):
                if p.get_text(strip=True):
                    first_paragraph = p.get_text(strip=True)
                    break
            
            source = urlparse(url).netloc
            
            items.append(NewsItem(
                title=title,
                url=url,
                source=source,
                summary=first_paragraph,
                published_at=datetime.now(timezone.utc)
            ))
        except Exception:
            continue
    return items
