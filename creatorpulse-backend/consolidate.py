from __future__ import annotations
import sys
import json
import yaml
import html
import time
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from scraper.news_item import NewsItem
from google import genai
from supabase_client import save_newsletter, fetch_clients
from email_service import EmailService


def _normalize_url(url: str | None) -> str:
    return (url or "").strip().lower().rstrip("/")


def dedupe_items(items: List[NewsItem]) -> List[NewsItem]:
    seen: dict[tuple[str, str], NewsItem] = {}
    for it in items:
        key = (_normalize_url(it.url), (it.title or "").strip().lower())
        # Keep the item with the higher score if a duplicate is found
        if key not in seen or (it.score > seen[key].score):
            seen[key] = it
    return list(seen.values())


def _source_weight_for(source: str | None, weights: Dict[str, float]) -> float:
    s = (source or "").strip().lower()
    if s.startswith("r/"):
        return float(weights.get("reddit", 0.0))
    
    # Check for specific domain matches in weights
    for domain, weight in weights.items():
        if domain in s:
            return float(weight)
            
    # Heuristic: treat everything else as RSS unless explicitly mapped
    return float(weights.get("rss", 0.0))


def rank_items(items: List[NewsItem], weights: Optional[Dict[str, float]] = None, now: Optional[datetime] = None) -> List[NewsItem]:
    if now is None:
        now = datetime.now(timezone.utc)
    weights = weights or {}
    def score_fn(it: NewsItem) -> float:
        age_hours = 0.0
        if it.published_at:
            # Ensure published_at is timezone-aware
            pub_date = it.published_at
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            age_hours = max(0.0, (now - pub_date).total_seconds() / 3600.0)
        
        recency_bonus = max(0.0, 48.0 - age_hours)  # prefer last 2 days
        base = float(it.score or 0.0)
        source_w = _source_weight_for(getattr(it, "source", None), weights)
        return base + recency_bonus + source_w
    return sorted(items, key=score_fn, reverse=True)


def _make_llm_prompt_full_report(items: List[NewsItem], max_items: int = 60) -> str:
    limited = items[:max_items]
    lines = [
        "You are an expert news editor and technical report writer.",
        "Produce a FULL, self-contained daily report in **HTML5 only** (do not use Markdown).",
        "Constraints and format:",
        "- Output a valid, standalone HTML document: include <!DOCTYPE html>, <html>, <head>, and <body>.",
        "- Add a <head> with a <style> block for clean, modern email-friendly formatting:",
        "    * Font: system-ui or sans-serif.",
        "    * Light background (#f9f9f9) with card-like white sections and subtle shadows.",
        "    * Use padding, spacing, and <h1>/<h2> headings for readability.",
        "- At the top: include an <h1> titled 'CreatorPulse Daily Report' and an **Executive Summary** (3–5 sentences).",
        "- Cluster and deduplicate: combine highly similar items into one topic section.",
        "- Each topic section should include:",
        "    * A short <h2> heading (the theme/topic).",
        "    * A descriptive summary (6–8 sentences).",
        "    * 5–8 key bullet takeaways (<ul><li>).",
        "    * At most one inline image if provided (with alt text).",
        "    * A 'Read more' link to the best single source.",
        "- At the end: add a 'Key Takeaways' section in bullet points.",
        "- Keep tone precise, professional, and neutral (no hype).",
        "- Ensure everything is self-contained—no external CSS, JS, or links except for sources.",
        "Here is the data to use for the report:"
    ]
    for it in limited:
        published = it.published_at.isoformat() if it.published_at else "N/A"
        image_part = f" image_url={it.image_url}" if getattr(it, "image_url", None) else ""
        summary_part = (it.summary or "").replace("\n", " ").strip()
        lines.append(
            f"- [source={it.source}] title={it.title} date={published} url={it.url}{image_part} summary={summary_part}"
        )
    return "\n".join(lines)


