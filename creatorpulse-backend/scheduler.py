import logging
from datetime import datetime, timezone
from dateutil import parser
from apscheduler.schedulers.background import BackgroundScheduler
from supabase_client import get_supabase_client
from email_service import EmailService

logger = logging.getLogger(__name__)

def send_scheduled_newsletters():
    """
    Checks for newsletters with status='scheduled' and scheduled_time <= now,
    sends them, and updates their status to 'sent'.
    """
    try:
        supabase_client = get_supabase_client()
        email_service = EmailService()
        now_utc = datetime.now(timezone.utc)

        response = supabase_client.table('newsletters')\
            .select('*')\
            .eq('status', 'scheduled')\
            .execute()

        newsletters = response.data or []

        for nl in newsletters:
            scheduled_time = nl.get('scheduled_time')
            if not scheduled_time:
                continue

            # Use dateutil.parser for robust ISO 8601 parsing with timezone
            try:
                scheduled_dt = parser.isoparse(scheduled_time)
            except ValueError:
                logger.warning(f"Could not parse scheduled_time '{scheduled_time}' for newsletter {nl['id']}. Skipping.")
                continue

            # Ensure both datetimes are timezone-aware for comparison
            if scheduled_dt.tzinfo is None:
                # If for some reason the stored time is naive, assume UTC as a fallback
                scheduled_dt = scheduled_dt.replace(tzinfo=timezone.utc)

            if scheduled_dt <= now_utc:
                # Fetch clients for this user
                user_id = nl['user_id']
                client_response = supabase_client.table('clients')\
                    .select('id')\
                    .eq('user_id', user_id)\
                    .execute()
                client_ids = [c['id'] for c in client_response.data] if client_response.data else []

                if not client_ids:
                    logger.warning(f"No clients found for newsletter {nl['id']}")
                    continue

                # Send email
                result = email_service.create_and_send_newsletter(
                    user_id=user_id,
                    title=nl['title'],
                    content=nl['content'],
                    client_ids=client_ids,
                    test_mode=False
                )

                if result.get('success'):
                    supabase_client.table('newsletters')\
                        .update({
                            'status': 'sent',
                            'updated_at': datetime.now(timezone.utc).isoformat()
                        })\
                        .eq('id', nl['id'])\
                        .execute()
                    logger.info(f"✅ Newsletter {nl['id']} sent successfully to {len(client_ids)} recipients")
                else:
                    logger.error(f"❌ Failed to send newsletter {nl['id']}: {result.get('error')}")

    except Exception as e:
        logger.error(f"Error in sending scheduled newsletters: {str(e)}")

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(send_scheduled_newsletters, 'interval', minutes=1)
scheduler.start()
logger.info("📅 Scheduler started for sending scheduled newsletters every 1 minute")
