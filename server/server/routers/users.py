# server/routers/users.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional

from .. import auth, crud, schemas, models
from ..services import UserService
# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["Users & Authentication"],
)

@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(auth.get_db)):
    """Create a new user account by calling the user service."""
    try:
        user_service = UserService(db)
        new_user = user_service.register_new_user(user)
        return new_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_user endpoint for {user.username}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/token", response_model=schemas.Token)
def login_for_access_token(request: schemas.UserLoginRequest, db: Session = Depends(auth.get_db)):
    """
    Login endpoint. Handles authentication and checks device fingerprint if registered.
    """
    try:
        user = crud.get_user_by_username(db, username=request.username)
        
        # 1. Verify username and password
        if not user or not auth.verify_password(request.password, user.hashed_password):
            logger.warning(f"Failed login attempt for username: {request.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )
        
        # 2. Check if account is active
        if not user.is_active:
            logger.warning(f"Inactive user attempted login: {request.username}")
            raise HTTPException(status_code=403, detail="Account is inactive or pending approval")

        # 3. Check device fingerprint if it's already registered for the user
        if user.device_fingerprint:
            # If a device is registered, the request MUST include a matching fingerprint.
            if request.device_fingerprint is None:
                logger.warning(f"Required device fingerprint was not sent for user: {request.username}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Device fingerprint is required for this account."
                )
            if user.device_fingerprint != request.device_fingerprint:
                logger.warning(f"Device fingerprint mismatch for user: {request.username}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Login from an unrecognized device is not permitted."
                )
        
        # 4. Issue tokens
        access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        refresh_token = auth.create_refresh_token(
            data={"sub": user.username}, db=db
        )
        
        logger.info(f"Successful login for user: {request.username}")
        return {
            "access_token": access_token, 
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login for {request.username}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

# ADD this new endpoint function after the login_for_access_token function:
@router.post("/me/register-device", status_code=status.HTTP_200_OK)
def register_device_fingerprint(
    request: schemas.DeviceRegisterRequest,
    db: Session = Depends(auth.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Registers a device fingerprint for the current user. This is a one-time action.
    """
    # 1. Check if a device is already registered to this user
    if current_user.device_fingerprint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A device has already been registered for this account."
        )

    # 2. Try to save the new fingerprint
    updated_user = crud.update_user_device_fingerprint(db, current_user, request.device_fingerprint)
    
    # crud.update_user_device_fingerprint returns None on conflict
    if not updated_user:
        logger.error(f"Device fingerprint conflict for user: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This device is already registered to another user. Please contact support."
        )

    logger.info(f"Device fingerprint registered for user: {current_user.username}")
    return {"message": "Device registered successfully."}

@router.post("/refresh", response_model=schemas.RefreshResponse)
def refresh_access_token(request: schemas.RefreshTokenRequest, db: Session = Depends(auth.get_db)):
    """Refresh access token using a valid refresh token."""
    try:
        # Verify refresh token and get user ID
        user_id = auth.verify_refresh_token(request.refresh_token, db)
        
        # Get user details
        user = crud.get_user(db, user_id=user_id)
        if not user:
            logger.error(f"User not found for refresh token, user_id: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.is_active:
            logger.warning(f"Inactive user attempted token refresh: {user.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )
        
        # FIXED: Create new access token with username (not user_id)
        access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires  # Use username
        )
        
        logger.info(f"Access token refreshed for user: {user.username}")
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/logout", response_model=schemas.LogoutResponse)
def logout(request: schemas.LogoutRequest, db: Session = Depends(auth.get_db), 
          current_user: models.User = Depends(auth.get_current_active_user)):
    """Logout endpoint that revokes the refresh token."""
    try:
        # Revoke the specific refresh token
        auth.revoke_refresh_token(request.refresh_token, db)
        
        logger.info(f"User logged out successfully: {current_user.username}")
        return {
            "success": True,
            "message": "Logged out successfully"
        }
        
    except Exception as e:
        logger.error(f"Error during logout for user {current_user.username}: {e}")
        return {
            "success": False,
            "message": "Logout completed, but there may have been an issue revoking the token"
        }

@router.post("/logout-all", response_model=schemas.LogoutResponse)
def logout_all_devices(db: Session = Depends(auth.get_db), 
                      current_user: models.User = Depends(auth.get_current_active_user)):
    """Logout from all devices by revoking all refresh tokens for the user."""
    try:
        # Revoke all refresh tokens for this user
        revoked_count = auth.revoke_all_user_refresh_tokens(current_user.id, db)
        
        logger.info(f"User logged out from all devices: {current_user.username} ({revoked_count} tokens revoked)")
        return {
            "success": True,
            "message": f"Logged out from all devices successfully ({revoked_count} sessions ended)"
        }
        
    except Exception as e:
        logger.error(f"Error during logout-all for user {current_user.username}: {e}")
        raise HTTPException(status_code=500, detail="Failed to logout from all devices")

@router.get("/me/", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    """Get current user information."""
    return current_user

@router.get("/me/sessions")
async def get_user_sessions(db: Session = Depends(auth.get_db),
                           current_user: models.User = Depends(auth.get_current_active_user)):
    """Get information about active sessions (refresh tokens) for the current user."""
    try:
        # Get all active refresh tokens for the user
        active_tokens = db.query(models.RefreshToken).filter(
            models.RefreshToken.user_id == current_user.id
        ).all()
        
        sessions = []
        for token in active_tokens:
            sessions.append({
                "id": token.id,
                "created_at": token.created_at,
                "expires_at": token.expires_at
            })
        
        return {
            "active_sessions": len(sessions),
            "sessions": sessions
        }
        
    except Exception as e:
        logger.error(f"Error fetching sessions for user {current_user.username}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch session information")
