import logging
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import platform
import os

from .dependencies import get_current_user, db_manager
from .scheduler import initialize_scheduler, stop_scheduler

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Deal Breaker Myntra",
    description="Client application for Myntra Deal Tracking.",
    version="3.0.0"
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initializes the background scheduler when the application starts."""
    initialize_scheduler()
    logger.info("Application startup complete. Scheduler initialized.")

@app.on_event("shutdown")
def shutdown_event():
    """Stops the background scheduler when the application shuts down."""
    stop_scheduler()
    logger.info("Application shutdown. Scheduler stopped.")

# --- API Routes ---
from .routes import (
    alert_routes, auth_routes, product_routes,
    scheduler_routes, activity_routes, internal_routes
)

app.include_router(auth_routes.router)
app.include_router(product_routes.router)
app.include_router(alert_routes.router)
app.include_router(scheduler_routes.router)
app.include_router(activity_routes.router)
app.include_router(internal_routes.router)

# --- User Info & Health Check ---
@app.get("/api/userinfo")
async def get_user_info(user: dict = Depends(get_current_user)):
    if not user:
        return {"success": False, "message": "Not authenticated"}
    return {
        "success": True,
        "username": user.get("username"),
        "tier": user.get("tier"),
    }

@app.get("/api/dashboard-stats", response_class=JSONResponse)
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    stats = db_manager.get_dashboard_stats()
    return JSONResponse(content={"success": True, "data": stats})

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}

# --- Frontend Serving ---
app.mount("/assets", StaticFiles(directory="client/dist/assets"), name="assets")

@app.get("/{catchall:path}", response_class=FileResponse)
async def serve_react_app(request: Request, catchall: str):
    return FileResponse("client/dist/index.html")