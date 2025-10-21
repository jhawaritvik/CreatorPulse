# FastAPI Integration Endpoints

This document outlines the expected API endpoints for the FastAPI backend integration.

## Newsletter Draft Generation

**Endpoint:** `POST /api/generate-draft`

**Request Body:**
```json
{
  "newsletterId": "uuid",
  "sources": [
    {
      "id": "uuid",
      "source_type": "rss|youtube|twitter|blog|podcast|other",
      "source_name": "string",
      "source_identifier": "string",
      "active": true
    }
  ]
}
```

**Response:**
```json
{
  "draft": "Generated newsletter content as markdown/text",
  "sources_used": ["source_id_1", "source_id_2"],
  "generation_time": "2024-01-01T12:00:00Z"
}
```

## Newsletter Sending

**Endpoint:** `POST /api/send-newsletter`

**Request Body:**
```json
{
  "newsletterId": "uuid",
  "clientIds": ["client_id_1", "client_id_2"],
  "scheduledTime": "2024-01-01T12:00:00Z" | null,
  "sendImmediately": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Newsletter sent successfully",
  "recipients": 5,
  "scheduledFor": "2024-01-01T12:00:00Z" | null
}
```

## Source Content Scraping

**Endpoint:** `GET /api/sources/{source_id}/content`

**Response:**
```json
{
  "source_id": "uuid",
  "content": [
    {
      "title": "Article Title",
      "url": "https://example.com/article",
      "published_at": "2024-01-01T12:00:00Z",
      "summary": "Article summary",
      "content": "Full article content"
    }
  ],
  "last_scraped": "2024-01-01T12:00:00Z"
}
```

## Implementation Notes

1. **Authentication**: All endpoints should validate the user's session/token
2. **Rate Limiting**: Implement appropriate rate limiting for API calls
3. **Error Handling**: Return proper HTTP status codes and error messages
4. **Logging**: Log all API calls for debugging and monitoring
5. **Caching**: Consider caching scraped content to reduce API calls

## Current Status

- ✅ Frontend components ready for integration
- ✅ Database schema supports all required fields
- ⏳ FastAPI backend implementation pending
- ⏳ Source scraping logic pending
- ⏳ LLM integration for draft generation pending
- ⏳ Email sending service integration pending
