import sys
import json
from typing import List
from dataclasses import asdict
from datetime import datetime

from supabase_client import fetch_active_sources
from scraper.reddit_scraper import fetch_from_reddit
from scraper.rss_scraper import fetch_from_rss
from scraper.youtube_scraper import fetch_from_youtube
from scraper.blog_scraper import fetch_from_blog
from scraper.other_scraper import fetch_from_other
from scraper.news_item import NewsItem
from scraper.images_scraper import attach_og_images

def scrape_for_user(user_id: str) -> List[NewsItem]:
    """
    Orchestrates the scraping process for a given user.
    Fetches active sources from Supabase, groups them by type,
    and calls the appropriate scraper for each type.
    """
    sources = fetch_active_sources(user_id)
    if not sources:
        return []

    source_map = {}
    for source in sources:
        source_type = source.get("source_type")
        if source_type not in source_map:
            source_map[source_type] = []
        source_map[source_type].append(source.get("source_identifier"))

    all_items: List[NewsItem] = []

    # TODO: Implement asyncio with aiohttp for concurrent requests.
    for source_type, identifiers in source_map.items():
        if not identifiers:
            continue
        print(f"Scraping {len(identifiers)} source(s) of type '{source_type}'...")
        if source_type == "reddit":
            all_items.extend(fetch_from_reddit(identifiers))
        elif source_type == "rss":
            all_items.extend(fetch_from_rss(identifiers))
        elif source_type == "youtube":
            all_items.extend(fetch_from_youtube(identifiers))
        elif source_type == "blog":
            all_items.extend(fetch_from_blog(identifiers))
        elif source_type == "other":
            all_items.extend(fetch_from_other(identifiers))

    if all_items:
        print(f"Attaching images for {len(all_items)} items...")
        attach_og_images(all_items)

    return all_items

def main():
    """
    Main function to run the scraper and save the output to a JSON file.
    Expects a user_id as a command-line argument.
    """
    if len(sys.argv) < 2:
        print("Usage: python main_scraper.py <user_id>")
        sys.exit(1)
    
    user_id = sys.argv[1]
    print(f"Starting scrape for user: {user_id}")
    
    items = scrape_for_user(user_id)
    
    if not items:
        print("No items found. Exiting.")
        return

    # Convert NewsItem objects to dictionaries for JSON serialization
    items_as_dict = [asdict(item) for item in items]
    
    # Generate a timestamped filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"newsletter_data_{user_id}_{timestamp}.json"
    
    # Custom JSON encoder to handle datetime objects
    class DateTimeEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, datetime):
                return o.isoformat()
            return super().default(o)

    # Write to JSON file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(items_as_dict, f, cls=DateTimeEncoder, ensure_ascii=False, indent=4)
        
    print(f"✅ Successfully wrote {len(items)} items to {filename}")


if __name__ == '__main__':
    main()
