# server/crud.py
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from . import models, schemas 

# Setup logging
logger = logging.getLogger(__name__)

# User CRUD operations
def get_user(db: Session, user_id: int):
    """Fetches a single user by their ID."""
    try:
        return db.query(models.User).filter(models.User.id == user_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching user by ID {user_id}: {e}")
        return None

def get_user_by_username(db: Session, username: str):
    """Fetches a single user by their username."""
    try:
        return db.query(models.User).filter(models.User.username == username).first()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching user by username {username}: {e}")
        return None

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """Fetches a list of all users, with optional pagination."""
    try:
        return db.query(models.User).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching users with skip={skip}, limit={limit}: {e}")
        return []

def create_user(db: Session, user: schemas.UserCreate, hashed_password: str):
    """Creates a new user with a pre-hashed password."""
    try:
        db_user = models.User(
            username=user.username,
            hashed_password=hashed_password,
            is_active=False
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"User created successfully: {user.username}")
        return db_user
    except SQLAlchemyError as e:
        logger.error(f"Error creating user {user.username}: {e}")
        db.rollback()
        return None

def update_user_status(db: Session, user: models.User, is_active: bool):
    """Updates user active status."""
    try:
        user.is_active = is_active
        db.commit()
        db.refresh(user)
        logger.info(f"User status updated for {user.username}: is_active={is_active}")
        return user
    except SQLAlchemyError as e:
        logger.error(f"Error updating user status for {user.username}: {e}")
        db.rollback()
        return None

def update_user_tier(db: Session, user: models.User, tier: str):
    """Updates user tier."""
    try:
        user.tier = tier
        db.commit()
        db.refresh(user)
        logger.info(f"User tier updated for {user.username}: tier={tier}")
        return user
    except SQLAlchemyError as e:
        logger.error(f"Error updating user tier for {user.username}: {e}")
        db.rollback()
        return None

def delete_user(db: Session, user: models.User):
    """Deletes a user and all associated data."""
    try:
        username = user.username
        db.delete(user)
        db.commit()
        logger.info(f"User deleted successfully: {username}")
        return {"message": "User deleted successfully"}
    except SQLAlchemyError as e:
        logger.error(f"Error deleting user {user.username}: {e}")
        db.rollback()
        return {"message": "Error deleting user"}


# Refresh Token CRUD operations
def create_refresh_token(db: Session, refresh_token: schemas.RefreshTokenCreate):
    """Creates a new refresh token in the database."""
    try:
        db_refresh_token = models.RefreshToken(
            token=refresh_token.token,
            user_id=refresh_token.user_id,
            expires_at=refresh_token.expires_at
        )
        db.add(db_refresh_token)
        db.commit()
        db.refresh(db_refresh_token)
        logger.info(f"Refresh token created for user {refresh_token.user_id}")
        return db_refresh_token
    except SQLAlchemyError as e:
        logger.error(f"Error creating refresh token for user {refresh_token.user_id}: {e}")
        db.rollback()
        return None

def get_refresh_token(db: Session, token: str):
    """Fetches a refresh token by token string."""
    try:
        return db.query(models.RefreshToken).filter(
            models.RefreshToken.token == token,
            models.RefreshToken.expires_at > datetime.now(timezone.utc)
        ).first()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching refresh token: {e}")
        return None

def delete_refresh_token(db: Session, token: str):
    """Deletes a specific refresh token (for logout)."""
    try:
        db_token = db.query(models.RefreshToken).filter(models.RefreshToken.token == token).first()
        if db_token:
            db.delete(db_token)
            db.commit()
            logger.info("Refresh token deleted successfully")
            return True
        return False
    except SQLAlchemyError as e:
        logger.error(f"Error deleting refresh token: {e}")
        db.rollback()
        return False

def delete_all_user_refresh_tokens(db: Session, user_id: int):
    """Deletes all refresh tokens for a user (for logout from all devices)."""
    try:
        deleted_count = db.query(models.RefreshToken).filter(
            models.RefreshToken.user_id == user_id
        ).delete()
        db.commit()
        logger.info(f"Deleted {deleted_count} refresh tokens for user {user_id}")
        return deleted_count
    except SQLAlchemyError as e:
        logger.error(f"Error deleting all refresh tokens for user {user_id}: {e}")
        db.rollback()
        return 0

def cleanup_expired_refresh_tokens(db: Session):
    """Cleanup expired refresh tokens (call this periodically)."""
    try:
        deleted_count = db.query(models.RefreshToken).filter(
            models.RefreshToken.expires_at <= datetime.now(timezone.utc)
        ).delete()
        db.commit()
        logger.info(f"Cleaned up {deleted_count} expired refresh tokens")
        return deleted_count
    except SQLAlchemyError as e:
        logger.error(f"Error cleaning up expired refresh tokens: {e}")
        db.rollback()
        return 0

# Product CRUD operations
def create_user_product(db: Session, product: schemas.TrackedProductCreate, user_id: int):
    """Creates a new tracked product for a user."""
    try:
        db_product = models.TrackedProduct(**product.model_dump(), owner_id=user_id)
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        logger.info(f"Product created for user {user_id}: {product.url}")
        return db_product
    except SQLAlchemyError as e:
        logger.error(f"Error creating product for user {user_id}: {e}")
        db.rollback()
        return None

def get_products(db: Session, skip: int = 0, limit: int = 100):
    """Fetches all tracked products with pagination."""
    try:
        return db.query(models.TrackedProduct).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching products: {e}")
        return []

def get_user_products(db: Session, user_id: int):
    """Fetches all tracked products for a specific user."""
    try:
        return db.query(models.TrackedProduct).filter(
            models.TrackedProduct.owner_id == user_id
        ).all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching products for user {user_id}: {e}")
        return []
def update_user_device_fingerprint(db: Session, user: models.User, device_fingerprint: str):
    """Updates user device fingerprint with proper error handling."""
    try:
        # Check if fingerprint already exists for another user
        existing_user = db.query(models.User).filter(
            models.User.device_fingerprint == device_fingerprint,
            models.User.id != user.id
        ).first()
        
        if existing_user:
            logger.warning(f"Device fingerprint already exists for user {existing_user.username}")
            return None
        
        user.device_fingerprint = device_fingerprint
        db.commit()
        db.refresh(user)
        logger.info(f"Device fingerprint updated for user {user.username}")
        return user
        
    except SQLAlchemyError as e:
        logger.error(f"Error updating device fingerprint for {user.username}: {e}")
        db.rollback()
        return None

def delete_product(db: Session, product_id: int, user_id: int = None):
    """Deletes a tracked product by ID, optionally checking ownership."""
    try:
        query = db.query(models.TrackedProduct).filter(models.TrackedProduct.id == product_id)
        
        # Add ownership check if user_id provided
        if user_id:
            query = query.filter(models.TrackedProduct.owner_id == user_id)
        
        db_product = query.first()
        if db_product:
            # Store product data before deletion
            product_data = {
                "id": db_product.id,
                "url": db_product.url,
                "price_threshold": db_product.price_threshold,
                "owner_id": db_product.owner_id
            }
            
            db.delete(db_product)
            db.commit()
            logger.info(f"Product deleted successfully: {product_id}")
            return product_data
        
        logger.warning(f"Product not found for deletion: {product_id}")
        return None
        
    except SQLAlchemyError as e:
        logger.error(f"Error deleting product {product_id}: {e}")
        db.rollback()
        return None
