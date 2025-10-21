#!/usr/bin/env python3
"""
Startup script for CreatorPulse FastAPI backend
"""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8001"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"
    
    print("🚀 Starting CreatorPulse FastAPI Backend")
    print(f"📡 Server: http://{host}:{port}")
    print(f"📚 API Docs: http://{host}:{port}/docs")
    print(f"🔄 Reload: {reload}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
