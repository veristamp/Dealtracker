# server/schemas.py
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str

# New schema for login request with device fingerprint
class UserLoginRequest(UserBase):
    password: str
    device_fingerprint: Optional[str] = None

class DeviceRegisterRequest(BaseModel):
    device_fingerprint: str = Field(..., min_length=16)   

class UserCreate(UserBase):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)

class User(UserBase):
    id: int
    is_active: bool
    tier: str
    # Updated: Changed from device_id to device_fingerprint
    device_fingerprint: Optional[str]

    class Config:
        from_attributes = True

class TrackedProductBase(BaseModel):
    url: str = Field(..., pattern=r"^https://www\.myntra\.com/.*$")
    price_threshold: float = Field(..., gt=0)
    
class TrackedProductCreate(TrackedProductBase):
    pass

class TrackedProduct(TrackedProductBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

# Enhanced Token schemas for refresh token support
class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# New schemas for refresh token management
class RefreshTokenBase(BaseModel):
    token: str
    user_id: int

class RefreshTokenCreate(RefreshTokenBase):
    expires_at: datetime

class RefreshToken(RefreshTokenBase):
    id: int
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

# Schema for refresh token request
class RefreshTokenRequest(BaseModel):
    refresh_token: str

# Schema for logout request
class LogoutRequest(BaseModel):
    refresh_token: str

# Enhanced response schemas
class LoginResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Token] = None

class RefreshResponse(BaseModel):
    access_token: str
    token_type: str

class LogoutResponse(BaseModel):
    success: bool
    message: str
