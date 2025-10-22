"""
API routes for CreatorPulse FastAPI backend
Implements the endpoints specified in API_INTEGRATION.md
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from pydantic import BaseModel, Field

# Import models and dependencies
from supabase_client import fetch_active_sources, fetch_clients
from email_service import EmailService
from consolidate import make_report
from main_scraper import scrape_for_user

logger = logging.getLogger(__name__)

# Pydantic models (duplicated from main.py to avoid circular imports)
class Source(BaseModel):
    id: str
    source_type: str = Field(..., pattern="^(rss|youtube|reddit|blog|podcast|other)$")
    source_name: str
    source_identifier: str
    active: bool = True

class GenerateDraftRequest(BaseModel):
    newsletterId: str
    sources: List[Source]

class GenerateDraftResponse(BaseModel):
    draft: str
    sources_used: List[str]
    generation_time: str

class SendNewsletterRequest(BaseModel):
    newsletterId: str
    clientIds: List[str]
    scheduledTime: Optional[str] = None
    sendImmediately: bool = True

class SendNewsletterResponse(BaseModel):
    success: bool
    message: str
    recipients: int
    scheduledFor: Optional[str] = None

class ContentItem(BaseModel):
    title: str
    url: str
    published_at: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None

class SourceContentResponse(BaseModel):
    source_id: str
    content: List[ContentItem]
    last_scraped: str


class TestEmailRequest(BaseModel):
    to_email: str
    subject: str = "Test Email from CreatorPulse"
    message: str = "This is a test email to verify SMTP configuration."


# Authentication dependency
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate user authentication using Supabase JWT token"""
    from supabase_client import get_supabase_client
    
    try:
        token = credentials.credentials
        supabase_client = get_supabase_client()
        
        # Validate token with Supabase
        user_response = supabase_client.auth.get_user(token)
        
        if not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        return user_response.user
    
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

# Create API router
router = APIRouter(prefix="/api", tags=["CreatorPulse API"])

@router.post("/generate-draft", response_model=GenerateDraftResponse)
async def generate_newsletter_draft(
    request: GenerateDraftRequest,
    current_user = Depends(get_current_user)
):
    """
    Generate a newsletter draft using LLM based on provided sources
    """
    try:
        logger.info(f"Generating draft for newsletter {request.newsletterId}")
        logger.info(f"User ID: {current_user.id if current_user else 'None'}")
        logger.info(f"Number of sources provided: {len(request.sources)}")
        
        # Get supabase client
        from supabase_client import get_supabase_client
        supabase_client = get_supabase_client()
        logger.info("✅ Supabase client initialized")
        
        # Validate newsletter exists and belongs to user (skip if newsletterId is 'new')
        if request.newsletterId != 'new':
            newsletter_response = supabase_client.table('newsletters')\
                .select('*')\
                .eq('id', request.newsletterId)\
                .eq('user_id', current_user.id)\
                .execute()
            
            if not newsletter_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Newsletter not found or access denied"
                )
        
        # Convert sources to the format expected by scraper
        source_identifiers = []
        sources_used = []
        
        for source in request.sources:
            if source.active:
                source_identifiers.append(source.source_identifier)
                sources_used.append(source.id)
        
        if not source_identifiers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active sources provided"
            )
        
        # Scrape content from sources
        logger.info(f"Scraping content from {len(source_identifiers)} sources")
        logger.info(f"Source identifiers: {source_identifiers}")
        
        try:
            news_items = scrape_for_user(current_user.id)
            logger.info(f"✅ Scraping completed, got {len(news_items) if news_items else 0} items")
        except Exception as scrape_error:
            logger.error(f"❌ Scraping failed: {str(scrape_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Scraping failed: {str(scrape_error)}"
            )
        
        if not news_items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No content found from provided sources"
            )
        
        # Load configuration
        import yaml
        try:
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning("⚠️ config.yaml not found, using defaults")
            config = {
                'llm': {'enabled': True, 'model': 'gemini-2.5-flash'},
                'ranking': {'source_weights': {'reddit': 10.0, 'rss': 5.0, 'youtube': 7.0, 'blog': 5.0}},
                'options': {'max_items': 60}
            }
        
        # Generate report using LLM
        logger.info(f"Generating report from {len(news_items)} items")
        logger.info(f"Config loaded: {config is not None}")
        
        try:
            draft_html = make_report(news_items, config)
            logger.info(f"✅ Report generated successfully, length: {len(draft_html) if draft_html else 0}")
        except Exception as report_error:
            logger.error(f"❌ Report generation failed: {str(report_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Report generation failed: {str(report_error)}"
            )
        
        # Update newsletter with generated content (only if not 'new')
        generation_time = datetime.now(timezone.utc)
        
        if request.newsletterId != 'new':
            supabase_client.table('newsletters')\
                .update({
                    'content': draft_html,
                    'status': 'draft',
                    'updated_at': generation_time.isoformat()
                })\
                .eq('id', request.newsletterId)\
                .execute()
        
        logger.info(f"✅ Draft generated successfully for newsletter {request.newsletterId}")
        
        return GenerateDraftResponse(
            draft=draft_html,
            sources_used=sources_used,
            generation_time=generation_time.isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating draft: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate draft: {str(e)}"
        )

