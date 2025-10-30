Here is the standalone README file for the `client/` local server.

-----

# DealTracker Local Server (Client)

This is the "smart client" backend for the **DealTracker** application. It is a local server that runs on the user's machine, acting as the engine and secure gateway for the DealTracker Frontend.

It is designed to communicate with the DealTracker Auth Backend (the "Main Backend") for authentication and master product list synchronization.

## 🏛️ The "Smart Client" Architecture

This application is not just a simple backend; it's a sophisticated local service with a "smart client" architecture.

  * **Serves the UI:** It runs a `FastAPI` server on `127.0.0.1:8001` that serves the static (built) React frontend.
  * **Secure Session Vault:** It *never* stores JWTs in the browser. Instead, it holds them in a local, encrypted `session.vault` file, tied to a device fingerprint.
  * **Local Caching:** It maintains a **local SQLite database** (`dealtracker_client.db`) to cache all user data (products, price history, activity logs). This makes the UI feel instantaneous.
  * **Local Task Runner:** It runs its own `APScheduler` to perform web scraping tasks (`scraper.py`) in the background on the user's machine, distributing the scraping load.
  * **Real-time Proxy:** It provides a local API (`/api/...`) for the frontend to consume. It either serves data from its local cache or proxies requests securely to the Main Backend.

## ✨ Core Features

  * **Secure Local Session Vault:** User authentication tokens are stored on disk in a `session.vault` file, encrypted using `Fernet` (from the `cryptography` package). Access is tied to a master key and a unique device fingerprint.
  * **Local Database Cache:** Uses `SQLAlchemy` and `SQLite` to maintain a local copy of all essential data. This provides a fast user experience and a persistent log of price history and activity.
  * **Data Synchronization:** A `SyncManager` handles keeping the local `ProductCache` in sync with the master product list from the Main Backend.
  * **Automated Background Scraping:** A background `APScheduler` (from `scheduler.py`) periodically triggers a local, asynchronous web scraping task.
  * **Intelligent Scraper:** Uses `crawl4ai` (`scraper.py`) to perform advanced, browser-based scraping of product pages, extract prices, and update the local database.
  * **Real-time SSE Notifications:** When the local scraper detects a price drop, it uses a `SSEManager` (`realtime/alert_sse.py`) to push a live notification directly to the connected frontend, triggering an instant alert.
  * **Secure API Proxy:** The `remote_api.py` client is the only component that communicates with the Main Backend. It handles all authentication, error handling, and automatic token refreshing.
  * **Self-Contained API:** Provides a complete set of local API endpoints (`routes/`) for the frontend to manage products, view analytics, and control the scheduler.

## 🛠️ Tech Stack

  * **Framework:** `FastAPI`
  * **Web Server:** `Uvicorn`
  * **Database:** `SQLAlchemy` with `SQLite`
  * **Scraping:** `crawl4ai`
  * **Background Tasks:** `APScheduler`
  * **Remote Comms:** `requests`
  * **Local Security:** `cryptography` (Fernet)

## 🚀 Installation & Running

This application is designed to run as a local service and serve the production build of the `Frontend/` application.

### Prerequisites

1.  The **DealTracker Auth Backend** (Main Server) *must* be running and accessible over the network.
2.  The **DealTracker Frontend** (`Frontend/`) *must* be built (`npm run build`).
3.  Python 3.10+

### Setup

1.  **Configure Environment:**
    Create a `.env` file. This file must specify the location of your Main Backend:

    ```.env
    # The URL of your remote "DealTracker Auth Backend"
    SERVER_BASE_URL="http://localhost:8000"
    ```

2.  **Install Python Dependencies:**
    It is highly recommended to use a virtual environment.

    ```bash
    # Create a virtual environment
    python -m venv venv

    # On macOS/Linux
    source venv/bin/activate

    # On Windows
    .\venv\Scripts\activate

    # Install requirements
    uv sync
    or 
    pip install -r requirements.txt
    ```

3.  **Add the Frontend Build:**
    The server expects the built React app to be in a `client/dist` directory.

    ```bash
    # From the project root, build the frontend
    cd ../Frontend
    npm run build

    # Go back to the root
    cd ..

    # Create the 'dist' directory inside 'client'
    mkdir -p client/dist

    # Copy the built frontend assets into the server's static folder
    cp -r Frontend/dist/* client/dist/
    ```

4.  **Run the Server:**

    ```bash
    python main.py
    ```

This will start the FastAPI server on `http://127.0.0.1:8001`. The script will automatically try to open this URL in your default web browser, launching the DealTracker application.

## 📂 Project Structure (Key Files)

```
client/
├── __init__.py
├── api.py                   # The main FastAPI app: serves static files, includes routes
├── client_auth.py           # Manages the local ENCRYPTED session vault
├── database.py              # Manages the local SQLITE database cache
├── dependencies.py          # Creates and shares all singleton instances (db, auth, api)
├── main.py                  # The main entry point to run the server
├── remote_api.py            # The API client that talks to the MAIN BACKEND
├── requirements.txt
├── scheduler.py             # Manages the APScheduler for background tasks
├── scraper.py               # The `crawl4ai` web scraping logic
├── sync_manager.py          # Logic for syncing local cache with the Main Backend
├── realtime/
│   └── alert_sse.py         # Server-Sent Events (SSE) manager for live alerts
├── routes/
│   ├── auth_routes.py       # Handles /api/auth/login (proxies to remote_api)
│   ├── product_routes.py    # Handles /api/products (from local database)
│   ├── scheduler_routes.py  # Handles /api/scheduler/start, /stop, etc.
│   ├── alert_routes.py      # Handles /api/alerts (from local db) & /stream (SSE)
│   └── internal_routes.py   # Internal endpoint for the scheduler to trigger a scrape
└── dist/
    ├── index.html           # (Copied from Frontend) The React app entry point
    └── assets/              # (Copied from Frontend) All static JS, CSS, etc.
```