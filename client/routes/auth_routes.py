# client/routes/auth_routes.py (Corrected)

import logging
from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import JSONResponse

from ..dependencies import auth_manager, api_client, sync_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login", response_class=JSONResponse)
async def login(username: str = Form(...), password: str = Form(...)):
    """
    Handles user login with robust, step-by-step validation.
    """
    try:
        logger.info(f"Login attempt for user: {username}")
        device_fingerprint = auth_manager.get_device_fingerprint()

        token_response = api_client.login_user(username, password, device_fingerprint)
        if not token_response.success or not token_response.data:
            logger.warning(f"Login failed for {username} at token step: {token_response.message}")
            return JSONResponse(
                status_code=token_response.status_code or 401,
                content={"success": False, "message": token_response.message or "Invalid credentials."}
            )

        user_response = api_client.get_current_user()
        if not user_response.success or not user_response.data:
            logger.error(f"Login failed for {username}: Could not fetch user profile after getting token. Reason: {user_response.message}")
            return JSONResponse(
                status_code=user_response.status_code or 401,
                content={"success": False, "message": "Login succeeded but failed to verify session."}
            )
        
        user_data = user_response.data

        auth_manager.save_session(
            access_token=token_response.data['access_token'],
            refresh_token=token_response.data['refresh_token'],
            user_data=user_data
        )
        logger.info(f"Session saved for user: {username}")

        sync_success = await sync_manager.sync_products()
        if not sync_success:
            logger.warning(f"Initial product sync failed for user {username}, but login will proceed.")

        return JSONResponse(content={"success": True, "message": "Login successful"})

    except Exception as e:
        logger.error(f"An unexpected error occurred during login for {username}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "An internal error occurred during login."}
        )

@router.post("/logout", response_class=JSONResponse)
async def logout():
    try:
        api_client.logout_user()
        auth_manager.clear_session()
        logger.info("User logged out and session cleared.")
        return JSONResponse(content={"success": True, "message": "Logged out successfully."})
    except Exception as e:
        logger.error(f"Error during logout: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "An internal error occurred during logout."}
        )

@router.post("/register")
async def register(username: str = Form(...), password: str = Form(...)):
    try:
        response = api_client.register_user(username, password)
        if response.success:
            return JSONResponse(content={"success": True, "message": "Registration successful"})
        else:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": response.message}
            )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Registration failed"}
        )