@router.post("/send-newsletter", response_model=SendNewsletterResponse)
async def send_newsletter(
    request: SendNewsletterRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """
    Send or schedule newsletter for the user
    """
    from datetime import datetime, timezone
    from dateutil import parser

    try:
        logger.info(f"Sending newsletter {request.newsletterId}")

        # Get Supabase client
        from supabase_client import get_supabase_client
        supabase_client = get_supabase_client()

        # Validate newsletter ownership
        newsletter_response = supabase_client.table('newsletters')\
            .select('*')\
            .eq('id', request.newsletterId)\
            .eq('user_id', current_user.id)\
            .execute()

        if not newsletter_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Newsletter not found or access denied"
            )

        newsletter = newsletter_response.data[0]

        # Validate or fetch clients
        if request.clientIds:
            logger.info(f"Client IDs provided: {request.clientIds}")
            client_response = supabase_client.table('clients')\
                .select('id')\
                .eq('user_id', current_user.id)\
                .in_('id', request.clientIds)\
                .execute()

            valid_client_ids = [client['id'] for client in client_response.data]
            if len(valid_client_ids) != len(request.clientIds):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Some client IDs are invalid or don't belong to user"
                )
        else:
            # Fetch all user clients
            all_clients = fetch_clients(current_user.id)
            request.clientIds = [client['id'] for client in all_clients]

        if not request.clientIds:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No clients found to send newsletter to. Please add clients first."
            )

        # Initialize email service
        try:
            email_service = EmailService()
            logger.info("✅ Email service initialized successfully")
        except Exception as email_init_error:
            logger.error(f"❌ Failed to initialize email service: {str(email_init_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Email service initialization failed: {str(email_init_error)}"
            )

        # -------------------- IMMEDIATE SEND --------------------
        if request.sendImmediately:
            logger.info(f"📤 Sending newsletter immediately to {len(request.clientIds)} clients")

            try:
                result = email_service.create_and_send_newsletter(
                    user_id=current_user.id,
                    title=newsletter['title'],
                    content=newsletter['content'],
                    client_ids=request.clientIds,
                    test_mode=False
                )

                if not result['success']:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to send newsletter: {result.get('error', 'Unknown error')}"
                    )

                # Update status
                supabase_client.table('newsletters')\
                    .update({
                        'status': 'sent',
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    })\
                    .eq('id', request.newsletterId)\
                    .execute()

                return SendNewsletterResponse(
                    success=True,
                    message="Newsletter sent successfully",
                    recipients=result['sent_count'],
                    scheduledFor=None
                )

            except Exception as e:
                logger.error(f"Email service error: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Email service failed: {str(e)}"
                )

        # -------------------- SCHEDULED SEND --------------------
        else:
            if not request.scheduledTime:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="scheduledTime required when sendImmediately is false"
                )

            # Parse ISO time robustly
            try:
                scheduled_dt = parser.isoparse(request.scheduledTime)

                # If scheduled time has no tzinfo → assume UTC
                if scheduled_dt.tzinfo is None:
                    logger.warning(f"⚠️ Scheduled time {request.scheduledTime} has no timezone info — assuming UTC.")
                    scheduled_dt = scheduled_dt.replace(tzinfo=timezone.utc)

                # Use timezone-aware current time
                current_time = datetime.now(timezone.utc)

                # If scheduled time is in past or now → send immediately
                if scheduled_dt <= current_time:
                    logger.info(f"📤 Scheduled time is in past/now ({scheduled_dt}), sending immediately.")

                    result = email_service.create_and_send_newsletter(
                        user_id=current_user.id,
                        title=newsletter['title'],
                        content=newsletter['content'],
                        client_ids=request.clientIds,
                        test_mode=False
                    )

                    if result['success']:
                        supabase_client.table('newsletters')\
                            .update({
                                'status': 'sent',
                                'updated_at': datetime.now(timezone.utc).isoformat()
                            })\
                            .eq('id', request.newsletterId)\
                            .execute()

                        return SendNewsletterResponse(
                            success=True,
                            message="Newsletter sent immediately (was scheduled for now)",
                            recipients=result['sent_count'],
                            scheduledFor=None
                        )
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to send newsletter: {result.get('error', 'Unknown error')}"
                        )

                # Future scheduling → save to DB
                supabase_client.table('newsletters')\
                    .update({
                        'status': 'scheduled',
                        'scheduled_time': scheduled_dt.isoformat(),
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    })\
                    .eq('id', request.newsletterId)\
                    .execute()

                logger.info(f"📅 Newsletter {request.newsletterId} scheduled for {scheduled_dt}")

                return SendNewsletterResponse(
                    success=True,
                    message="Newsletter scheduled successfully",
                    recipients=len(request.clientIds),
                    scheduledFor=scheduled_dt.isoformat()
                )

            except ValueError as date_error:
                logger.error(f"Invalid scheduledTime format: {request.scheduledTime}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid scheduledTime format: {str(date_error)}"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending newsletter: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send newsletter: {str(e)}"
        )


