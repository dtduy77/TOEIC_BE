from datetime import datetime, timedelta
from typing import Any, Optional, Union

from jose import jwt
from passlib.context import CryptContext
from app.core.config import get_settings
from app.core.redis import set_token_cache, get_token_cache, delete_token_cache

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        subject: The subject of the token (usually user ID)
        expires_delta: Optional expiration time delta
        
    Returns:
        JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    
    # Cache the token in Redis
    expiry_seconds = int(expires_delta.total_seconds()) if expires_delta else settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    set_token_cache(str(subject), encoded_jwt, expiry_seconds)
    
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password to compare against
        
    Returns:
        True if the password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password
    
    Args:
        password: The password to hash
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)

def validate_token(token: str, user_id: str) -> bool:
    """
    Validate a token against the Redis cache
    
    Args:
        token: The token to validate
        user_id: The user ID associated with the token
        
    Returns:
        True if the token is valid, False otherwise
    """
    cached_token = get_token_cache(user_id)
    if not cached_token:
        # Token not in cache, validate against JWT
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            return str(payload.get("sub")) == user_id
        except jwt.JWTError:
            return False
    
    # Compare with cached token
    return token == cached_token

def invalidate_token(user_id: str) -> None:
    """
    Invalidate a user's token (e.g., on logout)
    
    Args:
        user_id: The user ID associated with the token
    """
    delete_token_cache(user_id)
