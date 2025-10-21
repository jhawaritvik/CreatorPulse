# CreatorPulse Frontend

This is the React-based frontend for CreatorPulse. It provides the user interface for managing sources, clients, and newsletters.

## Features

-   **User Authentication:** Login and signup functionality using Supabase Auth.
-   **Dashboard:** An overview of sources, clients, and newsletters.
-   **Source Management:** Add, edit, delete, and view content sources.
-   **Client Management:** Add, edit, and delete clients (newsletter recipients).
-   **Newsletter Editor:** Create, edit, and generate newsletter drafts from sources.
-   **Newsletter Sending:** Send newsletters immediately or schedule them for later.

## Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd creatorpulse-frontend
    ```

2.  **Install Dependencies:**
    ```bash
    npm install
    ```

3.  **Environment Setup:**
    Create a `.env` file in this directory. You'll need to add your Supabase project's URL and anon key. These are different from the backend's service role key.

    ```env
    REACT_APP_SUPABASE_URL=your_supabase_url
    REACT_APP_SUPABASE_ANON_KEY=your_supabase_anon_key
    REACT_APP_API_BASE_URL=http://localhost:8001
    ```

    -   `REACT_APP_SUPABASE_URL` and `REACT_APP_SUPABASE_ANON_KEY` can be found in your Supabase project's API settings.
    -   `REACT_APP_API_BASE_URL` should point to your running backend server.

## Running the Development Server

Once the setup is complete, you can start the React development server:

```bash
npm start
```

This will open the application in your default browser at `http://localhost:3000`. The app will automatically reload if you make changes to the code.

## Available Scripts

In the project directory, you can run:

-   `npm start`: Runs the app in development mode.
-   `npm test`: Launches the test runner in interactive watch mode.
-   `npm run build`: Builds the app for production to the `build` folder.
-   `npm run eject`: Removes the single-dependency configuration from the project.
