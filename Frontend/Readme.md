Here is the standalone README file for the `Frontend/` application.

-----

# DealTracker Frontend

This is the official web interface for the **DealTracker** application. It is a modern, responsive frontend built with React, Vite, and TypeScript. It is designed to be served by and communicate exclusively with the DealTracker Local Server (the `client/` directory).

## ✨ Core Features

  * **🖥️ Main Dashboard:** A central hub to view live statistics, monitor the scraper's system status, and see real-time price drop alerts.
  * **🗂️ Product Management:** A powerful data table for viewing, adding, deleting, and managing all tracked products. It features bulk actions, filtering, and pagination.
  * **📈 Price Analytics:** Visualize the price history for individual products using interactive line charts, complete with target price overlays.
  * **⚡ Live Alerts:** Receives real-time price drop notifications from the local server via Server-Sent Events (SSE) and instantly displays them as toasts.
  * **📜 Activity Log:** A timeline view of all recent application events, such as adding or removing products.
  * **⚙️ Settings Panel:** A dedicated page to configure application preferences (like notification sounds) and control the backend scheduler (start/stop, change interval).
  * **🔒 Secure Authentication:** A clean login/register interface with all application routes protected by a `ProtectedRoute` component that verifies the user's session with the local server.
  * **📱 Responsive UI:** Built with `shadcn/ui` and Tailwind CSS, providing a polished, professional, and responsive experience on all screen sizes.
  * **🌗 Light/Dark Mode:** Full theme support that respects system preferences and allows for manual toggling.

## 🛠️ Tech Stack

  * **Framework:** React 18, Vite, TypeScript
  * **UI Components:** `shadcn/ui` (built on Radix UI & Tailwind CSS)
  * **Global State:** `Zustand`
  * **Data Fetching:** A custom `fetchAPI` wrapper for error handling and API calls
  * **Data Tables:** `Tanstack React Table`
  * **Charting:** `recharts`
  * **Routing:** `React Router DOM`
  * **Forms:** `React Hook Form` & `Zod`
  * **Notifications:** `Sonner`

## 🚀 Installation & Running (Development)

This frontend is designed to run against the **Local Server** (`client/`).

1.  **Start the Local Server:** Before starting the frontend, ensure the `client/` FastAPI server is running (typically on `http://127.0.0.1:8001`).

2.  **Navigate to the Frontend Directory:**

    ```bash
    cd Frontend
    ```

3.  **Install Dependencies:**

    ```bash
    npm install
    ```

4.  **Run the Development Server:**

    ```bash
    npm run dev
    ```

This will start the Vite development server, usually on `http://localhost:5173`.

### proxy Configuration

The Vite development server is pre-configured in `vite.config.ts` to proxy all API requests:

  * Any request to `/api` (e.g., `/api/auth/login`) will be automatically forwarded to `http://127.0.0.1:8001`.

This allows the React app to make API calls to its own origin (`/api`) while seamlessly communicating with the local server in the background.

### Building for Production

To create a production build (which the `client/` server is designed to serve as static files):

```bash
npm run build
```

This will generate a `dist/` folder containing the optimized static HTML, CSS, and JavaScript assets.