@router.get("/sources/{source_id}/content", response_model=SourceContentResponse)
async def get_source_content(
    source_id: str,
    current_user = Depends(get_current_user)
):
    """
    Get scraped content from a specific source
    """
    try:
        logger.info(f"Getting content for source {source_id}")
        
        # Validate source exists and belongs to user
        from supabase_client import get_supabase_client
        supabase_client = get_supabase_client()
        
        source_response = supabase_client.table('sources')\
            .select('*')\
            .eq('id', source_id)\
            .eq('user_id', current_user.id)\
            .execute()
        
        if not source_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source not found or access denied"
            )
        
        source = source_response.data[0]
        
        # Import appropriate scraper based on source type
        source_type = source['source_type']
        source_identifier = source['source_identifier']
        
        news_items = []
        
        if source_type == 'reddit':
            from scraper.reddit_scraper import fetch_from_reddit
            news_items = fetch_from_reddit([source_identifier], limit=20)
        
        elif source_type == 'rss':
            from scraper.rss_scraper import fetch_from_rss
            news_items = fetch_from_rss([source_identifier], max_items_per_feed=20)
        
        elif source_type == 'youtube':
            from scraper.youtube_scraper import fetch_from_youtube
            news_items = fetch_from_youtube([source_identifier])
        
        elif source_type == 'blog':
            from scraper.blog_scraper import fetch_from_blog
            news_items = fetch_from_blog([source_identifier])
        
        elif source_type == 'other':
            from scraper.other_scraper import fetch_from_other
            news_items = fetch_from_other([source_identifier])
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported source type: {source_type}"
            )
        
        # Convert NewsItem objects to ContentItem format
        content_items = []
        for item in news_items:
            content_items.append(ContentItem(
                title=item.title,
                url=item.url,
                published_at=item.published_at.isoformat() if item.published_at else None,
                summary=item.summary,
                content=item.summary  # Using summary as content for now
            ))
        
        logger.info(f"✅ Retrieved {len(content_items)} items from source {source_id}")
        
        return SourceContentResponse(
            source_id=source_id,
            content=content_items,
            last_scraped=datetime.now(timezone.utc).isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting source content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get source content: {str(e)}"
        )