def _call_gemini(cfg: Dict[str, Any], prompt: str, max_retries: int = 3, delay_sec: float = 5.0) -> Optional[str]:
    attempt = 0
    while attempt < max_retries:
        try:
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                print("❌ Missing Gemini API key. Please add GEMINI_API_KEY to your .env file.")
                return None

            model_name = cfg.get("model", "gemini-2.0-flash")
            
            print(f"⚡ _call_gemini(): Using model={model_name} (Attempt {attempt + 1})")
            
            # Use the new Google GenAI SDK
            client = genai.Client()

            print("⚡ Sending request to Gemini…")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            
            text = response.text.strip() if response.text else ""

            if text:
                print(f"🔍 RAW LLM RESPONSE LENGTH: {len(text)} characters")
                print(f"🔍 RAW LLM RESPONSE (first 500 chars):")
                print("=" * 50)
                print(text[:500])
                print("=" * 50)
                
                # Clean up the response, removing markdown backticks if present
                original_text = text
                if text.startswith("```html"):
                    text = text[7:]
                    print("🔧 Removed ```html prefix")
                if text.endswith("```"):
                    text = text[:-3]
                    print("🔧 Removed ``` suffix")
                
                if text != original_text:
                    print(f"🔍 CLEANED LLM RESPONSE LENGTH: {len(text)} characters")
                    print(f"🔍 CLEANED LLM RESPONSE (first 500 chars):")
                    print("=" * 50)
                    print(text[:500])
                    print("=" * 50)
                
                print("✅ Gemini call completed successfully.")
                return text.strip()
            else:
                print("⚠️ Gemini returned no text, retrying…")

        except Exception as e:
            print(f"❌ Gemini call failed: {e}")

        attempt += 1
        if attempt < max_retries:
            print(f"⏳ Waiting {delay_sec} seconds before retry…")
            time.sleep(delay_sec)
        else:
            print("⚠️ Max retries reached. Giving up.")

    return None

def _escape(s: str | None) -> str:
    return html.escape(s or "")


