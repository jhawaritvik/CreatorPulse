import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def get_supabase_client() -> Client:
    """Initializes and returns the Supabase client."""
    url = os.environ.get("CREATORPULSE_SUPABASE_URL")
    key = os.environ.get("CREATORPULSE_SUPABASE_KEY")
    if not url or not key:
        raise ValueError("Supabase URL and key must be set in .env file.")
    return create_client(url, key)

def fetch_active_sources(user_id: str) -> list:
    """Fetches all active sources for a given user."""
    supabase = get_supabase_client()
    # Implementation to fetch from 'sources' table
    response = supabase.table('sources').select('*').eq('user_id', user_id).eq('active', True).execute()
    return response.data

def fetch_clients(user_id: str) -> list:
    """Fetches all clients for a given user."""
    supabase = get_supabase_client()
    # Implementation to fetch from 'clients' table
    response = supabase.table('clients').select('*').eq('user_id', user_id).execute()
    return response.data

def save_newsletter(user_id: str, title: str, content: str, status: str = 'draft') -> str:
    """Saves a newsletter to the database and returns the newsletter ID."""
    from datetime import datetime, timezone
    
    supabase = get_supabase_client()
    newsletter_data = {
        'user_id': user_id,
        'title': title,
        'content': content,
        'status': status,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat()
    }
    
    response = supabase.table('newsletters').insert(newsletter_data).execute()
    if response.data:
        return response.data[0]['id']
    else:
        raise Exception("Failed to save newsletter to database")

def get_newsletter(newsletter_id: str) -> dict:
    """Retrieves a newsletter by ID."""
    supabase = get_supabase_client()
    response = supabase.table('newsletters').select('*').eq('id', newsletter_id).execute()
    if response.data:
        return response.data[0]
    else:
        raise Exception(f"Newsletter with ID {newsletter_id} not found")

def update_newsletter_status(newsletter_id: str, status: str) -> bool:
    """Updates the status of a newsletter."""
    from datetime import datetime, timezone
    
    supabase = get_supabase_client()
    response = supabase.table('newsletters').update({
        'status': status,
        'updated_at': datetime.now(timezone.utc).isoformat()
    }).eq('id', newsletter_id).execute()
    
    return bool(response.data)
