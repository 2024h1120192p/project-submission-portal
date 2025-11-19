"""Authentication utilities for the gateway service.

Handles JWT token creation, validation, and user authentication.
"""
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
from .config import settings


# JWT configuration
ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24


def create_access_token(user_id: str, role: str) -> str:
    """Create a JWT access token.
    
    Args:
        user_id: User ID to encode in token
        role: User role to encode in token
        
    Returns:
        Encoded JWT token string
    """
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS)
    payload = {
        "sub": user_id,
        "role": role,
        "exp": expire
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, str]]:
    """Decode and validate a JWT token.
    
    Args:
        token: JWT token string to decode
        
    Returns:
        Decoded payload dictionary or None if invalid
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        return None


def get_user_from_token(token: Optional[str], default_user_id: str = "user_001", default_role: str = "student") -> tuple[str, str]:
    """Extract user ID and role from JWT token with fallback to defaults.
    
    Args:
        token: JWT token string (optional)
        default_user_id: Default user ID if token is invalid
        default_role: Default role if token is invalid
        
    Returns:
        Tuple of (user_id, role)
    """
    if not token:
        return default_user_id, default_role
    
    payload = decode_token(token)
    if not payload:
        return default_user_id, default_role
    
    user_id = payload.get("sub", default_user_id)
    role = payload.get("role", default_role)
    
    return user_id, role
