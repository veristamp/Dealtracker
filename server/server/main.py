# server/main.py
import os
import logging
import structlog
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.staticfiles import StaticFiles
from slowapi.middleware import SlowAPIMiddleware
from starlette.responses import JSONResponse
from server import models
from server.database import engine, SessionLocal
from server.routers import users, products
from server.routers import admin
from server import crud
from datetime import datetime, timezone
from sqlalchemy import text
from dotenv import load_dotenv
from pathlib import Path
from fastapi import FastAPI, Request, status  # <-- Add status here
from sqlalchemy.exc import SQLAlchemyError
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"Environment variables loaded from {env_path}")
else:
    print("No .env file found, using system environment variables")
ENV = os.getenv("ENVIRONMENT", "development")
# Setup logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    processors=[structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer()]
)
logger = structlog.get_logger(__name__)
# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
# Background task for cleanup
async def cleanup_expired_tokens():
    """Background task to cleanup expired refresh tokens periodically."""
    while True:
        db: Optional[Session] = None
        try:
            db = SessionLocal()
            deleted_count = crud.cleanup_expired_refresh_tokens(db)
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired refresh tokens")
        except Exception as e:
            logger.error(f"Error during token cleanup: {e}")
        finally:
            if db:
                db.close()
        
        # Run cleanup every hour
        await asyncio.sleep(3600)
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")
if not SESSION_SECRET_KEY or len(SESSION_SECRET_KEY) < 32:
    logger.critical("SESSION_SECRET_KEY env var not set or is too short. App cannot start.")
    raise RuntimeError("A 32+ character SESSION_SECRET_KEY must be set as an environment variable.")
# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting DealTracker API...")
    
    # Create all tables in the database
    models.Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    
    # Start background cleanup task
    cleanup_task = asyncio.create_task(cleanup_expired_tokens())
    logger.info("Background cleanup task started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down DealTracker API...")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        logger.info("Background cleanup task cancelled")

# Create FastAPI app with lifespan
app = FastAPI(
    title="DealTracker API",
    description="Backend services for the DealTracker Desktop application.",
    version="1.0.0",
    docs_url=None if ENV == "production" else "/docs",
    redoc_url=None if ENV == "production" else "/redoc",
    openapi_url=None if ENV == "production" else "/openapi.json",
    lifespan=lifespan,  # if you use custom lifespan manager
)
@app.middleware("http")
async def add_csp_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
    "default-src 'self'; "
    "style-src  'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com 'unsafe-inline'; "
    "script-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com 'unsafe-inline'; "
    "font-src   'self' https://cdnjs.cloudflare.com data:; "
    "img-src    'self' data:;"
)

    return response
# Add rate limiter to app state
app.state.limiter = limiter
app.mount("/static", StaticFiles(directory="server/static"), name="static")
# --- CORS Configuration ---
origins = [
    "http://localhost:3000",  # React dev server
    "http://localhost:8080",  # Vue dev server
    "http://localhost:5000",  # Client app
    "http://127.0.0.1:5000",  # Client app alternative
    "http://localhost:8592",  # FastAPI dev server
    "http://127.0.0.1:8592",  # FastAPI dev server alternative
]

# Add development origins if in development mode
if os.getenv("ENVIRONMENT", "development") == "development":
    origins.extend([
        "http://localhost",
        "http://127.0.0.1",
        "http://localhost:*",  # Allow any localhost port in dev
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handles database-specific errors."""
    logger.error(f"A database error occurred: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database Error",
            "detail": "An error occurred while communicating with the database."
        }
    )
# --- Add Session Middleware ---
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    max_age=3600,  # Session expires after 1 hour
    same_site="lax",
    https_only=os.getenv("ENVIRONMENT", "development") == "production"
)

# --- Add Rate Limiting Middleware ---
app.add_middleware(SlowAPIMiddleware)

# --- Rate Limit Exception Handler ---
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    response = JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": f"Rate limit exceeded: {exc.detail}",
            "retry_after": getattr(exc, 'retry_after', None)
        }
    )
    response.headers["Retry-After"] = str(getattr(exc, 'retry_after', 60))
    return response

# --- Global Exception Handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred"
        }
    )

# --- Include the API routers ---
app.include_router(users.router)
app.include_router(products.router)
app.include_router(admin.router)

# --- Root endpoint with rate limiting ---
@app.get("/", tags=["Root"])
@limiter.limit("10/minute")  # Allow 10 requests per minute to root
async def read_root(request: Request):
    return {
        "message": "Welcome to the DealTracker API",
        "version": "1.0.0",
        "status": "operational"
    }

# --- Health check endpoint ---
@app.get("/health", tags=["Health"])
@limiter.limit("30/minute")
async def health_check(request: Request):
    try:
        # FIXED: Use text() wrapper for raw SQL
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )

# --- API Info endpoint ---
@app.get("/info", tags=["Info"])
@limiter.limit("5/minute")  # Allow 5 info requests per minute
async def api_info(request: Request):
    return {
        "title": "DealTracker API",
        "description": "Backend services for the DealTracker Desktop application",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "features": [
            "JWT Authentication with Refresh Tokens",
            "Device Fingerprinting",
            "Rate Limiting",
            "Admin Panel",
            "Product Tracking",
            "Price Alerts"
        ]
    }