# Additional utility endpoints

@router.get("/sources")
async def get_user_sources(current_user = Depends(get_current_user)):
    """Get all sources for the current user"""
    try:
        sources = fetch_active_sources(current_user.id)
        return {"sources": sources}
    except Exception as e:
        logger.error(f"Error getting user sources: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sources: {str(e)}"
        )

@router.get("/clients")
async def get_user_clients(current_user = Depends(get_current_user)):
    """Get all clients for the current user"""
    try:
        clients = fetch_clients(current_user.id)
        return {"clients": clients}
    except Exception as e:
        logger.error(f"Error getting user clients: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get clients: {str(e)}"
        )

@router.get("/newsletters")
async def get_user_newsletters(current_user = Depends(get_current_user)):
    """Get all newsletters for the current user"""
    try:
        from supabase_client import get_supabase_client
        supabase_client = get_supabase_client()
        
        response = supabase_client.table('newsletters')\
            .select('*')\
            .eq('user_id', current_user.id)\
            .order('created_at', desc=True)\
            .execute()
        
        return {"newsletters": response.data}
    except Exception as e:
        logger.error(f"Error getting user newsletters: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get newsletters: {str(e)}"
        )

@router.get("/test")
async def test_endpoint():
    """Test endpoint without authentication"""
    return {
        "message": "API is working!",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "healthy"
    }

@router.post("/test-email")
async def test_email(
    request: TestEmailRequest,
    current_user = Depends(get_current_user)
):
    """
    Test email sending functionality
    
    This endpoint allows you to test the email sending functionality with custom parameters.
    It's protected and requires authentication.
    """
    try:
        logger.info(f"Testing email to {request.to_email}")
        
        # Initialize email service
        try:
            email_service = EmailService()
            logger.info("✅ Email service initialized successfully")
        except Exception as email_init_error:
            logger.error(f"❌ Failed to initialize email service: {str(email_init_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Email service initialization failed: {str(email_init_error)}"
            )
        
        # Create HTML content
        html_content = f"""
        <html>
            <body>
                <h1>Test Email from CreatorPulse</h1>
                <p>{request.message}</p>
                <p>This email was sent to test the SMTP configuration.</p>
                <p>Current time: {datetime.now(timezone.utc).isoformat()}</p>
            </body>
        </html>
        """
        
        # Send the test email
        success = email_service.send_email(
            to_email=request.to_email,
            subject=request.subject,
            html_content=html_content,
            text_content=request.message
        )
        
        if success:
            logger.info(f"✅ Test email sent successfully to {request.to_email}")
            return {
                "success": True,
                "message": f"Test email sent successfully to {request.to_email}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            logger.error(f"❌ Failed to send test email to {request.to_email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send test email to {request.to_email}. Check server logs for details."
            )
            
    except Exception as e:
        logger.error(f"❌ Error in test_email endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while sending test email: {str(e)}"
        )

@router.get("/scheduled-newsletters")
async def get_scheduled_newsletters(current_user = Depends(get_current_user)):
    """Get all scheduled newsletters for the current user"""
    try:
        from supabase_client import get_supabase_client
        supabase_client = get_supabase_client()
        
        response = supabase_client.table('newsletters')\
            .select('*')\
            .eq('user_id', current_user.id)\
            .eq('status', 'scheduled')\
            .order('scheduled_time', desc=False)\
            .execute()
        
        return {
            "scheduled_newsletters": response.data,
            "count": len(response.data) if response.data else 0
        }
    except Exception as e:
        logger.error(f"Error getting scheduled newsletters: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scheduled newsletters: {str(e)}"
        )

