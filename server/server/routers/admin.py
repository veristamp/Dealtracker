# server/routers/admin.py
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, case
import os
from urllib.parse import quote_plus
from ..database import get_db
from .. import models, crud
from ..auth import verify_password
# Setup logging
logger = logging.getLogger(__name__)

# Templates setup
templates = Jinja2Templates(directory="server/templates")
templates.env.autoescape = True
# Router setup
router = APIRouter(prefix="/admin", tags=["Admin"])

# Admin configuration from environment
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
# ALLOWED_ADMIN_IPS = os.getenv("ALLOWED_ADMIN_IPS").split(",")

def check_admin_access(request: Request):
    """Check if the request is from an allowed IP and has admin session."""
    # client_ip = request.client.host
    # if client_ip not in ALLOWED_ADMIN_IPS:
    #     raise HTTPException(status_code=403, detail="Access denied from this IP")
    
    if not request.session.get("admin_authenticated"):
        raise HTTPException(status_code=401, detail="Admin authentication required")
    
    return True

# Login routes
@router.get("/", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Admin login page."""
    if request.session.get("admin_authenticated"):
        return RedirectResponse(url="/admin/dashboard", status_code=302)
    return templates.TemplateResponse("admin/login.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
async def admin_login_page_alt(request: Request):
    """Alternative admin login page route."""
    if request.session.get("admin_authenticated"):
        return RedirectResponse(url="/admin/dashboard", status_code=302)
    return templates.TemplateResponse("admin/login.html", {"request": request})

@router.post("/login")
async def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Admin login endpoint."""
    client_ip = request.client.host
    # if client_ip not in ALLOWED_ADMIN_IPS:
    #     return templates.TemplateResponse("admin/login.html", {
    #         "request": request,
    #         "error": "Access denied from this IP address"
    #     })
    
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        request.session["admin_authenticated"] = True
        logger.info(f"Admin login successful from IP: {client_ip}")
        return RedirectResponse(url="/admin/dashboard", status_code=302)
    else:
        logger.warning(f"Failed admin login attempt from IP: {client_ip}")
        return templates.TemplateResponse("admin/login.html", {
            "request": request,
            "error": "Invalid username or password"
        })
@router.get("/logout")
async def admin_logout(request: Request):
    """Admin logout endpoint."""
    request.session.clear()
    return RedirectResponse(url="/admin/", status_code=302)

# Dashboard route
@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    """Admin dashboard page."""
    check_admin_access(request)
    try:
        # A single, efficient query to get user stats
        stats = db.query(
            func.count(models.User.id).label("total_users"),
            func.count(case((models.User.is_active == True, models.User.id))).label("active_users"),
            func.count(case((models.User.is_active == False, models.User.id))).label("pending_users")
        ).one()

        total_products = db.query(func.count(models.TrackedProduct.id)).scalar()

        return templates.TemplateResponse("admin/dashboard.html", {
            "request": request,
            "total_users": stats.total_users,
            "active_users": stats.active_users,
            "total_products": total_products,
            "pending_users": stats.pending_users
        })
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {e}")
        raise HTTPException(status_code=500, detail="Error loading dashboard")


# User management route
@router.get("/users", response_class=HTMLResponse)
async def admin_users_page(request: Request, db: Session = Depends(get_db)):
    """Admin users management page."""
    check_admin_access(request)
    
    try:
        users = crud.get_users(db, limit=100)  # Get all users
        
        # Add product count for each user
        users_with_stats = []
        for user in users:
            product_count = db.query(models.TrackedProduct).filter(
                models.TrackedProduct.owner_id == user.id
            ).count()
            
            users_with_stats.append({
                "id": user.id,
                "username": user.username,
                "is_active": user.is_active,
                "tier": user.tier,
                "device_fingerprint": user.device_fingerprint,
                "product_count": product_count
            })
        
        return templates.TemplateResponse("admin/users.html", {
            "request": request,
            "users": users_with_stats
        })
    except Exception as e:
        logger.error(f"Error loading users page: {e}")
        raise HTTPException(status_code=500, detail="Error loading users")

# Analytics route
@router.get("/analytics", response_class=HTMLResponse)
async def admin_analytics_page(request: Request, db: Session = Depends(get_db)):
    """Admin analytics page."""
    check_admin_access(request)
    try:
        # Efficiently query user and product stats
        user_stats = db.query(
            func.count(models.User.id).label("total_users"),
            func.count(case((models.User.is_active == True, models.User.id))).label("active_users"),
            func.count(case((models.User.tier == "bronze", models.User.id))).label("bronze_users"),
            func.count(case((models.User.tier == "silver", models.User.id))).label("silver_users"),
            func.count(case((models.User.tier == "gold", models.User.id))).label("gold_users")
        ).one()

        total_products = db.query(func.count(models.TrackedProduct.id)).scalar()
        
        return templates.TemplateResponse("admin/analytics.html", {
            "request": request,
            "total_users": user_stats.total_users,
            "active_users": user_stats.active_users,
            "bronze_users": user_stats.bronze_users,
            "silver_users": user_stats.silver_users,
            "gold_users": user_stats.gold_users,
            "total_products": total_products
        })
    except Exception as e:
        logger.error(f"Error loading analytics page: {e}")
        raise HTTPException(status_code=500, detail="Error loading analytics")
# User action routes (for form submissions)
@router.post("/users/{user_id}/activate")
async def activate_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    """Activate a user."""
    check_admin_access(request)
    message = ""
    status = "error"
    try:
        user = crud.get_user(db, user_id=user_id)
        if user:
            crud.update_user_status(db, user, True)
            logger.info(f"Admin activated user: {user.username}")
            message = f"Successfully activated user: {user.username}"
            status = "success"
    except Exception as e:
        logger.error(f"Error activating user {user_id}: {e}")
        message = f"Failed to activate user {user_id}."
    
    return RedirectResponse(url=f"/admin/users?status={status}&message={quote_plus(message)}", status_code=302)

@router.post("/users/{user_id}/deactivate")
async def deactivate_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    """Deactivate a user."""
    check_admin_access(request)
    message = ""
    status = "error"
    try:
        user = crud.get_user(db, user_id=user_id)
        if user:
            crud.update_user_status(db, user, False)
            logger.info(f"Admin deactivated user: {user.username}")
            message = f"Successfully deactivated user: {user.username}"
            status = "success"
    except Exception as e:
        logger.error(f"Error deactivating user {user_id}: {e}")
        message = f"Failed to deactivate user {user_id}."

    return RedirectResponse(url=f"/admin/users?status={status}&message={quote_plus(message)}", status_code=302)

@router.post("/users/{user_id}/delete")
async def delete_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    """Delete a user."""
    check_admin_access(request)
    message = ""
    status = "error"
    try:
        user = crud.get_user(db, user_id=user_id)
        if user:
            username = user.username
            crud.delete_user(db, user)
            logger.info(f"Admin deleted user: {username}")
            message = f"Successfully deleted user: {username}"
            status = "success"
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        message = f"Failed to delete user {user_id}."
    
    return RedirectResponse(url=f"/admin/users?status={status}&message={quote_plus(message)}", status_code=302)

@router.post("/users/{user_id}/reset-device")
async def reset_user_device(user_id: int, request: Request, db: Session = Depends(get_db)):
    """Reset user's device fingerprint (admin only)."""
    check_admin_access(request)
    message = ""
    status = "error"
    try:
        user = crud.get_user(db, user_id=user_id)
        if user:
            user.device_fingerprint = None
            db.commit()
            logger.info(f"Admin reset device fingerprint for user: {user.username}")
            message = f"Device fingerprint reset for user: {user.username}"
            status = "success"
    except Exception as e:
        logger.error(f"Error resetting device fingerprint for user {user_id}: {e}")
        db.rollback()
        message = f"Failed to reset device for user {user_id}."
    
    return RedirectResponse(url=f"/admin/users?status={status}&message={quote_plus(message)}", status_code=302)

@router.post("/users/{user_id}/tier")
async def update_user_tier(user_id: int, tier: str = Form(...), request: Request = None, db: Session = Depends(get_db)):
    """Update user tier."""
    check_admin_access(request)
    message = ""
    status = "error"
    try:
        user = crud.get_user(db, user_id=user_id)
        # Add "admin" to this list of valid tiers
        if user and tier in ["bronze", "silver", "gold", "admin"]:
            crud.update_user_tier(db, user, tier)
            logger.info(f"Admin updated user {user.username} tier to {tier}")
            message = f"Updated {user.username}'s tier to {tier}."
            status = "success"
    except Exception as e:
        logger.error(f"Error updating user tier for {user_id}: {e}")
        message = f"Failed to update tier for user {user_id}."
    
    return RedirectResponse(url=f"/admin/users?status={status}&message={quote_plus(message)}", status_code=302)

