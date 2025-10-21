
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv(dotenv_path='creatorpulse-backend/.env')

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def check_newsletters():
    response = supabase.table('newsletters').select('id, title, created_at, updated_at').order('created_at', desc=True).limit(5).execute()
    if response.data:
        for newsletter in response.data:
            print(newsletter)
    else:
        print("No newsletters found.")

if __name__ == "__main__":
    check_newsletters()
