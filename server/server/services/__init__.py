# server/services/__init__.py
import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from .. import auth, crud, schemas, models

logger = logging.getLogger(__name__)

class UserService:
    """A service layer for user-related business logic."""
    def __init__(self, db: Session):
        self.db = db

    def register_new_user(self, user_create: schemas.UserCreate) -> models.User:
        """
        Orchestrates new user registration.
        1. Checks for existing username.
        2. Hashes the password.
        3. Creates the user record.
        """
        logger.info(f"Initiating registration for user: {user_create.username}")
        
        # Check if user already exists
        if crud.get_user_by_username(self.db, username=user_create.username):
            logger.warning(f"Attempted to create user with existing username: {user_create.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Username already registered"
            )
        
        # Hash the password
        hashed_password = auth.get_password_hash(user_create.password)

        # Create the user in the database
        new_user = crud.create_user(
            db=self.db, 
            user=user_create, 
            hashed_password=hashed_password
        )

        if not new_user:
            logger.error(f"Failed to create user object in database for {user_create.username}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Failed to create user"
            )
        
        logger.info(f"New user created successfully: {new_user.username}")
        return new_user