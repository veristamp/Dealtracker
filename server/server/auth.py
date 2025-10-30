# server/auth.py (Final Corrected Version)

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt
from pathlib import Path
from . import models, schemas, crud 
from .database import SessionLocal
import uuid
import bcrypt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
ALGORITHM = os.getenv("ALGORITHM", "EdDSA")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

def load_jwt_keys():
    """Load JWT keys from multiple possible locations for Dokploy compatibility"""
    key_locations = [
        # Dokploy file mounts
        ("/app/keys/private.pem", "/app/keys/public.pem"),
        # Environment variables
        (os.getenv("PRIVATE_KEY_PATH"), os.getenv("PUBLIC_KEY_PATH")),
        # Local development
        ("./private.pem", "./public.pem"),
    ]
    
    for private_path, public_path in key_locations:
        if private_path and public_path:
            private_path = Path(private_path)
            public_path = Path(public_path)
            
            if private_path.exists() and public_path.exists():
                try:
                    with open(private_path, "rb") as f:
                        private_key = f.read()
                    with open(public_path, "rb") as f:
                        public_key = f.read()
                    logger.info(f"JWT keys loaded from: {private_path}")
                    return private_key, public_key
                except Exception as e:
                    logger.warning(f"Failed to load keys from {private_path}: {e}")
                    continue
    
    raise RuntimeError("Could not load JWT keys from any location")

# Load keys
try:
    PRIVATE_KEY, PUBLIC_KEY = load_jwt_keys()
    logger.info("JWT keys loaded successfully")
except Exception as e:
    logger.error(f"Could not load JWT keys: {e}")
    raise RuntimeError(f"Could not load JWT keys: {e}")

# Password Hashing
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")

# Database Dependency 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    """Verify password using bcrypt directly."""
    try:
        # Truncate password to 72 bytes for bcrypt compatibility
        password_bytes = plain_password.encode('utf-8')[:72]
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

def get_password_hash(password):
    """Hash password using bcrypt directly."""
    try:
        # Truncate password to 72 bytes for bcrypt compatibility
        password_bytes = password.encode('utf-8')[:72]
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(f"Password hashing error: {e}")
        raise HTTPException(status_code=500, detail="Password hashing failed")

def authenticate_user(db: Session, username: str, password: str) -> models.User | None:
    try:
        user = crud.get_user_by_username(db, username=username)
        if not user or not verify_password(password, user.hashed_password):
            logger.warning("Auth-failed", extra={"uid": username})
            return None
        logger.info("Auth-ok",      extra={"uid": user.id})
        return user
    except Exception as e:
        logger.error("Auth-error", extra={"uid": username, "error": str(e)})
        return None

# JWT Creation & Verification using PyJWT 
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "jti": str(uuid.uuid4()) # JWT ID claim
    })
    try:
        encoded_jwt = jwt.encode(to_encode, PRIVATE_KEY, algorithm=ALGORITHM)
        logger.info(f"Access token created for user: {data.get('sub')}")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating access token: {e}")
        raise HTTPException(status_code=500, detail="Could not create access token")

def create_refresh_token(data: dict, db: Session):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    try:
        refresh_token = jwt.encode(to_encode, PRIVATE_KEY, algorithm=ALGORITHM)
        username = data.get("sub")
        user = crud.get_user_by_username(db, username=username)
        if not user:
            logger.error(f"User not found when creating refresh token: {username}")
            raise HTTPException(status_code=404, detail="User not found")
        
        refresh_token_create = schemas.RefreshTokenCreate(
            token=refresh_token,
            user_id=user.id,
            expires_at=expire
        )
        
        created_token = crud.create_refresh_token(db, refresh_token_create)
        if not created_token:
            raise HTTPException(status_code=500, detail="Failed to store refresh token")
        
        logger.info(f"Refresh token created for user: {username}")
        return refresh_token
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating refresh token: {e}")
        raise HTTPException(status_code=500, detail="Could not create refresh token")

def decode_token(token: str):
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
        
        # --- THE DEFINITIVE FIX ---
        # Add a manual, explicit check for the 'exp' claim to guarantee validation.
        # This makes the server's logic foolproof against unexpected behavior.
        exp_timestamp = payload.get("exp")
        if not exp_timestamp:
            raise jwt.InvalidTokenError("Token is missing 'exp' claim.")

        current_timestamp = datetime.now(timezone.utc).timestamp()

        if current_timestamp > exp_timestamp:
            logger.warning(f"Manual check failed: Token expired at {datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)}")
            raise jwt.ExpiredSignatureError("Token has expired (manual check).")
        # --- END OF FIX ---
        
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )

def verify_refresh_token(refresh_token: str, db: Session):
    """Verify refresh token and check if it exists in database (not revoked)"""
    try:
        payload = decode_token(refresh_token)
        username = payload.get("sub")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token format"
            )
        
        user = crud.get_user_by_username(db, username=username)
        if not user:
            logger.warning(f"User not found for refresh token: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        stored_token = crud.get_refresh_token(db, token=refresh_token)
        if not stored_token:
            logger.warning(f"Refresh token not found or revoked for user: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token revoked or invalid"
            )
        
        return user.id
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying refresh token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not verify refresh token"
        )


def revoke_refresh_token(refresh_token: str, db: Session):
    """Revoke a refresh token by removing it from database"""
    try:
        crud.delete_refresh_token(db, token=refresh_token)
        logger.info("Refresh token revoked successfully")
    except Exception as e:
        logger.error(f"Error revoking refresh token: {e}")
        raise HTTPException(status_code=500, detail="Could not revoke refresh token")

def revoke_all_user_refresh_tokens(user_id: int, db: Session):
    """Revoke all refresh tokens for a user"""
    try:
        crud.delete_all_user_refresh_tokens(db, user_id=user_id)
        logger.info(f"All refresh tokens revoked for user: {user_id}")
    except Exception as e:
        logger.error(f"Error revoking all refresh tokens for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Could not revoke refresh tokens")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error decoding token: {e}")
        raise credentials_exception

    try:
        user = crud.get_user_by_username(db, username=token_data.username)
        if user is None:
            logger.warning(f"User not found for token: {username}")
            raise credentials_exception
        return user
    except Exception as e:
        logger.error(f"Error getting user from database: {e}")
        raise credentials_exception

def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    if not current_user.is_active:
        logger.warning(f"Inactive user attempted access: {current_user.username}")
        raise HTTPException(status_code=403, detail="Account is inactive or pending approval")
    return current_user