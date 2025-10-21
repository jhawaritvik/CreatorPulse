"""
FastAPI backend for CreatorPulse
Integrates with existing scraping, LLM, and email functionality
"""

import os
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import uvicorn
from dotenv import load_dotenv

# Import existing backend functionality
from supabase_client import get_supabase_client, fetch_clients, save_newsletter, fetch_active_sources
from email_service import EmailService
from consolidate import make_report, load_news_items_from_json, save_and_send_newsletter
from main_scraper import scrape_for_user
from scraper.news_item import NewsItem
from scheduler import scheduler  # Import the scheduler instance
import yaml

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Global variables
supabase = None
config = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources"""
    global supabase, config
    
    # Startup
    logger.info("🚀 Starting CreatorPulse FastAPI backend...")
    supabase = get_supabase_client()
    
    # Load configuration
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        logger.info("✅ Configuration loaded")
    except FileNotFoundError:
        logger.warning("⚠️ config.yaml not found, using defaults")
        config = {
            'llm': {'enabled': True, 'model': 'gemini-2.5-flash'},
            'ranking': {'source_weights': {'reddit': 10.0, 'rss': 5.0, 'youtube': 7.0, 'blog': 5.0}},
            'options': {'max_items': 60}
        }
    
    # Start the background scheduler
    try:
        if not scheduler.running:
            scheduler.start()
            logger.info("✅ Background scheduler started")
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}")

    logger.info("✅ CreatorPulse backend initialized")
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down CreatorPulse backend...")
    if scheduler.running:
        scheduler.shutdown()
        logger.info("✅ Background scheduler shut down")

# Create FastAPI app
app = FastAPI(
    title="CreatorPulse API",
    description="Backend API for CreatorPulse newsletter generation and management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
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

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validate user authentication using Supabase JWT token
    """
    try:
        # In a real implementation, you would validate the JWT token with Supabase
        # For now, we'll extract user info from the token
        token = credentials.credentials
        
        # Validate token with Supabase
        user_response = supabase.auth.get_user(token)
        
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

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }

# Include API routes (import after app creation to avoid circular imports)
# This will be done at the end of the file

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "CreatorPulse API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Include API routes after all dependencies are set up
from api_routes import router as api_router
app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