def _fallback_sections(items: List[NewsItem], max_items: int = 30) -> str:
    parts: list[str] = []
    for it in items[:max_items]:
        published = it.published_at.isoformat() if it.published_at else ""
        parts.append(
            f"<li>[{_escape(it.source)}] <a href=\"{_escape(it.url)}\">{_escape(it.title)}</a> <small>{_escape(published)}</small></li>"
        )
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>CreatorPulse Fallback Report</title>
    <style>
        body {{ font-family: sans-serif; line-height: 1.6; }}
        ul {{ list-style-type: none; padding-left: 0; }}
        li {{ margin-bottom: 10px; }}
        a {{ text-decoration: none; color: #0066cc; }}
        small {{ color: #888; }}
    </style>
</head>
<body>
    <h1>CreatorPulse Fallback Report</h1>
    <p>The language model failed to generate a report. Here is a raw list of the latest items:</p>
    <h2>Latest</h2>
    <ul>{"\n".join(parts)}</ul>
</body>
</html>
"""
    return html_content.strip()


def make_report(items: List[NewsItem], config: Dict[str, Any]) -> str:
    """Return the raw LLM-generated full report (HTML or Markdown). Falls back to a simple HTML list."""
    items = dedupe_items(items)
    weights = (config.get("ranking", {}) or {}).get("source_weights", {})
    items = rank_items(items, weights=weights)
    
    llm_cfg = (config.get("llm") or {})
    use_llm = bool(llm_cfg.get("enabled"))
    
    if use_llm:
        print(f"⚡ Calling Gemini with {len(items)} items...")
        prompt = _make_llm_prompt_full_report(items, max_items=int(config.get("options", {}).get("max_items", 60)))
        text = _call_gemini(llm_cfg, prompt)
        if text:
            return text

    # Fallback: return a minimal HTML snippet
    print("⚠️ Using fallback report generation.")
    return _fallback_sections(items)

def load_news_items_from_json(file_path: str) -> List[NewsItem]:
    """Loads a list of NewsItem objects from a JSON file."""
    items = []
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for item_dict in data:
        # Convert ISO string back to datetime object
        if item_dict.get('published_at'):
            item_dict['published_at'] = datetime.fromisoformat(item_dict['published_at'])
        items.append(NewsItem(**item_dict))
    return items

def save_and_send_newsletter(report_html: str, user_id: str, send_email: bool = False, test_mode: bool = True) -> Optional[str]:
    """
    Save the generated report as a newsletter and optionally send it to clients.
    
    Args:
        report_html: The HTML content of the report
        user_id: ID of the user creating the newsletter
        send_email: Whether to send the newsletter via email
        test_mode: If True, only log what would be sent without actually sending
        
    Returns:
        str: Newsletter ID if saved successfully, None otherwise
    """
    try:
        # Generate title with timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d')
        title = f"CreatorPulse Daily Report - {timestamp}"
        
        # Save newsletter to database
        print(f"💾 Saving newsletter to database...")
        newsletter_id = save_newsletter(user_id, title, report_html, status='draft')
        print(f"✅ Newsletter saved with ID: {newsletter_id}")
        
        if send_email:
            print(f"📧 Preparing to send newsletter...")
            email_service = EmailService()
            
            # Get all clients for the user
            clients = fetch_clients(user_id)
            if not clients:
                print("⚠️ No clients found to send newsletter to")
                return newsletter_id
            
            client_ids = [client['id'] for client in clients]
            
            # Send newsletter
            result = email_service.create_and_send_newsletter(
                user_id=user_id,
                title=title,
                content=report_html,
                client_ids=client_ids,
                test_mode=test_mode
            )
            
            if result['success']:
                mode_text = "TEST MODE: " if test_mode else ""
                print(f"✅ {mode_text}Newsletter sent successfully!")
                print(f"   - Sent to: {result['sent_count']} clients")
                if result['failed_count'] > 0:
                    print(f"   - Failed: {result['failed_count']} clients")
                    for error in result.get('errors', []):
                        print(f"     • {error}")
            else:
                print(f"❌ Failed to send newsletter: {result.get('error', 'Unknown error')}")
        
        return newsletter_id
        
    except Exception as e:
        print(f"❌ Error saving/sending newsletter: {str(e)}")
        return None

def main():
    """
    Main function to generate the final HTML report from a JSON data file.
    Enhanced with database integration and email functionality.
    
    Usage:
        python consolidate.py <path_to_json_file> [user_id] [--send-email] [--live]
        
    Arguments:
        path_to_json_file: Path to the JSON file containing news items
        user_id: User ID for database operations (optional)
        --send-email: Send newsletter via email (optional)
        --live: Send actual emails instead of test mode (optional)
    """
    load_dotenv() # Load environment variables from .env file
    
    if len(sys.argv) < 2:
        print("Usage: python consolidate.py <path_to_json_file> [user_id] [--send-email] [--live]")
        print("  path_to_json_file: Path to the JSON file containing news items")
        print("  user_id: User ID for database operations (optional)")
        print("  --send-email: Send newsletter via email (optional)")
        print("  --live: Send actual emails instead of test mode (optional)")
        sys.exit(1)
        
    json_file_path = sys.argv[1]
    user_id = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else None
    send_email = '--send-email' in sys.argv
    live_mode = '--live' in sys.argv
    test_mode = not live_mode
    
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("❌ config.yaml not found. Please create it.")
        sys.exit(1)

    print(f"📰 Loading data from {json_file_path}...")
    news_items = load_news_items_from_json(json_file_path)
    
    if not news_items:
        print("❌ No news items found in the JSON file. Exiting.")
        return
        
    print(f"🔄 Processing {len(news_items)} news items...")
    report_html = make_report(news_items, config)
    
    # Save the final report to a file (legacy behavior)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_filename = f"report_{timestamp}.html"
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(report_html)
        
    print(f"✅ Successfully generated and saved report to {report_filename}")
    
    # Database and email integration
    if user_id:
        print(f"👤 User ID provided: {user_id}")
        newsletter_id = save_and_send_newsletter(
            report_html=report_html,
            user_id=user_id,
            send_email=send_email,
            test_mode=test_mode
        )
        
        if newsletter_id:
            print(f"📄 Newsletter saved to database with ID: {newsletter_id}")
            if send_email:
                mode_text = "test mode" if test_mode else "live mode"
                print(f"📧 Email sending completed in {mode_text}")
        else:
            print("❌ Failed to save newsletter to database")
    else:
        print("ℹ️  No user ID provided. Skipping database and email operations.")
        print("   To use database features, provide a user ID as the second argument.")
        print("   Example: python consolidate.py data.json your-user-id --send-email")

if __name__ == "__main__":
    main()