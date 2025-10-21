# CreatorPulse FastAPI Backend

This FastAPI backend integrates with the existing CreatorPulse functionality to provide REST API endpoints for the frontend.

## Features

- ✅ **Newsletter Draft Generation** - Generate newsletters using LLM from scraped sources
- ✅ **Newsletter Sending** - Send newsletters to clients via email
- ✅ **Source Content Scraping** - Scrape content from various sources (Reddit, RSS, YouTube, etc.)
- ✅ **Authentication** - Supabase JWT token validation
- ✅ **CORS Support** - Frontend integration ready
- ✅ **Error Handling** - Proper HTTP status codes and error messages
- ✅ **Logging** - Comprehensive logging for debugging

## Installation

1.  **Navigate to the backend directory:**
    ```bash
    cd creatorpulse-backend
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**
    -   Windows: `venv\Scripts\activate`
    -   macOS/Linux: `source venv/bin/activate`

4.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Environment Setup**:
    Create a `.env` file in this directory and ensure it contains all required variables:
    ```env
    # Supabase
    CREATORPULSE_SUPABASE_URL=your_supabase_url
    CREATORPULSE_SUPABASE_KEY=your_supabase_key

    # Gemini AI
    GEMINI_API_KEY=your_gemini_api_key

    # SMTP Email
    SMTP_SERVER=smtp.gmail.com
    SMTP_PORT=587
    SMTP_USERNAME=your_email@gmail.com
    SMTP_PASSWORD=your_app_password
    FROM_EMAIL=your_email@gmail.com
    FROM_NAME=CreatorPulse

    # Optional API Configuration
    API_HOST=0.0.0.0
    API_PORT=8001
    API_RELOAD=true
    ```

## Running the Server

### Option 1: Using the startup script (Recommended)
```bash
python start_api.py
```

### Option 2: Direct uvicorn
```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

The API will be available at `http://localhost:8001` and the interactive documentation at `http://localhost:8001/docs`.

## API Endpoints

### Core Endpoints

- **`GET /`** - API information
- **`GET /health`** - Health check
- **`GET /docs`** - Interactive API documentation (Swagger UI)

### Newsletter Management

- **`POST /api/generate-draft`** - Generate newsletter draft from sources
- **`POST /api/send-newsletter`** - Send newsletter to clients
- **`GET /api/newsletters`** - Get user's newsletters

### Source Management

- **`GET /api/sources/{source_id}/content`** - Get content from specific source
- **`GET /api/sources`** - Get user's sources

### Client Management

- **`GET /api/clients`** - Get user's clients

## Authentication

All API endpoints (except `/`, `/health`, `/docs`) require authentication using Supabase JWT tokens passed in the `Authorization` header.