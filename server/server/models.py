from sqlalchemy import Boolean, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from server.database import Base

class User(Base):
    __tablename__ = "dealtracker_users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)
    tier = Column(String, default="bronze")
    # Updated: Changed from device_id to device_fingerprint
    device_fingerprint = Column(String, unique=True, index=True, nullable=True)

    # Preserving cascade for products relationship
    products = relationship("TrackedProduct", back_populates="owner", cascade="all, delete-orphan")
    # New: Relationship with refresh tokens
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

class TrackedProduct(Base):
    __tablename__ = "dealtracker_products"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, index=True, nullable=False)
    price_threshold = Column(Float, nullable=False)
    owner_id = Column(Integer, ForeignKey("dealtracker_users.id"))

    owner = relationship("User", back_populates="products")

class RefreshToken(Base):
    __tablename__ = "dealtracker_refresh_tokens"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("dealtracker_users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationship with user
    user = relationship("User", back_populates="refresh_tokens")
