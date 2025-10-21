# CreatorPulse

CreatorPulse is a full-stack application designed to help content creators and businesses automate the process of creating and distributing newsletters. It scrapes content from various sources (like RSS feeds, Reddit, and YouTube), uses a language model to generate a newsletter draft, and sends it to a list of clients.

This project is divided into two main parts:

-   **[Backend (FastAPI)](creatorpulse-backend/README.md):** A Python-based backend powered by FastAPI that handles content scraping, newsletter generation, and email sending.
-   **[Frontend (React)](creatorpulse-frontend/README.md):** A React-based single-page application for managing sources, clients, and newsletters.

## Quick Start

To get the entire application running, you will need to start both the backend and frontend servers.

### Backend

1.  **Navigate to the backend directory:**
    ```bash
    cd creatorpulse-backend
    ```
2.  **Follow the setup instructions** in the [backend README](creatorpulse-backend/README.md).
3.  **Start the backend server:**
    ```bash
    python start_api.py
    ```
    The API will be running at `http://localhost:8001`.

### Frontend

1.  **Navigate to the frontend directory:**
    ```bash
    cd creatorpulse-frontend
    ```
2.  **Follow the setup instructions** in the [frontend README](creatorpulse-frontend/README.md).
3.  **Start the frontend development server:**
    ```bash
    npm start
    ```
    The frontend will be accessible at `http://localhost:3000`.

## Project Structure

```
.
├── creatorpulse-backend/     # FastAPI backend
├── creatorpulse-frontend/    # React frontend
└── README.md                 # This file
```